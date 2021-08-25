from fastapi import APIRouter

router = APIRouter()


@router.post("/create_subscription")
async def create_subscription():
    """Метод оформления подписки"""
    pass


@router.post("/cancel_subscription")
async def cancel_subscription():
    """Метод отказа от подписки"""
    pass


@router.get("/subscriptions")
async def user_subscriptions():
    """Метод просмотра подписок пользователя"""
    pass


@router.get("/orders")
async def user_orders():
    """Метод просмотра заказов пользователя"""
    pass
