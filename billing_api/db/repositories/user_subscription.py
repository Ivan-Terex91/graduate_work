from datetime import date, timedelta
from typing import Optional

from models.common_models import SubscriptionState
from models.db_models import Order, Subscription, UsersSubscription
from pydantic import UUID4
from tortoise import timezone


class UserSubscriptionRepository:
    """Класс для работы с таблицей подписок пользователей."""

    @staticmethod
    async def get_user_subscription(
            user_id: UUID4, status=list[SubscriptionState], **kwargs
    ) -> Optional[UsersSubscription]:
        """Метод возвращает подписку пользователя"""
        return await UsersSubscription.get_or_none(
            user_id=user_id, status__in=status, **kwargs
        ).select_related("subscription")

    @staticmethod
    async def _get_user_subscriptions(**kwargs):
        """Получить список подписок"""
        return await UsersSubscription.filter(**kwargs).select_related("subscription")

    @staticmethod
    async def _update_user_subscriptions(status: SubscriptionState, **kwargs) -> None:
        """Обновить подписку пользователя"""
        await UsersSubscription.filter(**kwargs).update(
            status=status, modified=timezone.now()
        )

    async def get_active_user_subscriptions(self):
        """Метод возвращает активные подписки"""
        return await self._get_user_subscriptions(status=SubscriptionState.ACTIVE)

    async def get_inactive_user_subscriptions(self):
        """Метод возвращает активные подписки"""
        return await self._get_user_subscriptions(status=SubscriptionState.INACTIVE)

    async def get_expiring_active_subscriptions_automatic(
            self,
    ) -> list[UsersSubscription]:
        """Метод возвращает активные 'автоматические' подписки, срок действия которых истекает завтра"""
        return await self._get_user_subscriptions(
            status=SubscriptionState.ACTIVE,
            subscription__automatic=True,
            end_date=date.today() + timedelta(days=1),
        )

    async def get_user_subscriptions_by_user_id(
            self, user_id: UUID4
    ) -> list[UsersSubscription]:
        """Метод возвращает все подписки, которые есть и были у пользователя"""
        return await self._get_user_subscriptions(user_id=user_id)

    async def update_user_subscription_status_by_id(
            self, subscription_id: UUID4, status: SubscriptionState
    ) -> None:
        """Метод обновляет статус подписки пользователя"""
        await self._update_user_subscriptions(status=status, id=subscription_id)

    async def update_user_subscription_status_by_user_id_and_sub(
            self, user_id: UUID4, subscription: Subscription, status: SubscriptionState
    ):
        """Метод обновления статуса подписки пользователя"""
        await self._update_user_subscriptions(
            status=status, user_id=user_id, subscription=subscription
        )

    async def update_expired_user_subscription(self):
        """Метод обновляет обновляет статус истёкшим подпискам"""
        await self._update_user_subscriptions(
            status=SubscriptionState.INACTIVE, end_date=date.today()
        )

    @staticmethod
    async def update_preactive_user_subscription():
        """Метод обновляет обновляет статус предактивным подпискам"""
        await UsersSubscription.filter(status=SubscriptionState.PREACTIVE, start_date=date.today()).update(
            status=SubscriptionState.ACTIVE, modified=timezone.now()
        )

    @staticmethod
    async def create_user_subscriptions(order: Order, status: SubscriptionState,
                                        start_date: Optional[date] = None,
                                        end_date: Optional[date] = None) -> UsersSubscription:
        """Метод создания подписки пользователя"""
        return await UsersSubscription.create(
            user_id=order.user_id,
            subscription=order.subscription,
            start_date=date.today() if not start_date else start_date,
            end_date=(date.today() + timedelta(days=order.subscription.period)) if not end_date else end_date,
            status=status,
            created=timezone.now(),
            modified=timezone.now(),
        )
