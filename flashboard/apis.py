import jwt

from flask import request, url_for, current_app, render_template, Blueprint
from flask_login import login_url
from flask_restplus import Resource, Api
from flask_login import current_user
from flask_babel import gettext as _

from config.config import all_urls
from .forms import LoginForm, SignupForm
from .utils import normal_response, extract_authorization_from_header, ValidationException
from .services import UserService, TokenService, token_required
from .dtos import AppDTO
from .app import send_email

###############################################################################
# blueprints for API
bp = Blueprint('flashboard-api', __name__)

# API instance
authorizations = {
    'JWT': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': _('JWT authorization key which must be started with "Bearer "')
    }
}
api = Api(
    bp,
    title=_('Flashboard API'),
    version='1.0',
    # doc=False,  # disable Swagger UI entirely
    authorizations=authorizations,
    description=_('Flashboard API')
)


@api.errorhandler(ValidationException)
def handle_validation_exception(error):
    return {'message': _('Validation error'), 'errors': {error.error_field_name: error.message}}, 400


@api.errorhandler(jwt.ExpiredSignatureError)
def handle_expired_signature_error(error):
    return normal_response(_('Token expired'), 401)


@api.errorhandler(jwt.InvalidTokenError)
@api.errorhandler(jwt.DecodeError)
@api.errorhandler(jwt.InvalidIssuerError)
def handle_invalid_token_error(error):
    return normal_response(_('Token incorrect, supplied or malformed'), 401)


# create namespaces instance
auth_ns = AppDTO.api


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(AppDTO.auth_details, validate=True)
    @auth_ns.response(200, 'Success', AppDTO.return_token)
    @auth_ns.response(401, _('Invalid username or password or inactive user'))
    def post(self):
        """ API interface for user login """

        # load submitted data
        email = auth_ns.payload['email'] if 'email' in auth_ns.payload else ''
        password = auth_ns.payload['password'] if 'password' in auth_ns.payload else ''
        remember_me = False

        # mimic the LoginForm
        form = LoginForm(data={
            'email': email,
            'password': password,
            'remember_me': remember_me,
        })
        form.skip_csrf_validation()

        status_code = 200
        msg = ''

        # input data validation
        if form.validate_on_submit():
            # check user account and password exist or not
            usvc = UserService()
            user = usvc.load_valid_user(email, password)
            login_ip = request.environ.get(
                'HTTP_X_REAL_IP', request.remote_addr
            )

            # update user login information
            if user and usvc.login_user(user, remember=remember_me, login_ip=login_ip):
                access_token, refresh_token = TokenService().generate_auth_tokens(
                    user.id
                )
                # generate tokens
                if access_token and refresh_token:
                    return {'access_token': access_token, 'refresh_token': refresh_token}, 200
                else:
                    status_code = 401
                    msg = _('Failed to generate API tokens')
            else:
                status_code = 401
                msg = _('Invalid username or password or inactive user')
        else:
            status_code = 401
            msg = form.extract_errors() or _('Invalid username or password')
        return auth_ns.abort(status_code, msg or _('Unknown error'))


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.response(200, 'Success', AppDTO.return_message)
    @auth_ns.doc(security='JWT')
    @token_required
    def get(self):
        """ API interface for user logout """

        if current_user.is_authenticated:
            # Purge all access tokens and refresh tokens
            access_token = extract_authorization_from_header()
            if access_token:
                TokenService().purge(TokenService.TOKEN_JWT_ACCESS, current_user.id, access_token)

            # update user information
            UserService().logout_user(current_user)
        return normal_response()


@auth_ns.route('/refresh')
class Refresh(Resource):
    @auth_ns.expect(AppDTO.refresh_details, validate=True)
    @auth_ns.response(200, 'Success', AppDTO.return_token)
    @auth_ns.response(401, _('Invalid refresh token'))
    @auth_ns.doc(security='JWT')
    def post(self):
        """ API interface for refresh access token """

        # get refresh token from parameter
        refresh_token = auth_ns.payload['refresh_token'] if 'refresh_token' in auth_ns.payload else ''
        if refresh_token is None:
            return auth_ns.abort(401, _('Invalid refresh token'))

        tsvc = TokenService()

        # verify refresh token
        token, msg = tsvc.verify(
            TokenService.TOKEN_JWT_REFRESH, None, refresh_token
        )

        if token is None or token.access_count is None:
            return auth_ns.abort(401, msg or _('Invalid or expired refresh token'))

        # purge existing tokens
        tsvc.purge_auth_tokens(token)

        # re-generate refresh token and access token
        access_token, refresh_token = tsvc.generate_auth_tokens(token.owner_id)
        if access_token and refresh_token:
            return {'access_token': access_token, 'refresh_token': refresh_token}, 200

        return auth_ns.abort(401, _('Failed to re-generate API tokens'))


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(AppDTO.register_details, validate=True)
    @auth_ns.marshal_with(AppDTO.return_message)
    @auth_ns.response(401, _('username or password incorrect'))
    @auth_ns.doc(security='JWT')
    @token_required
    def post(self):
        """ API interface for user registration """

        if not current_user.is_authenticated:
            return auth_ns.abort(401, _('Invalid user'))

        # load submitted data
        name = auth_ns.payload['name'] if 'name' in auth_ns.payload else ''
        email = auth_ns.payload['email'] if 'email' in auth_ns.payload else ''
        password = auth_ns.payload['password'] if 'password' in auth_ns.payload else ''

        # mimic the SignupForm
        form = SignupForm(data={
            'name': name,
            'email': email,
            'password': password,
            'password2': password,
        })
        form.skip_csrf_validation()

        status_code = 200
        msg = ''

        # input data validation
        if form.validate_on_submit():
            usvc = UserService()
            user, token, error = usvc.register_user(name, email, password)
            if user and token:
                # triger activation email
                confirm_url = login_url(
                    login_view=url_for(
                        all_urls['login'],
                        _external=True
                    ),
                    next_url=url_for(
                        all_urls['confirm_email'],
                        token=token.token
                    ))
                html = render_template(
                    'activate.html', confirm_url=confirm_url
                )
                subject = _('Please confirm your email')
                send_email(current_app, user.email, subject, html)

                return normal_response()
            else:
                status_code = 401
                msg = error or _('Unknown error in user registration')
        else:
            status_code = 401
            msg = form.extract_errors() or _('Invalid username or password')
        return auth_ns.abort(status_code, msg or _('Unknown error'))
