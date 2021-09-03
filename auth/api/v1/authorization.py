from uuid import UUID

from api.v1.models.authorization import ResponseGetUserRoles, RoleModel
from core.api import Resource, is_superuser, login_required
from flask_restx import Namespace

authorizations = {
    "api_key": {
        "type": "apiKey",
        "in": "Header",
        "name": "TOKEN",
    }
}
ns = Namespace(
    "Authorization Namespace", authorizations=authorizations, security="api_key"
)


@ns.route("/user_role/<user_id>/")
@ns.doc(security="api_key")
@ns.response(401, description="Unauthorized")
@ns.response(403, description="Forbidden, you don't have permission to access")
@ns.response(404, description="User not found")
class GetUserRoles(Resource):
    @login_required
    @is_superuser
    @ns.marshal_with(
        ResponseGetUserRoles, code=200, description="Successfully getting user roles"
    )
    def get(self, user_id: UUID):
        user = self.services.user.get(user_id=user_id)
        if not user:
            return {"message": "User not found"}, 404
        user_roles_permissions = (
            self.services.authorization_service.get_user_roles_permissions(
                user_id=user_id
            )
        )
        return {"roles": ", ".join(user_roles_permissions["user_roles"])}, 200


@ns.route("/user_role/")
@ns.response(401, description="Unauthorized")
@ns.response(403, description="Forbidden, you don't have permission to access")
@ns.response(404, description="User not found")
class ChangeUserRole(Resource):
    @ns.expect(RoleModel, validate=True)
    @ns.response(201, description="Successfully add role to user")
    def post(self):
        user = self.services.user.get(user_id=self.api.payload["user_id"])
        if not user:
            return {"message": "User not found"}, 404

        self.services.authorization_service.add_role_to_user(
            user_id=self.api.payload["user_id"],
            role_title=self.api.payload["role_title"],
        )
        return {"message": "Successfully add role to user"}, 201

    @ns.expect(RoleModel, validate=True)
    @ns.response(204, description="Successfully delete role from user")
    @ns.response(400, description="The user does not have this role")
    def delete(self):
        user = self.services.user.get(user_id=self.api.payload["user_id"])
        if not user:
            return {"message": "User not found"}
        if self.services.authorization_service.delete_role_from_user(
            user_id=self.api.payload["user_id"],
            role_title=self.api.payload["role_title"],
        ):
            return {"message": "Successfully delete role from user"}, 204
        return {"message": "The user does not have this role"}, 400
