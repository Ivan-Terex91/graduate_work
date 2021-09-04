from datetime import datetime, timezone

from flask import url_for
from flask_restx import Namespace
from passlib import pwd

from api.v1.models.auth import LoginResponseModel
from api.v1.models.oauth import OAuthAccountModel
from core.api import Resource, get_current_user, login_required
from core.enums import OAuthProvider
from core.oauth import oauth

authorizations = {
    "api_key": {
        "type": "apiKey",
        "in": "Header",
        "name": "TOKEN",
    }
}
ns = Namespace("OAuth Namespace", authorizations=authorizations, security="api_key")


@ns.doc(security="api_key")
@ns.route("/accounts/", endpoint="oauth_accounts")
class OAuthAccountResource(Resource):
    @login_required
    @ns.response(401, description="Unauthorized")
    @ns.marshal_with(
        OAuthAccountModel, as_list=True, code=200, description="List of oauth accounts"
    )
    def get(self):
        """
        Get list of connected oauth accounts
        """
        user = get_current_user()
        return self.services.oauth_account.get_all_by_user_id(user.id)


@ns.route("/facebook/", endpoint="oauth_facebook")
class OAuthFacebookResource(Resource):
    def get(self):
        """
        Start authentication by Facebook provider
        """
        redirect_uri = url_for("oauth_facebook_complete", _external=True)
        response = oauth.facebook.authorize_redirect(redirect_uri)
        return response

    @login_required
    @ns.doc(security="api_key")
    @ns.response(204, description="Successfully deleted user profile")
    def delete(self):
        """
        Remove connected oauth account
        """
        user = get_current_user()
        oauth_account = self.services.oauth_account.get_by_user_id(
            provider=OAuthProvider.facebook, user_id=user.id
        )

        response = oauth.facebook.delete(f"{oauth_account.account_id}/permissions")
        response.raise_for_status()

        self.services.oauth_account.delete(oauth_account)
        return {"message": "Successfully deleted user profile"}, 204


@ns.route("/facebook/complete/", endpoint="oauth_facebook_complete")
class OAuthFacebookCompleteResource(Resource):
    @ns.response(200, description="Successfully logged in", model=LoginResponseModel)
    def get(self):
        """
        Complete authentication for Facebook provider
        """
        token_data = oauth.facebook.authorize_access_token()
        access_token = token_data["access_token"]
        exp = datetime.fromtimestamp(token_data["expires_at"], tz=timezone.utc)

        response = oauth.facebook.get("me", params={"fields": "email"})
        response.raise_for_status()

        account_data = response.json()
        account_id = account_data["id"]
        account_email = account_data["email"]

        oauth_account = self.services.oauth_account.get_by_account_id(
            provider=OAuthProvider.facebook, account_id=account_id
        )

        if oauth_account:
            self.services.oauth_account.update(
                id=oauth_account.id, access_token=access_token, exp=exp
            )
            access_token, refresh_token = self.services.token_service.create_tokens(
                oauth_account.user_id
            )
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        user = self.services.user.create(
            email=account_email,
            password=pwd.genphrase(length=6),
        )
        self.services.authorization_service.add_role_to_user(
            user_id=user.id, role_title="authenticated"
        )

        self.services.oauth_account.create(
            user_id=user.id,
            provider=OAuthProvider.facebook,
            account_id=account_id,
            access_token=access_token,
            exp=exp,
        )

        user_roles_permissions = (
            self.services.authorization_service.get_user_roles_permissions(
                user_id=user.id
            )
        )
        access_token, refresh_token = self.services.token_service.create_tokens(
            user.id,
            user_roles_permissions["user_roles"],
            user_roles_permissions["user_permissions"],
        )
        return {"access_token": access_token, "refresh_token": refresh_token}, 200
