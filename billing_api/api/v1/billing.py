from core.auth import auth_current_user
from fastapi import APIRouter, Depends

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
    pass


@router.get("/orders")
async def user_orders(auth_user=Depends(auth_current_user)):
    """Метод просмотра заказов пользователя"""
    pass
