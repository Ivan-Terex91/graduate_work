from api import api
from flask_restx import fields

CaptchaChallengeModel = api.model(
    "CaptchaChallengeModel",
    {"id": fields.String(as_uuid=True), "exp": fields.DateTime(required=True)},
)
