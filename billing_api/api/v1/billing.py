import logging
from datetime import date, timedelta

from core.auth import auth_current_user
from core.helpers import get_amount, get_refund_amount
from core.roles import get_roles_client
from core.stripe import get_stripe
from db.repositories.order import OrderRepository
from db.repositories.payment_method import PaymentMethodRepository
from db.repositories.subscription import SubscriptionRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from fastapi import APIRouter, Depends, HTTPException
from models.api_models import (ExpireUserSubscriptionData, PaymentDataIn,
                               UserSubscriptionApiModel)
from models.common_models import OrderStatus, SubscriptionState
from starlette import status
from tortoise.transactions import in_transaction

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/subscription/payment/create")
async def create_subscription_payment(
    payment_data: PaymentDataIn,
    auth_user=Depends(auth_current_user),
    stripe_client=Depends(get_stripe),
    order_repository=Depends(OrderRepository),
    user_subscription_repository=Depends(UserSubscriptionRepository),
) -> None:
    """Метод оформления (оплаты) подписки"""

    user_subscription = await user_subscription_repository.get_user_subscription(
        user_id=auth_user.user_id,
        status=[
            SubscriptionState.ACTIVE,
            SubscriptionState.CANCELED,
        ],
    )
    if user_subscription:
        logger.error(
            f"Error when paying for a subscription, user {auth_user.user_id} has active/not expired or paid subscription"
        )
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has subscriptions")

    user_order = await order_repository.get_order(
        user_id=auth_user.user_id, status=OrderStatus.PROGRESS
    )
    if user_order:
        logger.error(
            f"Error when paying for a subscription, user {auth_user.user_id} has order in progress"
        )
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="User has order in progress"
        )

    subscription = await SubscriptionRepository.get_subscription(
        subscription_id=payment_data.subscription_id
    )
    if not subscription:
        logger.error(
            f"Error when paying for a subscription, subscription with id-{payment_data.subscription_id} does not exist"
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Subscription does not exist"
        )

    stripe_payment_method = await stripe_client.create_payment_method(
        payment_method_data=payment_data.payment_method
    )

    payment_method = await PaymentMethodRepository.create_payment_method(
        payment_method_data=stripe_payment_method, user_id=auth_user.user_id
    )

    async with in_transaction():
        order = await order_repository.create_order(
            user_id=auth_user.user_id,
            user_email=auth_user.user_email,
            subscription=subscription,
            payment_data=payment_data,
            payment_method=payment_method,
        )
        logger.info(f"Order {order.id} created for user {auth_user.user_id}")

        customer = await stripe_client.create_customer(
            user_id=order.user_id,
            user_email=order.user_email,
            payment_method=payment_method.id,
        )

        payment = await stripe_client.create_payment(
            customer_id=customer.id,
            user_email=customer.email,
            amount=get_amount(order.total_cost),
            currency=order.currency.value,
            payment_method_id=order.payment_method.id,
        )

        logger.info(f"Payment {payment.id} created for user {auth_user.user_id}")

        await order_repository.update_order_external_id(
            order_id=order.id,
            external_id=payment.id,
            status=OrderStatus.PROGRESS,
            customer_id=customer.id,
        )
        logger.info(
            f"Order {order.id} update status to progress and has external_id {payment.id}"
        )


@router.post("/subscription/payment/confirm")
async def confirm_subscription_payment(
    payment_id: str,
    auth_user=Depends(auth_current_user),
    stripe_client=Depends(get_stripe),
    order_repository=Depends(OrderRepository),
) -> None:
    """Метод подтверждения платёжа пользователем"""
    user_order = await order_repository.get_order(
        user_id=auth_user.user_id,
        status=OrderStatus.PROGRESS,
    )
    if not user_order:
        logger.error(
            f"Error when confirm payment a subscription, user {auth_user.user_id} has no processing orders"
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User has no processing orders"
        )

    await stripe_client.confirm_payment(
        payment_id=payment_id, payment_method=user_order.payment_method.id
    )


