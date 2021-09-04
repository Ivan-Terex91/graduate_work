from io import BytesIO

from flask.helpers import send_file
from flask_restx import Namespace

from api.v1.models.captcha import CaptchaChallengeModel
from core.api import Resource

ns = Namespace("Captcha Namespace")


@ns.route("/")
class CaptchaGenerateView(Resource):
    @ns.marshal_with(
        CaptchaChallengeModel, code=200, description="New captcha challenge"
    )
    def post(self):
        """
        Generate new captcha challenge
        """
        return self.services.captcha.create()


@ns.route("/<uuid:id>/")
class CaptchaPayloadView(Resource):
    @ns.response(200, description="Captcha challenge payload")
    @ns.produces(["application/png"])
    def get(self, id):
        """
        Get captcha challenge payload
        """
        captcha_challenge = self.services.captcha.get(id)
        b = BytesIO()
        b.write(captcha_challenge.payload)
        b.seek(0)

        return send_file(
            b,
            attachment_filename="challenge.png",
            cache_timeout=0,
        )


@ns.route("/<hash_key>/verify/")
class CaptchaVerifyView(Resource):
    @ns.response(200, description="Captcha challenge is valid")
    @ns.response(400, description="Captcha challenge is invalid")
    @ns.response(404, description="Captcha challenge not found")
    def post(self, hash_key):
        """
        Verify captcha solution
        """
        self.services.captcha.verify(hash_key)
        return None, 200
