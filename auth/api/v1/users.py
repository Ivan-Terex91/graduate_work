import datetime

from flask import request
from flask_restx import Namespace

from api.v1.models.history import History
from api.v1.models.users import ChangePassword, UserModel
from core.api import Resource, login_required

authorizations = {
    "api_key": {
        "type": "apiKey",
        "in": "Header",
        "name": "TOKEN",
    }
}
ns = Namespace("Profile Namespace", authorizations=authorizations, security="api_key")


@ns.route("/")
@ns.doc(security="api_key")
@ns.response(401, description="Unauthorized")
@ns.response(404, description="User not found")
class UserProfile(Resource):
    @login_required
    @ns.marshal_with(UserModel, code=200, description="Successful getting profile")
    def get(self):
        """Getting profile user by id"""
        token = request.headers.get("TOKEN")
        user_data = self.services.token_service.decode_access_token(token)
        user = self.services.user.get(user_data.user_id)
        if not user:
            return {"message": "User not found"}, 404
        return user, 200

    @login_required
    @ns.expect(UserModel, validate=True)
    @ns.response(200, description="Successfully updated user profile")
    @ns.response(409, description="This email address is already in use")
    def put(self):
        """Change profile user by id"""
        token = request.headers.get("TOKEN")
        user_data = self.services.token_service.decode_access_token(token)
        updated_user = self.services.user.put(user_data.user_id, **self.api.payload)
        if "birthdate" in self.api.payload:
            if (
                datetime.date.today().year
                - datetime.datetime.strptime(
                    self.api.payload["birthdate"], "%Y-%m-%d"
                ).year
            ) >= 18:
                self.services.authorization_service.add_role_to_user(
                    user_id=user_data.user_id, role_title="adult"
                )

        if not updated_user:
            return {"message": "User not found"}, 404
        return {"message": "Successfully updated user profile"}, 200

    @login_required
    @ns.response(204, description="Successfully deleted user profile")
    def delete(self):
        """Delete profile user"""
        token = request.headers.get("TOKEN")
        user_data = self.services.token_service.decode_access_token(token)
        if self.services.user.delete(user_data.user_id):
            return {"message": "Successfully deleted user profile"}, 204
        return {"message": "User not found"}, 404


@ns.response(404, "User not found")
@ns.doc(security="api_key")
@ns.route("/history/")
class UserHistory(Resource):
    @login_required
    @ns.response(401, description="Unauthorized")
    @ns.marshal_with(
        History, as_list=True, code=200, description="Successful getting history"
    )
    def get(self):
        """Getting the user's login history"""
        token = request.headers.get("TOKEN")
        user_data = self.services.token_service.decode_access_token(token)
        return self.services.user_history.get_history(user_data.user_id)


@ns.response(404, description="User not found")
@ns.doc(security="api_key")
@ns.route("/change_password/")
class ChangePassword(Resource):
    @login_required
    @ns.response(200, description="Successful change password")
    @ns.response(401, description="Unauthorized")
    @ns.response(400, description="Bad request")
    @ns.expect(ChangePassword, validate=True)
    def patch(self):
        """Change user password"""
        token = request.headers.get("TOKEN")
        user_data = self.services.token_service.decode_access_token(token)
        old_password = self.api.payload.get("old_password")
        new_password = self.api.payload.get("new_password")
        self.services.user.change_password(
            user_data.user_id, old_password, new_password
        )
        return {"message": "Successful change password"}, 200
