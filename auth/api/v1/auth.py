from api.v1.models.auth import (LoginResponseModel, RefreshTokenModel,
                                RefreshTokensResponseModel,
                                SignupResponseModel)
from api.v1.models.users import LoginRequestModel
from core.api import Resource, captcha_challenge, login_required
from flask import g, request
from flask_restx import Namespace

authorizations = {
    "api_key": {
        "type": "apiKey",
        "in": "Header",
        "name": "TOKEN",
    }
}
ns = Namespace("Auth Namespace", authorizations=authorizations, security="api_key")


# signup_parser = ns.parser()
# signup_parser.add_argument("CAPTCHA_HASH_KEY", location="headers")


@ns.route("/signup/")
class SignupView(Resource):
    # @captcha_challenge
    # @ns.param("CAPTCHA_HASH_KEY", _in="header")
    @ns.expect(LoginRequestModel, validate=True)
    @ns.response(409, description="This email address is already in use")
    @ns.response(400, description="Bad request")
    @ns.response(201, description="Successfully signup in", model=SignupResponseModel)
    def post(self):
        """Signup new user"""
        user = self.services.user.create(**self.api.payload)
        self.services.authorization_service.add_role_to_user(
            user_id=user.id, role_title="authenticated"
        )

        return {"message": "Successfully signup in"}, 201


@ns.route("/login/")
class LoginView(Resource):
    @ns.expect(LoginRequestModel, validate=True)
    @ns.response(404, description="User not found")
    @ns.response(400, description="Bad request")
    @ns.response(401, description="Unauthorized")
    @ns.response(200, description="Successfully logged in", model=LoginResponseModel)
    def post(self):
        """Login in user"""
        user = self.services.user.get_by_email_password(
            email=self.api.payload.get("email"),
            password=self.api.payload.get("password"),
        )
        if not user:
            return {"message": "User not found"}, 404

        user_id = user.id
        user_agent = request.headers.get("User-Agent")
        user_roles_permissions = (
            self.services.authorization_service.get_user_roles_permissions(
                user_id=user_id
            )
        )

        access_token, refresh_token = self.services.token_service.create_tokens(
            user_id=user_id,
            user_email=user.email,
            user_roles=user_roles_permissions["user_roles"],
            user_permissions=user_roles_permissions["user_permissions"],
            country=user.country,
            birthdate=user.birthdate,
        )
        self.services.user_history.insert_entry(
            user_id=user_id, action="login", user_agent=user_agent
        )
        return {"access_token": access_token, "refresh_token": refresh_token}, 200


@ns.route("/logout/")
@ns.doc(security="api_key")
class LogoutView(Resource):
    @login_required
    @ns.response(401, description="Unauthorized")
    @ns.response(200, "Successfully logout")
    def post(self):
        """Logout user"""
        token = request.headers.get("TOKEN")
        user_data = self.services.token_service.decode_access_token(token)
        user_agent = request.headers.get("User-Agent")
        self.services.user_history.insert_entry(
            user_id=user_data.user_id, action="logout", user_agent=user_agent
        )
        self.services.token_service.remove_tokens(g.access_token)
        return "Successfully logout"


@ns.route("/refresh/")
class RefreshTokensView(Resource):
    @ns.expect(RefreshTokenModel, validate=True)
    @ns.response(404, "Refresh token not found")
    @ns.marshal_with(
        RefreshTokensResponseModel, "Successfully getting new access and refresh tokens"
    )
    def post(self):
        """Getting refresh token"""
        access_token, refresh_token = self.services.token_service.refresh_tokens(
            self.api.payload["refresh_token"]
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
