from uuid import UUID

from sqlalchemy.orm import Session

from core.db import Permission, Role, RolePermission, User, UserRole


class AuthorizationService:
    """Сервис авторизации"""

    def __init__(self, session: Session):
        self.session = session

    def get_user_roles_permissions(self, user_id: UUID):
        """Метод сбора всех ролей и прав пользователя"""
        user_roles = (
            self.session.query(Role.id, Role.title)
            .join(UserRole)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        user_permissions = (
            self.session.query(Permission.title)
            .join(RolePermission)
            .filter(RolePermission.role_id.in_((role[0] for role in user_roles)))
            .all()
        )

        return {
            "user_roles": [role[1] for role in user_roles] or ["anonymous"],
            "user_permissions": [perm[0] for perm in user_permissions],
        }

    def add_role_to_user(self, user_id: UUID, role_title: str):
        """Добавление роли пользователю"""
        role = self.session.query(Role).filter(Role.title == role_title).first()
        user_role = UserRole(user_id=user_id, role_id=role.id)
        self.session.add(user_role)

    def delete_role_from_user(self, user_id: UUID, role_title: str):
        """Удаление роли у пользователя"""
        role = self.session.query(Role).filter(Role.title == role_title).first()
        user_role = UserRole(user_id=user_id, role_id=role.id)
        return (
            self.session.query(UserRole)
            .filter(UserRole.user_id == user_id, UserRole.role_id == user_role.role_id)
            .delete()
        )
