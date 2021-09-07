import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from tortoise.transactions import in_transaction

from core.auth import auth_current_user
from core.helpers import get_amount, get_refund_amount
from core.roles import get_roles_client
from core.stripe import get_stripe
from db.repositories.order import OrderRepository
from db.repositories.payment_method import PaymentMethodRepository
from db.repositories.subscription import SubscriptionRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from models.api_models import PaymentDataIn
from models.common_models import OrderStatus, SubscriptionState

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
            "Error when paying for a subscription, %s has active/not expired or paid subscription",
            auth_user.user_id,
        )
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has subscriptions")

    user_order = await order_repository.get_order(
        user_id=auth_user.user_id, status=OrderStatus.PROGRESS
    )
    if user_order:
        logger.error(
            "Error when paying for a subscription, user %s has order in progress",
            auth_user.user_id,
        )
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="User has order in progress"
        )

    subscription = await SubscriptionRepository.get_subscription(
        subscription_id=payment_data.subscription_id
    )
    if not subscription:
        logger.error(
            "Error when paying for a subscription, subscription with id-%s does not exist",
            payment_data.subscription_id,
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Subscription does not exist"
        )

    stripe_payment_method = await stripe_client.create_payment_method(
        payment_method_data=payment_data.payment_method
    )

    async with in_transaction():
        payment_method = await PaymentMethodRepository.create_payment_method(
            payment_method_data=stripe_payment_method, user_id=auth_user.user_id
        )

        order = await order_repository.create_order(
            user_id=auth_user.user_id,
            user_email=auth_user.user_email,
            subscription=subscription,
            payment_data=payment_data,
            payment_method=payment_method,
        )
        logger.info("Order %s created for user %s", order.id, auth_user.user_id)

        customer = await stripe_client.create_customer(
            user_id=order.user_id,
            user_email=order.user_email,
        )

        await stripe_client.attach_payment_method(
            payment_method_id=payment_method.id, customer_id=customer.id
        )

        payment = await stripe_client.create_payment(
            customer_id=customer.id,
            user_email=customer.email,
            amount=get_amount(order.total_cost),
            currency=order.currency.value,
            payment_method_id=order.payment_method.id,
        )

        logger.info("Payment %s created for user %s", payment.id, auth_user.user_id)

        await order_repository.update_order_external_id(
            order_id=order.id,
            external_id=payment.id,
            status=OrderStatus.PROGRESS,
            customer_id=customer.id,
        )

        logger.info(
            "Order %s update status to progress and has external_id %s",
            order.id,
            payment.id,
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
            "Error when confirm payment a subscription, user % has no processing orders",
            auth_user.user_id,
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
            "Error when refunding a subscription, user %s has no active subscription",
            auth_user.user_id,
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
            "Error when returning a subscription, user %s has no actual paid orders",
            auth_user.user_id,
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
            "Refund order %s created for user %s", refund_order.id, auth_user.user_id
        )
        refund = await stripe_client.create_refund(
            payment_intent_id=user_order.external_id, amount=get_amount(refund_amount)
        )

        await order_repository.update_order_external_id(
            order_id=refund_order.id, external_id=refund.id, status=OrderStatus.PROGRESS
        )
        logger.info(
            "Refund order %s update status to progress and has external_id %s",
            refund_order.id,
            refund.id,
        )

        await user_subscription_repository.update_user_subscription_status_by_id(
            subscription_id=user_subscription.id, status=SubscriptionState.INACTIVE
        )
        logger.info("Subscription %s update status to inactive", user_subscription.id)

        await roles_client.revoke_role(
            user_id=refund_order.user_id,
            role_title=f"subscriber_{refund_order.subscription.type.value}",
        )
        logger.info(
            "Roles subscriber_%s has revoke from user %s",
            refund_order.subscription.type.value,
            refund_order.user_id,
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
            "Error when canceling a subscription, user %s has no active automatic subscription",
            auth_user.user_id,
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="User has no active automatic subscription",
        )

    await user_subscription_repository.update_user_subscription_status_by_id(
        subscription_id=user_subscription.id, status=SubscriptionState.CANCELED
    )
    logger.info("Subscription %s update status to canceled", user_subscription.id)
