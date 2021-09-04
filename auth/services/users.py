from typing import Optional
from uuid import UUID

from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session

from core.db import User
from core.exceptions import AuthError, EmailUsedError, NotFound


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: UUID) -> Optional[User]:
        """Получение пользователя по id"""
        user = self.session.query(User).get({"id": user_id})
        return user

    def create(self, **created_data) -> User:
        """Создание нового пользователя"""

        if self.session.query(User).filter(User.email == created_data["email"]).first():
            raise EmailUsedError("This email address is already in use")

        user = User(**created_data)
        user.password = self.get_hash_password(user.password)
        self.session.add(user)
        self.session.flush()
        return user

    def put(self, user_id: UUID, **updated_data) -> Optional[User]:
        """Редактирование пользователя"""
        user = self.session.query(User).get({"id": user_id})
        if "email" in updated_data:
            if (
                self.session.query(User)
                .filter(User.email == updated_data["email"])
                .first()
            ):
                raise EmailUsedError("This email address is already in use")

        self.session.query(User).filter(User.email == user.email).update(updated_data)
        return True

    def delete(self, user_id: UUID):
        """Удаление пользователя"""
        return self.session.query(User).filter(User.id == user_id).delete()

    def get_by_email_password(self, email: str, password: str) -> Optional[User]:
        """Получение пользователя по email и password"""
        user = self.session.query(User).filter(User.email == email).first()
        if not user:
            raise AuthError("Invalid email")
        if not self.verify_password(password=password, password_hash=user.password):
            raise AuthError("Invalid password")
        return user

    def change_password(self, user_id: UUID, old_password: str, new_password: str):
        """Смена пароля"""
        user = self.session.query(User).get({"id": user_id})
        if not user:
            raise NotFound("User not found")
        if not self.verify_password(password=old_password, password_hash=user.password):
            raise AuthError("Invalid old_password")
        self.session.query(User).filter(User.password == user.password).update(
            {"password": self.get_hash_password(new_password)}
        )

    def get_hash_password(self, password):
        """Получение хэша пароля"""
        return pbkdf2_sha256.hash(password)

    def verify_password(self, password, password_hash):
        """Верификация пароля"""
        return pbkdf2_sha256.verify(password, password_hash)
