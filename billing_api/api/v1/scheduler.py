import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from tortoise.transactions import in_transaction

from core.helpers import get_amount
from core.roles import get_roles_client
from core.stripe import get_stripe
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from models.api_models import ExpireUserSubscriptionData, OrderApiModel
from models.common_models import OrderStatus, SubscriptionState

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/subscriptions/automatic/active", response_model=list[ExpireUserSubscriptionData]
)
async def expiring_active_subscriptions_automatic(
    user_subscription_repository=Depends(UserSubscriptionRepository),
) -> list[ExpireUserSubscriptionData]:
    """Метод просмотра всех активных подписок пользователей, срок действия которых истекает завтра"""
    user_subscriptions = (
        await user_subscription_repository.get_expiring_active_subscriptions_automatic()
    )
    logger.info("All subscriptions expiring tomorrow have been collected")
    return [
        ExpireUserSubscriptionData(
            user_id=user_subscription.user_id,
            subscription_id=user_subscription.subscription.id,
        )
        for user_subscription in user_subscriptions
    ]


@router.get("/orders/processing", response_model=list[OrderApiModel])
async def processing_orders(
    order_repository=Depends(OrderRepository),
) -> list[OrderApiModel]:
    """Метод просмотра заказов в обработке"""
    orders = await order_repository.get_processing_orders()
    logger.info("All orders are collected in progress")
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]


@router.get("/order/{order_external_id:str}/check")
async def check_order_payment(
    order_external_id: str,
    stripe_client=Depends(get_stripe),
    order_repository=Depends(OrderRepository),
    user_subscription_repository=Depends(UserSubscriptionRepository),
    roles_client=Depends(get_roles_client),
) -> None:
    """Метод проверки оплаты заказа"""
    payment = await stripe_client.get_payment_data(payment_intents_id=order_external_id)
    if payment.status == "succeeded":
        logger.info("The order with external_id %s is paid", order_external_id)
        order = await order_repository.get_order_by_external_id(external_id=payment.id)
        async with in_transaction():
            await order_repository.update_order_status(
                order_id=order.id, status=OrderStatus.PAID
            )
            logger.info("Order %s update status to paid", order.id)
            await user_subscription_repository.create_user_subscriptions(
                order=order, status=SubscriptionState.ACTIVE
            )
            logger.info(
                "Subscription %s for the user %s is activated",
                order.subscription.id,
                order.user_id,
            )
            await roles_client.grant_role(
                user_id=order.user_id,
                role_title=f"subscriber_{order.subscription.type.value}",
            )
            logger.info(
                "Roles subscriber_%s has grant to user %s",
                order.subscription.type.value,
                order.user_id,
            )


@router.get("/refunds/processing", response_model=list[OrderApiModel])
async def processing_refunds(
    order_repository=Depends(OrderRepository),
) -> list[OrderApiModel]:
    """Метод просмотра возвратов в обработке"""
    refunds_orders = await order_repository.get_processing_refunds()
    logger.info("All refunds are collected in progress")
    return [
        OrderApiModel(
            subscription=refund_order.subscription.__dict__, **refund_order.__dict__
        )
        for refund_order in refunds_orders
    ]


@router.get("/refund/{refund_external_id:str}/check")
async def check_refund_order(
    refund_external_id: str,
    stripe_client=Depends(get_stripe),
    order_repository=Depends(OrderRepository),
    user_subscription_repository=Depends(UserSubscriptionRepository),
    roles_client=Depends(get_roles_client),
) -> None:
    """Метод проверяет прошёл ли возврат"""
    refund = await stripe_client.get_refund_data(refund_order_id=refund_external_id)
    if refund.status == "succeeded":
        refund_order = await order_repository.get_order_by_external_id(
            external_id=refund.id
        )
        async with in_transaction():
            await order_repository.update_order_status(
                order_id=refund_order.id, status=OrderStatus.PAID
            )
            logger.info("Refund %s update status to paid", refund_order.id)
            await user_subscription_repository.update_user_subscription_status_by_user_id_and_sub(
                user_id=refund_order.user_id,
                subscription=refund_order.subscription,
                status=SubscriptionState.INACTIVE,
            )
            logger.info(
                "Subscription %s for the user %s is inactive",
                refund_order.subscription.id,
                refund_order.user_id,
            )
            await roles_client.revoke_role(
                user_id=refund_order.user_id,
                role_title=f"subscriber_{refund_order.subscription.type.value}",
            )
            logger.info(
                "Roles subscriber_%s has revoke from user %s",
                refund_order.subscription.type.value,
                refund_order.user_id,
            )


