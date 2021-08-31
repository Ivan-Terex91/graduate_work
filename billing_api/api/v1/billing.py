import logging

from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_current_user
from core.stripe import get_stripe
from starlette import status

from models.api_models import PaymentDataIn
from models.common_models import SubscriptionState, OrderStatus

from core.helpers import get_refund_amount, get_amount
from db.repositories.order import OrderRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from db.repositories.subscription import SubscriptionRepository
from tortoise.transactions import in_transaction

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/subscription/payment/create")
async def create_subscription_payment(
        payment_data: PaymentDataIn,  # TODO может быть OrderDataIn
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод оформления (оплаты) подписки"""

    user_subscription = await UserSubscriptionRepository.get_user_subscription(user_id=auth_user.user_id,
                                                                               status=[SubscriptionState.PAID,
                                                                                       SubscriptionState.ACTIVE])
    if user_subscription:
        logger.error(
            f"Error when paying for a subscription, user {auth_user.user_id} has active or paid subscription")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has subscriptions")

    user_order = await OrderRepository.get_order(user_id=auth_user.user_id, status=OrderStatus.PROGRESS)
    if user_order:
        logger.error(f"Error when paying for a subscription, user {auth_user.user_id} has order in progress")
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has order in progress")

    subscription = await SubscriptionRepository.get_subscription(subscription_id=payment_data.subscription_id)
    if not subscription:
        logger.error(
            f"Error when paying for a subscription, subscription with id-{payment_data.subscription_id} does not exist"
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subscription does not exist")

    async with in_transaction():
        # TODO надо ли создавать подписку для пользователя ??!! Я думаю что пока нет, надо подумать
        order = await OrderRepository.create_order(user_id=auth_user.user_id,
                                                   user_email=auth_user.user_email,
                                                   subscription=subscription, payment_data=payment_data)
        logger.info(f"Order {order.id} created for user {auth_user.user_id}")

        customer = await stripe_client.create_customer(user_id=order.user_id, user_email=order.user_email)
        payment = await stripe_client.create_payment(customer_id=customer.id, user_email=customer.email,
                                                     amount=get_amount(subscription.price),
                                                     currency=subscription.currency.value)

        logger.info(f"Payment {payment.id} created for user {auth_user.user_id}")

        await OrderRepository.update_order_status(order_id=order.id, external_id=payment.id,
                                                  status=OrderStatus.PROGRESS)
        logger.info(f"Order {order.id} update status to progress and has external_id {payment.id}")
    # TODO тут поидее надо вернуть client.secret для формы ввода в stripe


@router.post("/subscription/payment/confirm")
async def confirm_subscription_payment(
        payment_id: str,
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод подтверждения платёжа пользователем"""
    # TODO пока это заглушка и данные о payment_method в stripe_client захардкожены
    confirm_payment = await stripe_client.confirm_payment(payment_id=payment_id)
    logger.info(f"Payment {payment_id} has confirm")


@router.post("/subscription/refund")
async def refund_subscription(
        # refund_data: RefundDataIn,  # TODO теоритически подписка активная может быть только одна в нашем сервисе ??!!
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe)):
    """Метод возврата денег за подписку"""
    user_subscription = await UserSubscriptionRepository.get_user_subscription(user_id=auth_user.user_id,
                                                                               status=[SubscriptionState.ACTIVE])
    if not user_subscription:
        logger.error(f"Error when returning a subscription, user {auth_user.user_id} has no active subscription")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no active subscription")

    user_order = await OrderRepository.get_order(user_id=auth_user.user_id, status=OrderStatus.PAID)
    if not user_order:
        logger.error(f"Error when returning a subscription, user {auth_user.user_id} has no paid orders")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no paid orders")

    refund_amount = get_refund_amount(end_date=user_subscription.end_date, amount=user_order.total_cost,
                                      period=user_order.subscription.period.value)

    async with in_transaction():
        refund_order = await OrderRepository.create_refund_order(order=user_order, total_cost=refund_amount)
        logger.info(f"Refund order {refund_order.id} created for user {auth_user.user_id}")
        refund = await stripe_client.create_refund(payment_intent_id=user_order.external_id,
                                                   amount=get_amount(refund_amount))

        await OrderRepository.update_order_status(order_id=refund_order.id, external_id=refund.id,
                                                  status=OrderStatus.PROGRESS)
        logger.info(f"Refund order {refund_order.id} update status to progress and has external_id {refund.id}")

        await UserSubscriptionRepository.update_user_subscription_status(subscription_id=user_subscription.id,
                                                                         status=SubscriptionState.INACTIVE)
        logger.info(f"Subscription {user_subscription.id} update status to inactive")
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
    user_subscription = await UserSubscriptionRepository.get_user_subscription(user_id=auth_user.user_id,
                                                                               status=[SubscriptionState.ACTIVE])
    if not user_subscription:
        logger.info(f"Error when canceling a subscription, user {auth_user.user_id} has no active subscription")
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User has no active subscription")

    await UserSubscriptionRepository.update_user_subscription_status(subscription_id=user_subscription.id,
                                                                     status=SubscriptionState.CANCELED)
    logger.info(f"Subscription {user_subscription.id} update status to canceled")
