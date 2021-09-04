from datetime import datetime, timezone
from uuid import UUID

import user_agents
from sqlalchemy.orm import Session

from core.db import History, User
from core.enums import Action
from core.exceptions import NotFound


class UserHistoryService:
    def __init__(self, session: Session):
        self.session = session

    def get_history(self, user_id: UUID):
        """Метод получения истории о пользователе"""
        history = (
            self.session.query(History)
            .filter(History.user_id == user_id)
            .order_by(History.datetime)
            .all()
        )
        return history

    def insert_entry(self, user_id: UUID, action: Action, user_agent: str):
        """Метод добавления записи в историю пользователя"""
        user = self.session.query(User).get({"id": user_id})
        if not user:
            raise NotFound("User not found")
        if user_agents.parse(user_agent).is_pc:
            device_type = "pc"
        elif user_agents.parse(user_agent).is_mobile:
            device_type = "mobile"
        elif user_agents.parse(user_agent).is_tablet:
            device_type = "tablet"
        else:
            device_type = "undefined"
        history = History(
            user_id=user_id,
            action=action,
            user_agent=user_agent,
            device_type=device_type,
            datetime=datetime.now(tz=timezone.utc),
        )
        self.session.add(history)
