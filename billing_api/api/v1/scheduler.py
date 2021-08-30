from fastapi import APIRouter, Depends

from models.db_models import Order, UsersSubscription

from models.api_models import OrderApiModel, UserSubscriptionApiModel
from core.stripe import get_stripe

router = APIRouter()


@router.get(
    "/active_subscriptions",
    response_model=list[UserSubscriptionApiModel]
)
async def active_subscriptions():
    """Метод просмотра всех активных подписок пользователей"""
    subscriptions = await UsersSubscription.filter(status="active", subscription__automatic=True).select_related(
        "subscription"
    )
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get(
    "/processing_orders",
    response_model=list[OrderApiModel]
)
async def processing_orders():
    """Метод просмотра заказов в обработке"""
    orders = await Order.filter(status="progress").prefetch_related("subscription")
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]


@router.get("/order_info/{order_external_id:str}")
async def check_order_payment(
        order_external_id: str,
        stripe_client=Depends(get_stripe)):
    """Метод проверки оплаты заказа"""  # TODO или метод проверки статуса заказа
    print("В check")
    payment = await stripe_client.get_payment_data(payment_intents_id=order_external_id)
    if payment.get("status") == "succeeded":
        print("Платёж прошёл")
    elif payment.get("status") == "requires_confirmation":
        print("Ожидается подтверждение")
