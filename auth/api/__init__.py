from http import HTTPStatus

from flask_restx import Api

from core.exceptions import (AuthError, AuthorizationError, BadRequestError,
                             EmailUsedError, NotFound)

api = Api(title="Auth")


@api.errorhandler(NotFound)
def handle_not_found_error(error):
    return {"message": f"{error!s}"}, HTTPStatus.NOT_FOUND


@api.errorhandler(AuthError)
def handle_permission_error(error):
    return {"message": f"{error!s}"}, HTTPStatus.UNAUTHORIZED


@api.errorhandler(EmailUsedError)
def handle_email_used_error(error):
    return {"message": f"{error}"}, HTTPStatus.CONFLICT


@api.errorhandler(AuthorizationError)
def handle_authorization_error(error):
    return {"message": f"{error!s}"}, HTTPStatus.FORBIDDEN


@api.errorhandler(BadRequestError)
def handle_bad_request_error(error):
    return {"message": f"{error!s}"}, HTTPStatus.BAD_REQUEST
