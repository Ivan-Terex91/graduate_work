from dataclasses import dataclass

from flask_restx import fields

from api import api

UserModel = api.model(
    "UserModel",
    {
        "id": fields.String(readonly=True, as_uuid=True),
        "first_name": fields.String(),
        "last_name": fields.String(),
        "birthdate": fields.Date(),
        "country": fields.String(),
        "email": fields.String(),
    },
)

LoginRequestModel = api.model(
    "LoginRequestModel",
    {
        "email": fields.String(required=True),
        "password": fields.String(required=True),
    },
)

ChangePassword = api.model(
    "ChangePassword",
    {
        "old_password": fields.String(required=True),
        "new_password": fields.String(required=True),
    },
)
