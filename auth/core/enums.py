from enum import Enum


class Action(Enum):
    """Действия пользователя."""

    login = "login"
    logout = "logout"


class DeviceType(Enum):
    """Типы устройств пользователя."""

    pc = "pc"
    mobile = "mobile"
    tablet = "tablet"
    undefined = "undefined"


class OAuthProvider(Enum):
    facebook = "facebook"
