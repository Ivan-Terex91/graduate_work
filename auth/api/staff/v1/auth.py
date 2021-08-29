from api.staff.v1.models.auth import CheckTokenModel, CheckTokenResponseModel
from core.api import Resource
from flask_restx import Namespace

ns = Namespace("Staff Auth Namespace")


@ns.route("/check_token/")
class CheckToken(Resource):
    @ns.expect(CheckTokenModel, validate=True)
    @ns.marshal_with(CheckTokenResponseModel, code=200)
    def post(self):
        token = self.api.payload["token"]
        access_token = self.services.token_service.decode_access_token(token)
        return {
            "user_id": str(access_token.user_id),
            "user_email": access_token.user_email,
            "user_roles": access_token.user_roles,
            "user_permissions": access_token.user_permissions,
            "country": access_token.country,
            "birthdate": access_token.birthdate,
            "first_name": "first",
            "last_name": "last",
        }