@router.get("/subscriptions/expired/disable")
async def disabling_expired_subscriptions(
    user_subscription_repository=Depends(UserSubscriptionRepository),
    roles_client=Depends(get_roles_client),
) -> None:
    """Метод отключает истёкшие подписки"""
    await user_subscription_repository.update_expired_user_subscription()
    inactive_user_subscriptions = (
        await user_subscription_repository.get_inactive_user_subscriptions()
    )
    for user_subscription in inactive_user_subscriptions:
        await roles_client.revoke_role(
            user_id=user_subscription.user_id,
            role_title=f"subscriber_{user_subscription.subscription.type.value}",
        )

        logger.info(
            "Roles subscriber_%s has revoke from user %s",
            user_subscription.subscription.type.value,
            user_subscription.user_id,
        )


@router.get("/subscriptions/preactive/enable")
async def enable_preactive_subscriptions(
    user_subscription_repository=Depends(UserSubscriptionRepository),
    roles_client=Depends(get_roles_client),
) -> None:
    """Метод включает предактивные подписки"""
    await user_subscription_repository.update_preactive_user_subscription()
    active_user_subscriptions = (
        await user_subscription_repository.get_active_user_subscriptions()
    )
    for user_subscription in active_user_subscriptions:
        await roles_client.grant_role(
            user_id=user_subscription.user_id,
            role_title=f"subscriber_{user_subscription.subscription.type.value}",
        )
        logger.info(
            "Roles subscriber_%s has grant to user %s",
            user_subscription.subscription.type.value,
            user_subscription.user_id,
        )


@router.post("/subscription/recurring_payment")
async def recurring_payment(
    user_subscription_data: ExpireUserSubscriptionData,
    user_subscription_repository=Depends(UserSubscriptionRepository),
    order_repository=Depends(OrderRepository),
    stripe_client=Depends(get_stripe),
) -> None:
    """Метод по списанию рекурентных платежей"""
    user_order = await order_repository.get_order(
        user_id=user_subscription_data.user_id,
        status=OrderStatus.PAID,
        subscription__id=user_subscription_data.subscription_id,
        parent_id=None,
    )

    child_order = await order_repository.get_recurrent_order(
        order_parend_id=user_order.id
    )
    if not child_order:
        async with in_transaction():
            child_order = await order_repository.create_recurrent_order(
                order=user_order
            )
            payment = await stripe_client.create_recurrent_payment(
                customer_id=child_order.user_id,
                user_email=child_order.user_email,
                amount=get_amount(child_order.total_cost),
                currency=child_order.currency.value,
                payment_method_id=child_order.payment_method.id,
            )
            if payment.status == "succeeded":
                await order_repository.update_order_external_id(
                    order_id=child_order.id,
                    external_id=payment.id,
                    status=OrderStatus.PAID,
                )
                await user_subscription_repository.create_user_subscriptions(
                    order=child_order,
                    status=SubscriptionState.PREACTIVE,
                    start_date=date.today() + timedelta(days=1),
                    end_date=date.today()
                    + timedelta(days=1 + child_order.subscription.period),
                )

                return

            raise Exception(
                f"Error when trying recurrent payment for subscription {child_order.subscription},user {child_order.id}"
            )
