from fastapi import APIRouter
from models.db_models import Order, UsersSubscription

from .models.api_models import OrderApiModel, UserSubscriptionApiModel

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
