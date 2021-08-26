from fastapi import APIRouter, Depends

from core.auth import auth_current_user
from models.db_models import Order, UsersSubscription

from .models.api_models import OrderApiModel, UserSubscriptionApiModel

# from billing_api.models.models import UsersSubscription

router = APIRouter()


@router.post("/create_subscription")
async def create_subscription(auth_user=Depends(auth_current_user)):
    """Метод оформления подписки"""
    pass


@router.post("/cancel_subscription")
async def cancel_subscription(auth_user=Depends(auth_current_user)):
    """Метод отказа от подписки"""
    pass


@router.get("/subscriptions", response_model=list[UserSubscriptionApiModel])
async def user_subscriptions(auth_user=Depends(auth_current_user)):
    """Метод просмотра подписок пользователя"""
    subscriptions = await UsersSubscription.filter(user_id=auth_user).select_related(
        "subscription"
    )
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get("/orders", response_model=list[OrderApiModel])
async def user_orders(auth_user=Depends(auth_current_user)):
    """Метод просмотра заказов пользователя"""
    orders = await Order.filter(user_id=auth_user).prefetch_related(
        "subscription", "payment_method"
    )
    return [
        OrderApiModel(
            subscription=order.subscription.__dict__,
            payment_method=order.payment_method.__dict__,
            **order.__dict__
        )
        for order in orders
    ]
