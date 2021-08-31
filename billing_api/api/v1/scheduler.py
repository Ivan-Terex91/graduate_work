import logging

from fastapi import APIRouter, Depends

from core.stripe import get_stripe
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from models.api_models import OrderApiModel, UserSubscriptionApiModel
from tortoise.transactions import in_transaction

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/subscriptions/automatic/active", response_model=list[UserSubscriptionApiModel]
)
async def expiring_active_subscriptions_automatic() -> list[UserSubscriptionApiModel]:
    """Метод просмотра всех активных подписок пользователей, срок действия которых истекает сегодня"""
    subscriptions = (
        await UserSubscriptionRepository.get_expiring_active_subscriptions_automatic()
    )
    logger.info("All subscriptions expiring today have been collected")
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get("/orders/processing", response_model=list[OrderApiModel])
async def processing_orders() -> list[OrderApiModel]:
    """Метод просмотра заказов в обработке"""
    orders = await OrderRepository.get_processing_orders()
    logger.info("All orders are collected in progress")
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]


@router.get("/order/{order_external_id:str}/check")
async def check_order_payment(
        order_external_id: str, stripe_client=Depends(get_stripe)
):
    """Метод проверки оплаты заказа"""  # TODO или метод проверки статуса заказа
    payment = await stripe_client.get_payment_data(payment_intents_id=order_external_id)
    # TODO тут подумаю какие логи нужны
    # payment_mod = PaymentInner()
    print(payment.status)
    if payment.status == "succeeded":
        logger.info(f"The order {order_external_id} is paid")
        order = await OrderRepository.get_order_by_external_id(external_id=payment.id)
        print(order)
        # TODO дальше должна быть транзакция
        async with in_transaction():
            await OrderRepository.update_only_order_status(order_id=order.id)
            logger.info(f"Order {order.id} update status to paid")
            # await UserSubscriptionRepository  # TODO создаём подписку пользователю
    elif payment.status == "error":  # TODO посмотри в доке
        pass  # TODO подумай над алгоритмом

    # return payment
    # if payment.get("status") == "succeeded":
    #     return {"details": "Платёж прошёл"}
    # elif payment.get("status") == "requires_confirmation":
    #     return {"details": "Ожидается оплата"}
    # else:
    #     print(payment)
    #     # return {"details": "Нет такого платежа"}
    #     return payment
