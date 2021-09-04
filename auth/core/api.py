from functools import wraps

from flask import g, request
from flask_restx import Resource as RestResource

from core.db import session
from core.exceptions import AuthError, AuthorizationError, BadRequestError
from services import services


def get_current_user():
    token = request.headers.get("TOKEN")
    if not token:
        return None

    user_data = services.token_service.decode_access_token(token)
    return services.user.get(user_data.user_id)


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        token = request.headers.get("TOKEN")
        if not token:
            raise AuthError("Access token required")

        g.access_token = services.token_service.decode_access_token(token)

        return func(*args, **kwargs)

    return decorated_view


def is_authorized(permission_name):
    def func_wrapper(func):
        @wraps(func)
        def decorator_view(*args, **kwargs):
            token = request.headers.get("TOKEN")
            if not token:
                raise AuthError("Access token required")

            access_token = services.token_service.decode_access_token(token)
            user_roles_permissions = (
                services.authorization_service.get_user_roles_permissions(
                    user_id=access_token.user_id
                )
            )

            if permission_name in user_roles_permissions["user_permissions"]:
                return func(*args, **kwargs)

            raise AuthorizationError("Forbidden, you don't have permission to access")

        return decorator_view

    return func_wrapper


def is_superuser(func):
    @wraps(func)
    def decorator_view(*args, **kwargs):
        token = request.headers.get("TOKEN")
        if not token:
            raise AuthError("Access token required")

        access_token = services.token_service.decode_access_token(token)
        user_roles_permissions = (
            services.authorization_service.get_user_roles_permissions(
                user_id=access_token.user_id
            )
        )
        if "superuser" in user_roles_permissions["user_roles"]:
            return func(*args, **kwargs)

        raise AuthorizationError("Forbidden, you don't have permission to access")

    return decorator_view


def captcha_challenge(func):
    @wraps(func)
    def decorator_view(*args, **kwargs):
        hash_key = request.headers.get("CAPTCHA_HASH_KEY")
        if not hash_key:
            raise BadRequestError("Captcha hash key is required")

        services.captcha.verify(hash_key)
        return func(*args, **kwargs)

    return decorator_view


class Resource(RestResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services = self.api.services

    def dispatch_request(self, *args, **kwargs):
        try:
            resp = super().dispatch_request(*args, **kwargs)
            session.commit()
            return resp
        except Exception as exc:
            session.rollback()
            raise exc
        finally:
            session.remove()
