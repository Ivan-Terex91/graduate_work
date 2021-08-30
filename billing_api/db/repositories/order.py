from decimal import Decimal
from typing import Optional
from tortoise import timezone
from pydantic import UUID4

from models.common_models import OrderStatus
from models.db_models import Order, Subscription

from models.api_models import PaymentDataIn  # TODO может переместить в common, Нее


class OrderRepository:
    """Класс для работы с таблицей заказов."""

    @staticmethod
    async def get_order(user_id: UUID4, status: OrderStatus) -> Optional[Order]:
        """Метод возвращает заказ пользователя в обработке"""
        return await Order.get_or_none(user_id=user_id, status=status,
                                       refund=False).select_related("subscription")

    @staticmethod
    async def create_order(user_id: UUID4, user_email: str, subscription: Subscription, payment_data: PaymentDataIn):
        """Метод создания заказа"""
        return await Order.create(
            user_id=user_id,
            user_email=user_email,
            subscription=subscription,
            currency=payment_data.currency,
            discount=payment_data.discount,
            total_cost=payment_data.total_cost,
            refund=False,
            created=timezone.now(),
            modified=timezone.now(),
        )

    @staticmethod
    async def create_refund_order(order: Order, total_cost: Decimal):
        """Метод создания возврата заказа"""
        return await Order.create(
            user_id=order.user_id,
            user_email=order.user_email,
            subscription=order.subscription,
            currency=order.currency,
            discount=0,
            total_cost=total_cost,
            refund=True,
            created=timezone.now(),
            modified=timezone.now(),
        )

    @staticmethod
    async def update_order_status(order_id: UUID4, external_id: str, status: OrderStatus):
        """Метод обновления статуса заказа"""
        return await Order.filter(id=order_id).update(external_id=external_id, status=status, modified=timezone.now())
