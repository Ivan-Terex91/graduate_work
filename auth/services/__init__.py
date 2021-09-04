from flask import current_app
from werkzeug.local import LocalProxy

from services.auth import OAuthService, TokenService
from services.authorization import AuthorizationService
from services.captcha import CaptchaService
from services.history import UserHistoryService
from services.users import UserService

services = LocalProxy(lambda: current_app.extensions["services"])


class Services:
    def __init__(self, session, redis, secret_key):
        self.session = session
        self.redis = redis
        self.user = UserService(session)
        self.user_history = UserHistoryService(session)
        self.token_service = TokenService(session, redis, secret_key)
        self.authorization_service = AuthorizationService(session)
        self.oauth_account = OAuthService(session)
        self.captcha = CaptchaService(session)
