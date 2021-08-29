from api import api
from flask_restx import fields

CheckTokenModel = api.model("CheckTokenModel", {"token": fields.String(required=True)})

CheckTokenResponseModel = api.model(
    "CheckTokenResponseModel",
    {
        "user_id": fields.String(),
        "user_email": fields.String(),
        "first_name": fields.String(),
        "last_name": fields.String(),
        "birthdate": fields.Date(),
        "country": fields.String(),
        "user_roles": fields.Wildcard(cls_or_instance=fields.Raw),
        "user_permissions": fields.Wildcard(cls_or_instance=fields.Raw),
    },
)
