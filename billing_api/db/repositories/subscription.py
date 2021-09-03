from typing import Optional

from pydantic import UUID4

from models.db_models import Subscription


class SubscriptionRepository:
    """Класс для работы с таблицей подписок."""

    @staticmethod
    async def get_subscription(subscription_id: UUID4) -> Optional[Subscription]:
        """Метод возвращает подписку"""
        return await Subscription.get_or_none(id=subscription_id)
