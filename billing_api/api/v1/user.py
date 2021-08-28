from fastapi import APIRouter, Depends
from models.db_models import Order, UsersSubscription
from core.auth import auth_current_user
from .models.api_models import OrderApiModel, UserSubscriptionApiModel

router = APIRouter()


@router.get(
    "/subscriptions", response_model=list[UserSubscriptionApiModel]
)
async def user_subscriptions(auth_user=Depends(auth_current_user)):
    """Метод просмотра всех подписок пользователя"""
    subscriptions = await UsersSubscription.filter(user_id=auth_user).select_related(
        "subscription"
    )
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get("/orders", response_model=list[OrderApiModel])
async def user_orders(auth_user=Depends(auth_current_user)):
    """Метод просмотра всех заказов пользователя"""
    orders = await Order.filter(user_id=auth_user).select_related("subscription")
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]
