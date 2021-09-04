from flask_restx import fields

from api import api

CaptchaChallengeModel = api.model(
    "CaptchaChallengeModel",
    {"id": fields.String(as_uuid=True), "exp": fields.DateTime(required=True)},
)