@router.post("/subscription/refund")
async def refund_subscription(
    auth_user=Depends(auth_current_user),
    roles_client=Depends(get_roles_client),
    stripe_client=Depends(get_stripe),
    order_repository=Depends(OrderRepository),
    user_subscription_repository=Depends(UserSubscriptionRepository),
) -> None:
    """Метод возврата денег за подписку"""
    user_subscription = await user_subscription_repository.get_user_subscription(
        user_id=auth_user.user_id,
        status=[SubscriptionState.ACTIVE, SubscriptionState.CANCELED],
    )
    if not user_subscription:
        logger.error(
            f"Error when refunding a subscription, user {auth_user.user_id} has no active subscription"
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User has no active subscription"
        )

    user_order = await order_repository.get_order(
        user_id=auth_user.user_id,
        status=OrderStatus.PAID,
        subscription=user_subscription.subscription,
    )
    if not user_order:
        logger.error(
            f"Error when returning a subscription, user {auth_user.user_id} has no actual paid orders"
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User has no actual paid orders"
        )

    refund_amount = get_refund_amount(
        end_date=user_subscription.end_date,
        amount=user_order.total_cost,
        period=user_order.subscription.period.value,
    )

    async with in_transaction():
        refund_order = await order_repository.create_refund_order(
            order=user_order, total_cost=refund_amount
        )
        logger.info(
            f"Refund order {refund_order.id} created for user {auth_user.user_id}"
        )
        refund = await stripe_client.create_refund(
            payment_intent_id=user_order.external_id, amount=get_amount(refund_amount)
        )

        await order_repository.update_order_external_id(
            order_id=refund_order.id, external_id=refund.id, status=OrderStatus.PROGRESS
        )
        logger.info(
            f"Refund order {refund_order.id} update status to progress and has external_id {refund.id}"
        )

        await user_subscription_repository.update_user_subscription_status_by_id(
            subscription_id=user_subscription.id, status=SubscriptionState.INACTIVE
        )
        logger.info(f"Subscription {user_subscription.id} update status to inactive")

        await roles_client.revoke_role(
            user_id=refund_order.user_id,
            role_title=f"subscriber_{refund_order.subscription.type.value}",
        )
        logger.info(
            f"Roles subscriber_{refund_order.subscription.type.value} has revoke from user {refund_order.user_id}"
        )


@router.post("/subscription/cancel")
async def cancel_subscription(
    auth_user=Depends(auth_current_user),
    user_subscription_repository=Depends(UserSubscriptionRepository),
) -> None:
    """Метод отказа от подписки (отказа от автоматической пролонгации)"""
    user_subscription = await user_subscription_repository.get_user_subscription(
        user_id=auth_user.user_id,
        subscription__automatic=True,
        status=[SubscriptionState.ACTIVE],
    )
    if not user_subscription:
        logger.info(
            f"Error when canceling a subscription, user {auth_user.user_id} has no active automatic subscription"
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="User has no active automatic subscription",
        )

    await user_subscription_repository.update_user_subscription_status_by_id(
        subscription_id=user_subscription.id, status=SubscriptionState.CANCELED
    )
    logger.info(f"Subscription {user_subscription.id} update status to canceled")


@router.post("/subscription/recurring_payment")
async def recurring_payment(
    user_subscription_data: ExpireUserSubscriptionData,
    user_subscription_repository=Depends(UserSubscriptionRepository),
    order_repository=Depends(OrderRepository),
    stripe_client=Depends(get_stripe),
) -> None:
    """Метод по списанию рекурентных платежей"""
    user_order = await order_repository.get_order(
        user_id=user_subscription_data.user_id,
        status=OrderStatus.PAID,
        subscription__id=user_subscription_data.subscription_id,
        parent_id=None,
    )

    child_order = await order_repository.get_recurrent_order(
        order_parend_id=user_order.id
    )
    if not child_order:
        async with in_transaction():
            child_order = await order_repository.create_recurrent_order(
                order=user_order
            )
            payment = await stripe_client.create_recurrent_payment(
                customer_id=child_order.user_id,
                user_email=child_order.user_email,
                amount=get_amount(child_order.total_cost),
                currency=child_order.currency.value,
                payment_method_id=child_order.payment_method.id,
            )
            if payment.status == "succeeded":
                await order_repository.update_order_external_id(
                    order_id=child_order.id,
                    external_id=payment.id,
                    status=OrderStatus.PAID,
                )
                await user_subscription_repository.create_user_subscriptions(
                    order=child_order,
                    status=SubscriptionState.PREACTIVE,
                    start_date=date.today() + timedelta(days=1),
                    end_date=date.today()
                    + timedelta(days=1 + child_order.subscription.period),
                )

                return

            raise Exception(
                f"Error when trying recurrent payment for subscription {child_order.subscription}, user {child_order.id}"
            )
