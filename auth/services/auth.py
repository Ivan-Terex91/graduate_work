import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

import jwt

from core.db import OAuthAccount, RefreshToken
from core.enums import OAuthProvider
from core.exceptions import AuthError, NotFound

ACCESS_TOKEN_INTERVAL = 3600  # 1 hour
REFRESH_TOKEN_INTERVAL = 3600 * 24 * 10  # 10 day


class RefreshTokenNotFound(NotFound):
    pass


class RefreshTokenExpired(AuthError):
    pass


class AccessTokenRevoked(AuthError):
    pass


class OAuthAccountNotFound(NotFound):
    pass


@dataclass
class AccessToken:
    token: str
    user_id: UUID
    user_email: str
    user_roles: list
    user_permissions: list
    country: str
    birthdate: str
    exp: datetime
    iat: datetime


class TokenService:
    def __init__(self, session, redis, secret_key):
        self.session = session
        self.redis = redis
        self.secret_key = secret_key

    def create_tokens(
        self,
        user_id: UUID,
        user_email: str,
        user_roles: list,
        user_permissions: list,
        country: str,
        birthdate: str,
    ) -> Tuple[str, str]:
        """
        Создание новой пары access, refresh токенов
        """

        now = datetime.now(tz=timezone.utc)
        payload = {
            "user_id": str(user_id),
            "user_email": user_email,
            "user_roles": json.dumps(user_roles),
            "user_permissions": json.dumps(user_permissions),
            "country": country,
            "birthdate": birthdate,
            "iat": now,
            "exp": now + timedelta(seconds=ACCESS_TOKEN_INTERVAL),
        }

        access_token = jwt.encode(payload, key=self.secret_key)
        refresh_token = RefreshToken(
            user_id=user_id,
            exp=now + timedelta(seconds=REFRESH_TOKEN_INTERVAL),
            token=secrets.token_urlsafe(),
            access_token=access_token,
        )
        self.session.add(refresh_token)

        return access_token, refresh_token.token

    def decode_access_token(self, token: str, verify_exp=True) -> AccessToken:
        """
        Декодирование jwt access токена

        :raises AccessTokenRevoked: Если токен был отозван (пользователь вышел из аккаунта)
        """

        payload = jwt.decode(
            token,
            key=self.secret_key,
            algorithms=["HS256"],
            options={"require": ["exp", "iat"], "verify_exp": verify_exp},
        )
        if self._is_token_revoked(token):
            raise AccessTokenRevoked("Access token was revoked")

        access_token = AccessToken(
            token=token,
            user_id=payload["user_id"],
            user_email=payload["user_email"],
            user_roles=json.loads(payload["user_roles"]),
            user_permissions=json.loads(payload["user_permissions"]),
            country=payload["country"],
            birthdate=payload["birthdate"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
        )
        return access_token

    def refresh_tokens(self, token: str) -> Tuple[str, str]:
        """
        Обновление access, refresh токенов.
        1. Старый refresh токен удаляется, старый access токен помечается как revoked
        2. Генерируется новая пара access, refresh токенов
        """

        refresh_token = self._get_refresh_token(token)
        access_token = self.decode_access_token(
            refresh_token.access_token, verify_exp=False
        )

        user_id = refresh_token.user_id
        user_email = access_token.user_email
        user_roles = access_token.user_roles
        user_permissions = access_token.user_permissions
        country = access_token.country
        birthdate = access_token.birthdate
        self.session.delete(refresh_token)
        self._revoke_token(access_token)

        return self.create_tokens(
            user_id, user_email, user_roles, user_permissions, country, birthdate
        )

    def remove_tokens(self, access_token: AccessToken):
        """
        Удаление access, refresh токенов.
        1. Удаление refresh токена
        2. Access токен поменяется как revoked
        """
        refresh_token = (
            self.session.query(RefreshToken)
            .filter(RefreshToken.access_token == access_token.token)
            .first()
        )
        self.session.delete(refresh_token)
        self._revoke_token(access_token)

    def _get_refresh_token(self, token: str, validate_exp=True) -> RefreshToken:
        refrest_token = (
            self.session.query(RefreshToken).filter(RefreshToken.token == token).first()
        )
        if not refrest_token:
            raise RefreshTokenNotFound("Refresh token not found")

        if validate_exp and refrest_token.exp.replace(
            tzinfo=timezone.utc
        ) < datetime.now(tz=timezone.utc):
            raise RefreshTokenExpired("Refresh token is expired")

        return refrest_token

    def _is_token_revoked(self, token: str) -> bool:
        return bool(self.redis.exists(token))

    def _revoke_token(self, access_token: AccessToken):
        now = datetime.now(timezone.utc)

        if access_token.exp < now:
            return

        return self.redis.setex(access_token.token, access_token.exp - now, 1)


class OAuthService:
    def __init__(self, session):
        self.session = session

    def create(self, **kwargs) -> OAuthAccount:
        account = OAuthAccount(**kwargs)
        self.session.add(account)
        return account

    def update(self, id: UUID, **kwargs):
        return (
            self.session.query(OAuthAccount)
            .filter(OAuthAccount.id == id)
            .update(kwargs)
        )

    def delete(self, oauth_account: OAuthAccount):
        return self.session.delete(oauth_account)

    def get_by_user_id(
        self, provider: OAuthProvider, user_id: str
    ) -> Optional[OAuthAccount]:
        oauth_account = (
            self.session.query(OAuthAccount)
            .filter(OAuthAccount.provider == provider, OAuthAccount.user_id == user_id)
            .first()
        )
        return oauth_account

    def get_by_account_id(
        self, provider: OAuthProvider, account_id: str
    ) -> Optional[OAuthAccount]:
        oauth_account = (
            self.session.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == provider, OAuthAccount.account_id == account_id
            )
            .first()
        )
        return oauth_account

    def get_all_by_user_id(self, user_id: int) -> List[OAuthAccount]:
        return list(
            self.session.query(OAuthAccount).filter(OAuthAccount.user_id == user_id)
        )
