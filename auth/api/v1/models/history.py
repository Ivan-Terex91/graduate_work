from flask_restx import fields

from api import api
from core.enums import Action, DeviceType

History = api.model(
    "HistoryModel",
    {
        "id": fields.String(readonly=True, as_uuid=True),
        "user_id": fields.String(readonly=True, as_uuid=True),
        "action": fields.String(required=True, enum=[act.value for act in Action]),
        "datetime": fields.DateTime(required=True),
        "user_agent": fields.String(required=True),
        "device_type": fields.String(
            required=True, enum=[dev_type.value for dev_type in DeviceType]
        ),
    },
)
