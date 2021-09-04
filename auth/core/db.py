import uuid

from sqlalchemy import (Column, Date, DateTime, ForeignKey, LargeBinary,
                        PrimaryKeyConstraint, String, UniqueConstraint,
                        create_engine)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, scoped_session, sessionmaker

from core.enums import Action, DeviceType, OAuthProvider
from core.insert_data import (insert_permissions, insert_user_role_permissions,
                              insert_user_roles)

session = scoped_session(sessionmaker(autocommit=False, autoflush=False))

Base = declarative_base()


class User(Base):
    """Таблица пользователей"""

    __tablename__ = "user"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    first_name = Column(String)
    last_name = Column(String)
    birthdate = Column(Date)
    country = Column(String, default="Russia")
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = relationship("UserRole")

    def __repr__(self):
        return f"<User {self.first_name} - {self.last_name}>"


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    token = Column(String, index=True, nullable=False)
    access_token = Column(String, index=True, nullable=False)
    exp = Column(DateTime, nullable=False)


class OAuthAccount(Base):
    __tablename__ = "oauth_account"
    __table_args__ = (UniqueConstraint("account_id", "provider", name="social_pk"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship(User, backref=backref("oauth_accounts", lazy=True))

    account_id = Column(String, nullable=False)
    provider = Column(ENUM(OAuthProvider), nullable=False)

    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    exp = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<OAuthAccount {self.account_id} - {self.provider}>"


def create_partition(target, connection, **kw) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_at_pc" PARTITION OF "history" FOR VALUES IN ('pc')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_at_mobile" PARTITION OF "history" FOR VALUES IN ('mobile')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_at_tablet" PARTITION OF "history" FOR VALUES IN ('tablet')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "history_at_undefined" PARTITION OF "history" FOR VALUES IN ('undefined')"""
    )


class History(Base):
    __tablename__ = "history"

    id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    action = Column(ENUM(Action), nullable=False)
    datetime = Column(DateTime, nullable=False)
    user_agent = Column(String, nullable=False)
    device_type = Column(ENUM(DeviceType), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(id, device_type),
        UniqueConstraint(id, device_type),
        {
            "postgresql_partition_by": "LIST (device_type)",
            "listeners": [("after_create", create_partition)],
        },
    )

    def __repr__(self):
        return f"{self.user_id} - {self.action} - {self.datetime} - {self.device_type}"


class Role(Base):
    """Таблица ролей"""

    __tablename__ = "role"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    title = Column(String, nullable=False)
    permission = relationship("RolePermission")

    __table_args__ = (
        UniqueConstraint(title),
        {
            "listeners": [("after_create", insert_user_roles)],
        },
    )


class Permission(Base):
    """Таблица правил"""

    __tablename__ = "permission"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    title = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(title),
        {
            "listeners": [("after_create", insert_permissions)],
        },
    )


class RolePermission(Base):
    """Таблица правил в ролях"""

    __tablename__ = "role_permission"

    role_id = Column(
        UUID(as_uuid=True), ForeignKey("role.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
    )
    perm = relationship("Permission")

    __table_args__ = {
        "listeners": [("after_create", insert_user_role_permissions)],
    }


class UserRole(Base):
    """Таблица ролей пользователей"""

    __tablename__ = "user_role"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("role.id", ondelete="CASCADE"), primary_key=True
    )
    roles = relationship("Role")


class CaptchaChallenge(Base):
    __tablename__ = "captcha"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    payload = Column(LargeBinary, nullable=False)
    exp = Column(DateTime, nullable=False)
    hash_key = Column(String, nullable=False, index=True)


def init_session(dsn):
    engine = create_engine(dsn)
    session.configure(bind=engine)
    Base.metadata.create_all(engine)
    return session
