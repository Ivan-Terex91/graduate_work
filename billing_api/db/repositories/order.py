from decimal import Decimal
from typing import Optional

from pydantic import UUID4
from tortoise import timezone

from models.api_models import PaymentDataIn, PaymentMethodDataOut
from models.common_models import OrderStatus
from models.db_models import Order, Subscription


class OrderRepository:
    """Класс для работы с таблицей заказов."""

    @staticmethod
    async def _get_order(**kwargs) -> Optional[Order]:
        """Получить заказ"""
        return (
            await Order.filter(**kwargs)
            .order_by(
                "-created",
            )
            .prefetch_related("subscription", "payment_method")
            .first()
        )

    @staticmethod
    async def _get_orders(**kwargs) -> list[Order]:
        """Получить список заказов"""
        return await Order.filter(**kwargs).prefetch_related(
            "subscription", "payment_method"
        )

    @staticmethod
    async def _update_order(order_id: UUID4, **kwargs) -> None:
        """Обновить заказ"""
        await Order.filter(id=order_id).update(modified=timezone.now(), **kwargs)

    async def get_order_by_external_id(self, external_id: str) -> Optional[Order]:
        """Метод возвращает заказ по внешнему идентификатору заказа"""
        return await self._get_order(external_id=external_id)

    async def get_order(
        self, user_id: UUID4, status: OrderStatus, **kwargs
    ) -> Optional[Order]:
        """Метод возвращает заказ пользователя в обработке"""
        return await self._get_order(
            user_id=user_id, status=status, refund=False, **kwargs
        )

    async def get_recurrent_order(self, order_parend_id: UUID4) -> Optional[Order]:
        """Метод возвращет рекурентный заказ (заказ потомок)"""
        return await self._get_order(parent_id=order_parend_id)

    async def get_processing_orders(self) -> list[Order]:
        """Метод возваращает все заказы находящиеся в обработке"""
        return await self._get_orders(status=OrderStatus.PROGRESS, refund=False)

    async def get_processing_refunds(self) -> list[Order]:
        """Метод возваращает все возвраты находящиеся в обработке"""
        return await self._get_orders(status=OrderStatus.PROGRESS, refund=True)

    async def get_user_orders(self, user_id: UUID4) -> list[Order]:
        """Метод возвращает все заказы пользователя"""
        return await self._get_orders(user_id=user_id)

    async def update_order_external_id(
        self, order_id: UUID4, external_id: str, status: OrderStatus, **kwargs
    ) -> None:
        """Метод обновления внешнего идентификатора заказа"""
        await self._update_order(
            order_id=order_id, external_id=external_id, status=status, **kwargs
        )

    async def update_order_status(self, order_id: UUID4, status: OrderStatus) -> None:
        """Метод обновляет статус заказа"""
        await self._update_order(order_id=order_id, status=status)

    @staticmethod
    async def create_order(
        user_id: UUID4,
        user_email: str,
        subscription: Subscription,
        payment_data: PaymentDataIn,
        payment_method: PaymentMethodDataOut,
    ) -> Order:
        """Метод создания заказа"""
        return await Order.create(
            user_id=user_id,
            user_email=user_email,
            subscription=subscription,
            currency=payment_data.currency,
            discount=payment_data.discount,
            total_cost=payment_data.total_cost,
            payment_method=payment_method,
            refund=False,
            created=timezone.now(),
            modified=timezone.now(),
        )

    @staticmethod
    async def create_refund_order(order: Order, total_cost: Decimal) -> Order:
        """Метод создания возврата заказа"""
        return await Order.create(
            user_id=order.user_id,
            customer_id=order.customer_id,
            user_email=order.user_email,
            subscription=order.subscription,
            currency=order.currency,
            discount=0,
            total_cost=total_cost,
            payment_method=order.payment_method,
            refund=True,
            created=timezone.now(),
            modified=timezone.now(),
        )

    @staticmethod
    async def create_recurrent_order(order: Order):
        """Метод создания рекуррентного заказа"""
        return await Order.create(
            parent_id=order.id,
            user_id=order.user_id,
            customer_id=order.customer_id,
            user_email=order.user_email,
            subscription=order.subscription,
            currency=order.currency,
            discount=0,
            total_cost=order.total_cost,
            payment_method=order.payment_method,
            refund=order.refund,
            created=timezone.now(),
            modified=timezone.now(),
        )
