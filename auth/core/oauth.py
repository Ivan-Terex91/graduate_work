from authlib.integrations.flask_client import OAuth
from authlib.oauth2.auth import OAuth2Token

from core.api import get_current_user
from core.enums import OAuthProvider
from services import services


def fetch_token(provider_name: str):
    provider = OAuthProvider(provider_name)
    user = get_current_user()
    oauth_account = services.oauth_account.get_by_user_id(
        provider=provider, user_id=user.id
    )
    token = OAuth2Token(
        dict(
            access_token=oauth_account.access_token,
            expires_at=oauth_account.exp.timestamp(),
        )
    )
    return token


oauth = OAuth(fetch_token=fetch_token)
