from fastapi import APIRouter, Depends
from core.auth import auth_current_user
from models.api_models import OrderApiModel, UserSubscriptionApiModel
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository

router = APIRouter()


@router.get(
    "/user/subscriptions", response_model=list[UserSubscriptionApiModel]
)
async def user_subscriptions(auth_user=Depends(auth_current_user)) -> list[UserSubscriptionApiModel]:
    """Метод просмотра всех подписок пользователя"""
    subscriptions = await UserSubscriptionRepository.get_user_subscriptions(user_id=auth_user.get("user_id"))
    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get("/user/orders", response_model=list[OrderApiModel])
async def user_orders(auth_user=Depends(auth_current_user)) -> list[OrderApiModel]:
    """Метод просмотра всех заказов пользователя"""
    orders = await OrderRepository.get_orders(user_id=auth_user.get("user_id"))
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]
