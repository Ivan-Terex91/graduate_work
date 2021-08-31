from decimal import Decimal
from typing import Optional

from pydantic import UUID4
from tortoise import timezone

from models.api_models import PaymentDataIn
from models.common_models import OrderStatus
from models.db_models import Order, Subscription


class OrderRepository:
    """Класс для работы с таблицей заказов."""

    @staticmethod
    async def get_order(user_id: UUID4, status: OrderStatus) -> Optional[Order]:  # TODO тоже можно объединить
        """Метод возвращает заказ пользователя в обработке"""
        return await Order.get_or_none(
            user_id=user_id, status=status, refund=False
        ).select_related("subscription")

    @staticmethod
    async def create_order(
            user_id: UUID4,
            user_email: str,
            subscription: Subscription,
            payment_data: PaymentDataIn,
    ) -> Order:
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
    async def create_refund_order(order: Order, total_cost: Decimal) -> Order:
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
    async def update_order_status(
            # TODO метод update надо подругому обыграть внизу есть повтор!! И вообще посмотреть на все методы всех репозиториев
            order_id: UUID4, external_id: str, status: OrderStatus
    ) -> None:
        """Метод обновления статуса заказа"""
        await Order.filter(id=order_id).update(
            external_id=external_id, status=status, modified=timezone.now()
        )

    @staticmethod
    async def get_processing_orders() -> list[Order]:
        """Метод возваращает все заказы находящиеся в обработке"""
        return await Order.filter(status="progress").select_related("subscription")

    @staticmethod
    async def get_orders(user_id: UUID4) -> list[Order]:
        """Метод возвращает все заказы пользователя"""
        return await Order.filter(user_id=user_id).select_related("subscription")

    @staticmethod
    async def get_order_by_external_id(external_id: str) -> Order:
        """Метод возвращает заказ по внешнему идентификатору заказа"""
        return await Order.get(external_id=external_id).select_related("subscription")

    @staticmethod
    async def update_only_order_status(order_id: UUID4, status: OrderStatus):
        """Метод обновляет статус заказа"""
        return await Order.filter(order_id=order_id).update(status=status, modified=timezone.now())
