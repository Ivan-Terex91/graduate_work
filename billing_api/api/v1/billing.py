import logging
from datetime import date, timedelta

from core.auth import auth_current_user
from core.helpers import get_amount, get_refund_amount
from core.stripe import get_stripe
from db.repositories.order import OrderRepository
from db.repositories.subscription import SubscriptionRepository
from db.repositories.user_subscription import UserSubscriptionRepository
from fastapi import APIRouter, Depends, HTTPException
from models.api_models import PaymentDataIn, UserSubscriptionApiModel, ExpireUserSubscriptionData
from models.common_models import OrderStatus, SubscriptionState
from starlette import status
from tortoise.transactions import in_transaction

from db.repositories.payment_method import PaymentMethodRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/subscription/payment/create")
async def create_subscription_payment(
        payment_data: PaymentDataIn,  # TODO может быть OrderDataIn
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe),
        order_repository=Depends(OrderRepository),
        user_subscription_repository=Depends(UserSubscriptionRepository),
):
    """Метод оформления (оплаты) подписки"""
    user_subscription = await user_subscription_repository.get_user_subscription(
        user_id=auth_user.user_id,
        status=[
            # SubscriptionState.PAID,
            SubscriptionState.ACTIVE,
            SubscriptionState.CANCELED,
        ],
    )
    if user_subscription:
        logger.error(
            f"Error when paying for a subscription, user {auth_user.user_id} has active/not expired or paid subscription"
        )
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User has subscriptions")

    # TODO что если тут добавить проверку на отменённую, но не истёкшую подписку пока подписку(сделаю задачу в шедулере он будет истёкшие все переводить в неактивные)

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
        payment_method_data=payment_data.payment_method)  # TODO сходить в страйп и создать метод
    print(stripe_payment_method)

    payment_method = await PaymentMethodRepository.create_payment_method(payment_method_data=stripe_payment_method,
                                                                         user_id=auth_user.user_id)
    print(payment_method)

    async with in_transaction():
        order = await order_repository.create_order(
            user_id=auth_user.user_id,
            user_email=auth_user.user_email,
            subscription=subscription,
            payment_data=payment_data,
            payment_method=payment_method
        )
        print(order)
        logger.info(f"Order {order.id} created for user {auth_user.user_id}")

        customer = await stripe_client.create_customer(
            user_id=order.user_id, user_email=order.user_email, payment_method=payment_method.id
        )

        payment = await stripe_client.create_payment(
            customer_id=customer.id,
            user_email=customer.email,
            amount=get_amount(order.total_cost),
            currency=order.currency.value,
            payment_method_id=order.payment_method.id
        )

        logger.info(f"Payment {payment.id} created for user {auth_user.user_id}")

        await order_repository.update_order_external_id(
            order_id=order.id, external_id=payment.id, status=OrderStatus.PROGRESS, customer_id=customer.id
        )
        logger.info(
            f"Order {order.id} update status to progress and has external_id {payment.id}"
        )
    # TODO тут поидее надо вернуть client.secret для формы ввода в stripe


@router.post("/subscription/payment/confirm")
async def confirm_subscription_payment(
        payment_id: str,
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe),
        order_repository=Depends(OrderRepository),
):
    """Метод подтверждения платёжа пользователем"""
    # TODO пока это заглушка и данные о payment_method в stripe_client захардкожены
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

    await stripe_client.confirm_payment(payment_id=payment_id, payment_method=user_order.payment_method.id)
    # TODO далее работает шедуллер


@router.post("/subscription/refund")
async def refund_subscription(
        # refund_data: RefundDataIn,  # TODO теоритически подписка активная может быть только одна в нашем сервисе ??!!
        auth_user=Depends(auth_current_user),
        stripe_client=Depends(get_stripe),
        order_repository=Depends(OrderRepository),
        user_subscription_repository=Depends(UserSubscriptionRepository),
):
    """Метод возврата денег за подписку"""
    user_subscription = await user_subscription_repository.get_user_subscription(
        user_id=auth_user.user_id,
        status=[SubscriptionState.ACTIVE, SubscriptionState.CANCELED],
    )  # TODO а тут тогда можно добавить автоматическую отменённую, но не истёкшую подписку(сделаю задачу в шедулере он будет истёкшие все переводить в неактивные)
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
        subscription=user_subscription.subscription,  # TODO и подписка
    )
    if not user_order:
        logger.error(
            f"Error when returning a subscription, user {auth_user.user_id} has no actual paid orders"
        )
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="User has no actual paid orders"
        )  # TODO вопросиски...

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
        # TODO затем это должен подхватить шедуллер и платёжка скажет что деньги вернулись или отправились то уведомить


# @router.post("/create_automatic_subscription")
# async def create_automatic_subscription(auth_user=Depends(auth_current_user), stripe_client=Depends(get_stripe)):
#     """Метод оформления подписки с автомотической пролонгацией"""
#     pass  # TODO этот метод не нужен тут наверное!!!!


@router.post("/subscription/cancel")
async def cancel_subscription(
        auth_user=Depends(auth_current_user),
        user_subscription_repository=Depends(UserSubscriptionRepository),
):
    """Метод отказа от подписки (отказа от автоматической пролонгации)"""
    user_subscription = await user_subscription_repository.get_user_subscription(
        user_id=auth_user.user_id,
        subscription__automatic=True,
        status=[SubscriptionState.ACTIVE],
    )  # TODO и этот метод надо доработать - активная автоматическая
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

):
    """Тут будет метод по списанию рекурентных платежей"""  # TODO описание
    print(user_subscription_data)
    # user_subscription = user_subscription_repository.get_user_subscription(id=user_subscription_id)
    user_order = await order_repository.get_order(user_id=user_subscription_data.user_id, status=OrderStatus.PAID,
                                                  subscription__id=user_subscription_data.subscription_id,
                                                  parent_id=None)
    print(user_order)
    child_order = await order_repository.get_recurrent_order(order_parend_id=user_order.id)
    print(child_order)
    if not child_order:
        async with in_transaction():
            child_order = await order_repository.create_recurrent_order(order=user_order)
            print(child_order)
            # customer = await stripe_client.create_customer(user_id=child_order.user_id,
            #                                                user_email=child_order.user_email)
            payment = await stripe_client.create_recurrent_payment(customer_id=child_order.user_id,
                                                                   user_email=child_order.user_email,
                                                                   amount=get_amount(child_order.total_cost),
                                                                   currency=child_order.currency.value,
                                                                   payment_method_id=child_order.payment_method.id)
            if payment.status == "succeeded":
                await order_repository.update_order_external_id(order_id=child_order.id, external_id=payment.id,
                                                                status=OrderStatus.PAID)
                user_subscription = await user_subscription_repository.create_user_subscriptions(
                    order=child_order,
                    status=SubscriptionState.PREACTIVE,
                    start_date=date.today() + timedelta(days=1),
                    end_date=date.today() + timedelta(days=1 + child_order.subscription.period))
                print(user_subscription)
                return

            raise Exception("Не получилось оплатить")

    # TODO дальше новый метод на рекурентный заказ
    # new_order = order_repository.create_order(
    #     user_id=user_order.id,
    #     user_email=user_order.email,
    #     subscription=user_order.subscription,
    #     payment_data: Payment,
    #     payment_method: PaymentMethodDataOut
    # )
    # print(new_order)
    # print(user_subscription)
    # print(user_order)
