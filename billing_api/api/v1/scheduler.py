from fastapi import APIRouter, Depends

from models.api_models import OrderApiModel, UserSubscriptionApiModel
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from core.stripe import get_stripe

router = APIRouter()


@router.get(
    "/subscriptions/automatic/active",
    response_model=list[UserSubscriptionApiModel]
)
async def active_subscriptions_automatic() -> list[UserSubscriptionApiModel]:
    """Метод просмотра всех активных подписок пользователей"""
    subscriptions = await UserSubscriptionRepository.get_active_subscriptions_automatic()
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get(
    "/orders/processing",
    response_model=list[OrderApiModel]
)
async def processing_orders() -> list[OrderApiModel]:
    """Метод просмотра заказов в обработке"""
    orders = await OrderRepository.get_processing_orders()
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]


@router.get("/order/{order_external_id:str}/check")
async def check_order_payment(
        order_external_id: str,
        stripe_client=Depends(get_stripe)):
    """Метод проверки оплаты заказа"""  # TODO или метод проверки статуса заказа
    payment = await stripe_client.get_payment_data(payment_intents_id=order_external_id)
    if payment.get("status") == "succeeded":
        print("Платёж прошёл")
    elif payment.get("status") == "requires_confirmation":
        print("Ожидается подтверждение")
    else:
        print(payment)
