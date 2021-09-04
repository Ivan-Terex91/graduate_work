from flask_restx import fields

from api import api
from core.enums import OAuthProvider

OAuthAccountModel = api.model(
    "OAuthAccountModel",
    {
        "provider": fields.String(enum=[p.value for p in OAuthProvider]),
        "exp": fields.DateTime(),
    },
)
