import jwt

from flask import Blueprint
from flask_login import login_user
from flask_restplus import Api
from flask_restplus.errors import abort as api_abort

from .utils import extract_authorization_from_header
from .services import UserService, TokenService

###############################################################################
# blueprints for API
bp = Blueprint('flashboard-api', __name__)

# API instance
authorizations = {
    'JWT': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT authorization key which must be started with "Bearer "'
    }
}
api = Api(
    bp,
    title='Flashboard API',
    version='1.0',
    # doc=False,  # disable Swagger UI entirely
    authorizations=authorizations,
    description='Flashboard API'
)


class ValidationException(Exception):
    def __init__(self, message='Validation error', error_field_name='unknown_field', *args, **kwargs):
        super().__init__(args, **kwargs)
        self.error_field_name = error_field_name
        self.message = message


@api.errorhandler(ValidationException)
def handle_validation_exception(error):
    return {'message': 'Validation error', 'errors': {error.error_field_name: error.message}}, 400


@api.errorhandler(jwt.ExpiredSignatureError)
def handle_expired_signature_error(error):
    return normal_response('Token expired', 401)


@api.errorhandler(jwt.InvalidTokenError)
@api.errorhandler(jwt.DecodeError)
@api.errorhandler(jwt.InvalidIssuerError)
def handle_invalid_token_error(error):
    return normal_response('Token incorrect, supplied or malformed', 401)


def normal_response(msg='OK', status_code=200):
    """ helper function for normal response """
    return {'message': msg or 'OK'}, status_code


def token_required(func):
    """ decorator for API token """

    def wrapper(*args, **kwargs):
        # verify access token
        access_token = extract_authorization_from_header()
        if access_token:
            tsvc = TokenService()
            token, msg = tsvc.verify(
                TokenService.TOKEN_JWT_ACCESS, None, access_token
            )
            if token and token.access_count is not None:
                # get user information and inject into global scope
                user = UserService().load_raw_user(token.owner_id)
                if user.actived:
                    login_user(user)
                return func(*args, **kwargs)
            else:
                api_abort(403, 'Valid API Token required ({})'.format(
                    msg or 'Invalid token'
                ))
        else:
            api_abort(403, 'Valid API Token required (Invalid header)')

    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper
