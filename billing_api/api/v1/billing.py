from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_current_user
from core.stripe import get_stripe

from models.db_models import Order, UsersSubscription, Subscription
from starlette import status

from models.api_models import PaymentDataIn
from models.common_models import SubscriptionState, OrderStatus

from core.logger import logger
from core.helpers import get_refund_amount, get_amount
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from tortoise.transactions import in_transaction

router = APIRouter()


@router.post("/subscription/payment/create")
async def create_subscription_payment(
        payment_data: PaymentDataIn,  # TODO может быть OrderDataIn
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод оформления (оплаты) подписки"""
    user_subscription = await UserSubscriptionRepository.get_user_subscription(user_id=auth_user.get("user_id"),
                                                                               status=[SubscriptionState.PAID,
                                                                                       SubscriptionState.ACTIVE])
    if user_subscription:
        logger.debug(
            f"Error !!!!!!!, user {auth_user.get('user_id')} has active or paid subscription")  # TODO проверь логи
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has subscriptions")

    user_order = await OrderRepository.get_order(user_id=auth_user.get("user_id"), status=OrderStatus.PROGRESS)
    if user_order:
        logger.debug(f"Error !!!!!!!, user {auth_user.get('user_id')} has order in progress")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has order in progress")
    subscription = await Subscription.get_or_none(
        id=payment_data.subscription_id)  # TODO надо ли создавать репу???!!!!!

    # TODO далее наверное транзакция должна быть и логи логи логи!!!!
    async with in_transaction():
        order = await OrderRepository.create_order(user_id=auth_user.get("user_id"),
                                                   user_email=auth_user.get("user_email"),
                                                   subscription=subscription, payment_data=payment_data)

        customer = await stripe_client.create_customer(user_id=order.user_id, user_email=order.user_email)

        payment = await stripe_client.create_payment(customer_id=customer.get("id"), user_email=customer.get("email"),
                                                     amount=get_amount(subscription.price),
                                                     currency=subscription.currency.value)

        await OrderRepository.update_order_status(order_id=order.id, external_id=payment.get("id"),
                                                  status=OrderStatus.PROGRESS)

    # TODO тут поидее надо вернуть client.secret для формы ввода в stripe


@router.post("/subscription/payment/confirm")
async def confirm_subscription_payment(
        payment_id: str,
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод подтверждения платёжа пользователем"""
    # TODO пока это заглушка и данные о payment_method в stripe_client захардкожены
    confirm_payment = await stripe_client.confirm_payment(payment_id=payment_id)


@router.post("/subscription/refund")
async def refund_subscription(
        # refund_data: RefundDataIn,  # TODO теоритически подписка активная может быть только одна в нашем сервисе
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод возврата денег за подписку"""
    user_subscription = await UserSubscriptionRepository.get_user_subscription(user_id=auth_user.get("user_id"),
                                                                               status=[SubscriptionState.ACTIVE])
    if not user_subscription:
        logger.debug(f"!!!!!!!, user {auth_user.get('user_id')} has no active subscription")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no active subscription")

    user_order = await OrderRepository.get_order(user_id=auth_user.get("user_id"), status=OrderStatus.PAID)
    if not user_order:
        logger.debug(f"!!!!!!!, user {auth_user.get('user_id')} has no paid orders")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no paid orders")

    refund_amount = get_refund_amount(end_date=user_subscription.end_date, amount=user_order.total_cost,
                                      period=user_order.subscription.period.value)

    # TODO далее наверное транзакция должна быть и логи логи логи!!!!
    async with in_transaction():
        refund_order = await OrderRepository.create_refund_order(order=user_order, total_cost=refund_amount)

        refund = await stripe_client.create_refund(payment_intent_id=user_order.external_id,
                                                   amount=get_amount(refund_amount))

        await OrderRepository.update_order_status(order_id=refund_order.id, external_id=refund.get("id"),
                                                  status=OrderStatus.PROGRESS)

        await UserSubscriptionRepository.update_user_subscription_status(subscription_id=user_subscription.id,
                                                                         status=SubscriptionState.INACTIVE)

        # TODO затем это должен подхватить шедуллер и платёжка скажет что деньги вернулись или отправились то уведомить


# @router.post("/create_automatic_subscription")
# async def create_automatic_subscription(auth_user=Depends(auth_current_user), stripe_client=Depends(get_stripe)):
#     """Метод оформления подписки с автомотической пролонгацией"""
#     pass  # TODO этот метод не нужен тут наверное!!!!


@router.post("/subscription/cancel")
async def cancel_subscription(
        auth_user=Depends(auth_current_user),
):
    """Метод отказа от подписки"""
    # TODO логи логи логи
    user_subscription = await UserSubscriptionRepository.get_user_subscription(user_id=auth_user.get("user_id"),
                                                                               status=[SubscriptionState.ACTIVE])
    if not user_subscription:
        logger.debug(f"Error !!!!!!! , user {auth_user.get('user_id')} has no active subscription")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no active subscription")

    await UserSubscriptionRepository.update_user_subscription_status(subscription_id=user_subscription.id,
                                                                     status=SubscriptionState.CANCELED)
