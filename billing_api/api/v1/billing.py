from fastapi import APIRouter, Depends

from core.auth import auth_current_user
from models.db_models import Order, UsersSubscription

from .models.api_models import OrderApiModel, UserSubscriptionApiModel

router = APIRouter()


@router.post("/create_single_subscription")
async def create_single_subscription(auth_user=Depends(auth_current_user)):
    """Метод оформления одноразовой подписки"""
    pass


@router.post("/refund_for_subscription")
async def refund_for_subscription(auth_user=Depends(auth_current_user)):
    """Метод возврата денег за подписку"""
    pass


@router.post("/create_automatic_subscription")
async def create_automatic_subscription(auth_user=Depends(auth_current_user)):
    """Метод оформления подписки с автомотической пролонгацией"""
    pass


@router.post("/cancel_subscription")
async def cancel_automatic_subscription(auth_user=Depends(auth_current_user)):
    """Метод отказа от подписки"""
    pass

