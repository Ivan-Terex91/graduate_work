from typing import Optional

from pydantic import UUID4

from models.common_models import SubscriptionState

from models.db_models import UsersSubscription
from tortoise import timezone


class UserSubscriptionRepository:
    """Класс для работы с таблицей подписок пользователей."""

    @staticmethod
    async def get_user_subscription(user_id: UUID4, status=list[SubscriptionState]) -> Optional[UsersSubscription]:
        """Метод возвращает подписку пользователя"""
        return await UsersSubscription.get_or_none(
            user_id=user_id,
            status__in=status).select_related("subscription")

    @staticmethod
    async def update_user_subscription_status(subscription_id: UUID4, status: SubscriptionState) -> None:
        """Мето обновляет статус подписки пользователя"""
        await UsersSubscription.filter(id=subscription_id).update(status=status, modified=timezone.now())

    @staticmethod
    async def get_active_subscriptions_automatic() -> list[UsersSubscription]:
        """Метод возвращает активные 'автоматические' подписки"""
        return await UsersSubscription.filter(status="active", subscription__automatic=True).select_related(
            "subscription"
        )

    @staticmethod
    async def get_user_subscriptions(user_id: UUID4) -> list[UsersSubscription]:
        """Метод возвращает все подписки, которые есть и были у пользователя"""
        return await UsersSubscription.filter(user_id=user_id).select_related("subscription")
