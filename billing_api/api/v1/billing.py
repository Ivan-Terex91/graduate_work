from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_current_user
from core.stripe import get_stripe

from models.db_models import Order, UsersSubscription, Subscription
# from ...models.db_models import Subscription, Order, UsersSubscription,
from pydantic import UUID4
from starlette import status

from .models.api_models import OrderApiModel, UserSubscriptionApiModel, PaymentDataIn, RefundDataIn
from models.enums import SubscriptionState, OrderStatus

from core.logger import logger

from core.helpers import get_refund_amount

router = APIRouter()


@router.post("/create_single_subscription")  # TODO может Order_sub...
async def create_single_subscription(
        payment_data: PaymentDataIn,
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод оформления одноразовой подписки"""  # TODO только одноразовой ли ???!!!
    user_subscription = await UsersSubscription.get_or_none(user_id=auth_user.get("user_id"),
                                                            status__in=[SubscriptionState.PAID,
                                                                        SubscriptionState.ACTIVE])
    if user_subscription:
        logger.debug(f"Error, user {auth_user.get('user_id')} has active or paid subscription")  # TODO проверь логи
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has subscriptions")

    user_order = await Order.get_or_none(user_id=auth_user.get("user_id"), status=OrderStatus.PROGRESS,
                                         refund=False)  # TODO refund=False?
    if user_order:
        logger.debug(f"Error, user {auth_user.get('user_id')} has order in progress")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has order in progress")
    subscription = await Subscription.get_or_none(id=payment_data.subscription_id)

    # TODO далее наверное транзакция должна быть
    order = await Order.create(
        user_id=auth_user.get("user_id"),
        user_email=auth_user.get("user_email"),
        subscription=subscription,
        currency=subscription.currency,
        total_cost=subscription.price
    )
    print(order.__dict__)
    customer = await stripe_client.create_customer(user_id=order.user_id, user_email=order.user_email)
    print(customer)

    payment = await stripe_client.create_payment(customer_id=customer.get("id"), user_email=customer.get("email"),
                                                 amount=int(subscription.price * 100),
                                                 currency=subscription.currency.value)
    print(payment)
    await Order.filter(id=order.id).update(external_id=payment.get("id"), status=OrderStatus.PROGRESS)


@router.post("/confirm_single_subscription")
async def confirm_single_subscription(
        payment_id: str,
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод подтверждения платёжа пользователем"""
    # TODO пока это заглушка и данные о payment_method в stripe_client захардкожены
    confirm_payment = await stripe_client.confirm_payment(payment_id=payment_id)


@router.post("/refund_for_subscription")
async def refund_for_subscription(
        # refund_data: RefundDataIn,  # TODO теоритически подписка активная может быть только одна в нашем сервисе
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод возврата денег за подписку"""
    user_subscription = await UsersSubscription.get_or_none(user_id=auth_user.get("user_id"),
                                                            status=SubscriptionState.ACTIVE).select_related(
        "subscription")  # TODO может уберу select
    if not user_subscription:
        logger.debug(f"Error, user {auth_user.get('user_id')} has no active subscription")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no active subscription")
    print(user_subscription.__dict__)
    user_order = await Order.get_or_none(user_id=auth_user.get("user_id"), status=OrderStatus.PAID,
                                         refund=False).select_related(
        "subscription")
    if not user_order:
        logger.debug(f"Error, user {auth_user.get('user_id')} has no paid orders")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no paid orders")
    print(user_order.__dict__)
    refund_amount = get_refund_amount(end_date=user_subscription.end_date, amount=user_order.total_cost,
                                      period=user_order.subscription.period.value)
    print(refund_amount)
    """Дальше, по моему, должна быть транзакция и следующий алгоритм
    1. Создаём заказ на возврат
    2. Создаём возврат в Stripe
    3. Обновляем статус заказа на progress  # TODO может поменять название статуса на process ???!!!
    4. Остальное шедуллер  
    """
    refund_order = await Order.create(
        user_id=auth_user.get("user_id"),
        user_email=auth_user.get("user_email"),
        subscription=user_order.subscription,
        currency=user_order.currency,
        total_cost=refund_amount,
        refund=True
    )
    print(refund_order.__dict__)
    refund = await stripe_client.create_refund(payment_intent_id=user_order.external_id, amount=int(refund_amount * 100))
    print(refund)
    await Order.filter(id=refund_order.id).update(external_id=refund.get("id"), status=OrderStatus.PROGRESS)


@router.post("/create_automatic_subscription")
async def create_automatic_subscription(auth_user=Depends(auth_current_user), stripe_client=Depends(get_stripe)):
    """Метод оформления подписки с автомотической пролонгацией"""
    pass  # TODO этот метод не нужен тут наверное!!!!


@router.post("/cancel_subscription")
async def cancel_automatic_subscription(auth_user=Depends(auth_current_user), stripe_client=Depends(get_stripe)):
    """Метод отказа от подписки"""
    pass
