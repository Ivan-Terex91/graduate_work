import logging

from fastapi import APIRouter, Depends

from core.auth import auth_current_user
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from models.api_models import OrderApiModel, UserSubscriptionApiModel

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/user/subscriptions", response_model=list[UserSubscriptionApiModel])
async def user_subscriptions(
    auth_user=Depends(auth_current_user),
    user_subscription_repository=Depends(UserSubscriptionRepository),
) -> list[UserSubscriptionApiModel]:
    """Метод просмотра всех подписок пользователя"""
    subscriptions = (
        await user_subscription_repository.get_user_subscriptions_by_user_id(
            user_id=auth_user.user_id
        )
    )
    logger.info("All subscriptions of the user %s are collected", auth_user.user_id)

    return [
        UserSubscriptionApiModel(subscription=sub.subscription.__dict__, **sub.__dict__)
        for sub in subscriptions
    ]


@router.get("/user/orders", response_model=list[OrderApiModel])
async def user_orders(
    auth_user=Depends(auth_current_user), order_repository=Depends(OrderRepository)
) -> list[OrderApiModel]:
    """Метод просмотра всех заказов пользователя"""
    orders = await order_repository.get_user_orders(user_id=auth_user.user_id)
    logger.info("All orders of the user %s are collected", auth_user.user_id)
    return [
        OrderApiModel(subscription=order.subscription.__dict__, **order.__dict__)
        for order in orders
    ]
