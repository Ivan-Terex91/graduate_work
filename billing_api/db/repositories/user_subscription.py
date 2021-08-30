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
    async def update_user_subscription_status(subscription_id: UUID4, status: SubscriptionState) -> UsersSubscription:
        """Метод подписки пользователя"""
        return await UsersSubscription.filter(id=subscription_id).update(status=status, modified=timezone.now())
