import logging

from core.stripe import get_stripe
from core.roles import get_roles_client
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from fastapi import APIRouter, Depends
from models.api_models import OrderApiModel, UserSubscriptionApiModel, ExpireUserSubscriptionData
from models.common_models import OrderStatus, SubscriptionState
from tortoise.transactions import in_transaction

from models.db_models import UsersSubscription

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
        ExpireUserSubscriptionData(user_id=user_subscription.user_id, subscription_id=user_subscription.subscription.id)
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
        roles_client=Depends(get_roles_client)
) -> None:
    """Метод проверки оплаты заказа"""
    payment = await stripe_client.get_payment_data(payment_intents_id=order_external_id)
    if payment.status == "succeeded":
        logger.info(f"The order with external_id {order_external_id} is paid")
        order = await order_repository.get_order_by_external_id(external_id=payment.id)
        async with in_transaction():
            await order_repository.update_order_status(
                order_id=order.id, status=OrderStatus.PAID
            )
            logger.info(f"Order {order.id} update status to paid")
            await user_subscription_repository.create_user_subscriptions(order=order, status=SubscriptionState.ACTIVE)
            logger.info(
                f"Subscription {order.subscription.id} for the user {order.user_id} is activated"
            )
            await roles_client.grant_role(user_id=order.user_id,
                                          role_title=f"subscriber_{order.subscription.type.value}")


@router.get("/refunds/processing", response_model=list[OrderApiModel])
async def processing_refunds(
        order_repository=Depends(OrderRepository),
):
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
        roles_client=Depends(get_roles_client)
) -> None:
    """Метод проверяет прошёл ли возврат"""
    refund = await stripe_client.get_refund_data(refund_order_id=refund_external_id)
    if refund.status == "succeeded":
        refund_order = await order_repository.get_order_by_external_id(
            external_id=refund.id
        )
        await order_repository.update_order_status(
            order_id=refund_order.id, status=OrderStatus.PAID
        )
        logger.info(f"Refund {refund_order.id} update status to paid")
        await user_subscription_repository.update_user_subscription_status_by_user_id_and_sub(
            user_id=refund_order.user_id,
            subscription=refund_order.subscription,
            status=SubscriptionState.INACTIVE,
        )
        logger.info(
            f"Subscription {refund_order.subscription.id} for the user {refund_order.user_id} is inactive"
        )
        await roles_client.revoke_role(user_id=refund_order.user_id,
                                       role_title=f"subscriber_{refund_order.subscription.type.value}")


@router.get("/subscriptions/expired/disable")
async def disabling_expired_subscriptions(
        user_subscription_repository=Depends(UserSubscriptionRepository),
        roles_client=Depends(get_roles_client)
) -> None:
    """Метод отключает истёкшие подписки"""
    await user_subscription_repository.update_expired_user_subscription()
    inactive_user_subscriptions = await user_subscription_repository.get_inactive_user_subscriptions()
    for user_subscription in inactive_user_subscriptions:
        await roles_client.revoke_role(user_id=user_subscription.user_id,
                                       role_title=f"subscriber_{user_subscription.subscription.type.value}")


@router.get("/subscriptions/preactive/enable")
async def enable_preactive_subscriptions(
        user_subscription_repository=Depends(UserSubscriptionRepository),
        roles_client=Depends(get_roles_client)
) -> None:
    """Метод включает предактивные подписки"""
    await user_subscription_repository.update_preactive_user_subscription()
    active_user_subscriptions = await user_subscription_repository.get_active_user_subscriptions()
    for user_subscription in active_user_subscriptions:
        await roles_client.grant_role(user_id=user_subscription.user_id,
                                      role_title=f"subscriber_{user_subscription.subscription.type.value}")
