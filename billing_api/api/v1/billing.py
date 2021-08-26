from core.auth import auth_current_user
from fastapi import APIRouter, Depends

from models.models import UsersSubscription, Order
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


@router.get("/subscriptions")
async def user_subscriptions(auth_user=Depends(auth_current_user)):
    """Метод просмотра подписок пользователя"""
    # subscriptions = await UsersSubscription.get(user_id=auth_user)
    subscriptions = await UsersSubscription.filter(user_id=auth_user)
    print(subscriptions)
    print(type(subscriptions))
    return [sub.__dict__ for sub in subscriptions]


@router.get("/orders")
async def user_orders(auth_user=Depends(auth_current_user)):
    """Метод просмотра заказов пользователя"""
    orders = await Order.filter(user_id=auth_user)
    print(orders)
    print(type(orders))
    return [order.__dict__ for order in orders]
