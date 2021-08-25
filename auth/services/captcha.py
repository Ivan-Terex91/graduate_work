from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
from uuid import UUID, uuid4

from core.db import CaptchaChallenge
from core.exceptions import BadRequestError, NotFound
from multicolorcaptcha import CaptchaGenerator
from sqlalchemy.orm import Session


class CaptchaChallengeExpired(BadRequestError):
    pass


class CaptchaChallengeInvalidSolution(BadRequestError):
    pass


# Captcha image size number (2 -> 640x360)
CAPCTHA_SIZE_NUM = 2


class CaptchaService:
    def __init__(self, session: Session):
        self.session = session

    def get(self, id: UUID) -> CaptchaChallenge:
        captcha_challenge = self.session.query(CaptchaChallenge).get({"id": id})
        if not captcha_challenge:
            raise NotFound("Captcha challenge not found")

        if captcha_challenge.exp.replace(tzinfo=timezone.utc) < datetime.now(
            tz=timezone.utc
        ):
            raise CaptchaChallengeExpired("Captcha challenge expired")

        return captcha_challenge

    def create(self) -> CaptchaChallenge:
        generator = CaptchaGenerator(CAPCTHA_SIZE_NUM)
        captcha = generator.gen_captcha_image(difficult_level=3)

        b = BytesIO()
        image = captcha["image"]
        image.save(b, "png")
        b.seek(0)

        id = uuid4()
        hash_key = sha256((f'{id}{captcha["characters"]}').encode()).hexdigest()
        captcha_challenge = CaptchaChallenge(
            id=id,
            hash_key=hash_key,
            payload=b.read(),
            exp=datetime.now(tz=timezone.utc) + timedelta(minutes=5),
        )
        self.session.add(captcha_challenge)
        self.session.flush()
        return captcha_challenge

    def delete(self, id: UUID):
        return (
            self.session.query(CaptchaChallenge)
            .filter(CaptchaChallenge.id == id)
            .delete()
        )

    def verify(self, hash_key: str) -> bool:
        captcha_challenge = (
            self.session.query(CaptchaChallenge)
            .filter(CaptchaChallenge.hash_key == hash_key)
            .first()
        )

        if not captcha_challenge:
            raise NotFound("Captcha challenge not found or hash key is invalid")

        if captcha_challenge.exp.replace(tzinfo=timezone.utc) < datetime.now(
            tz=timezone.utc
        ):
            raise CaptchaChallengeExpired("Captcha challenge expired")

        self.delete(captcha_challenge.id)

        return True
