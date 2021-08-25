from api import api
from flask_restx import fields

RefreshTokenModel = api.model(
    "RefreshTokenModel",
    {
        "refresh_token": fields.String(required=True),
    },
)

RefreshTokensResponseModel = api.model(
    "RefreshTokensResponseModel",
    {
        "access_token": fields.String(),
        "refresh_token": fields.String(),
    },
)


LoginResponseModel = api.model(
    "LoginResponseModel",
    {
        "access_token": fields.String(),
        "refresh_token": fields.String(),
    },
)

SignupResponseModel = api.model(
    "SignupResponseModel",
    {
        "access_token": fields.String(),
        "refresh_token": fields.String(),
    },
)
