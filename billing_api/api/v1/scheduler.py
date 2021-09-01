import logging

from core.stripe import get_stripe
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from fastapi import APIRouter, Depends
from models.api_models import OrderApiModel, UserSubscriptionApiModel
from models.common_models import OrderStatus, SubscriptionState
from tortoise.transactions import in_transaction

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/subscriptions/automatic/active", response_model=list[UserSubscriptionApiModel]
)
async def expiring_active_subscriptions_automatic(
    user_subscription_repository=Depends(UserSubscriptionRepository),
) -> list[UserSubscriptionApiModel]:
    """Метод просмотра всех активных подписок пользователей, срок действия которых истекает сегодня"""
    subscriptions = (
        await user_subscription_repository.get_expiring_active_subscriptions_automatic()
    )
    logger.info("All subscriptions expiring today have been collected")
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
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
) -> None:
    """Метод проверки оплаты заказа"""
    # TODO тут ошибка если придёт возватный внешний идентификатор
    payment = await stripe_client.get_payment_data(payment_intents_id=order_external_id)
    logger.info(f"The order with external_id {order_external_id} is paid")
    if payment.status == "succeeded":
        order = await order_repository.get_order_by_external_id(external_id=payment.id)
        async with in_transaction():
            await order_repository.update_order_status(
                order_id=order.id, status=OrderStatus.PAID
            )
            logger.info(f"Order {order.id} update status to paid")
            if order.refund:
                await user_subscription_repository.update_user_subscription_status_by_user_id_and_sub(
                    user_id=order.user_id,
                    subscription=order.subscription,
                    status=SubscriptionState.INACTIVE,
                )
                logger.info(
                    f"Subscription {order.subscription.id} for the user{order.user_id} is inactive"
                )
            else:
                await user_subscription_repository.create_user_subscriptions(
                    order=order
                )
                logger.info(
                    f"Subscription {order.subscription.id} for the user{order.user_id} is activated"
                )


async def recurring_payment():
    """Тут будет метод по списанию рекурентных платежей"""
    # TODO а вот тут подошли к самому главному, мне полюбому нужно хранить payment_method
    pass
