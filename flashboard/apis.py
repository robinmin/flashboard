from flask import Blueprint, request, url_for, current_app, render_template, get_flashed_messages
from flask_login import login_url
from flask_restplus import Resource, Namespace, fields, Api
from flask_restplus.errors import abort as api_abort
from flask_login import current_user

from .forms import LoginForm, SignupForm
from .services import UserService
from .factories import normal_response, token_required
from .utils import extract_authorization_from_header
from .services import UserService, TokenService
from .dtos import AppDTO
from .app import send_email

###############################################################################

# all build-in urls here
all_urls = {
    'login': 'flashboard.login',
    'logout': 'flashboard.logout',
    'signup': 'flashboard.signup',
    'confirm_email': 'flashboard.confirm_email',
    'home': 'flashboard.home',

    'admin': 'admin.index',
}

# class AppDTO:
#     api = Namespace('app', description='application related operations')

#     # normal response message
#     message = api.model('message', {
#         'message': fields.String(description='user Identifier')
#     })

#     # data form for uers register
#     user = api.model('user', {
#         'email': fields.String(required=True, description='user email address'),
#         'username': fields.String(required=True, description='user username'),
#         'password': fields.String(required=True, description='user password'),
#         'public_id': fields.String(description='user Identifier')
#     })

#     user_auth = api.model('auth_details', {
#         'email': fields.String(required=True, description='The email address'),
#         'password': fields.String(required=True, description='The user password '),
#     })

#     return_token_model = api.model('ReturnToken', {
#         'access_token': fields.String(required=True),
#         'refresh_token': fields.String(required=True)
#     })

#     # register_model = api.model('Register', {
#     #     'username': fields.String(required=True, description='user username'),
#     #     'password': fields.String(required=True, description='user password')
#     # })

# create namespaces instance
auth_ns = AppDTO.api


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(AppDTO.auth_details, validate=True)
    @auth_ns.response(200, 'Success', AppDTO.return_token)
    @auth_ns.response(401, 'Invalid username or password or inactive user')
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
                    msg = 'Failed to generate API tokens'
            else:
                status_code = 401
                msg = 'Invalid username or password or inactive user'
        else:
            status_code = 401
            msg = form.extract_errors() or 'Invalid username or password'
        return auth_ns.abort(status_code, msg or 'Unknown error')


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
    @auth_ns.response(401, 'Invalid refresh token')
    @auth_ns.doc(security='JWT')
    def post(self):
        """ API interface for refresh access token """

        # get refresh token from parameter
        refresh_token = auth_ns.payload['refresh_token'] if 'refresh_token' in auth_ns.payload else ''
        if refresh_token is None:
            return auth_ns.abort(401, 'Invalid refresh token')

        tsvc = TokenService()

        # verify refresh token
        token, msg = tsvc.verify(
            TokenService.TOKEN_JWT_REFRESH, None, refresh_token
        )

        if token is None or token.access_count is None:
            return auth_ns.abort(401, msg or 'Invalid or expired refresh token')

        # purge existing tokens
        tsvc.purge_auth_tokens(token)

        # re-generate refresh token and access token
        access_token, refresh_token = tsvc.generate_auth_tokens(token.owner_id)
        if access_token and refresh_token:
            return {'access_token': access_token, 'refresh_token': refresh_token}, 200

        return auth_ns.abort(401, 'Failed to re-generate API tokens')


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(AppDTO.register_details, validate=True)
    @auth_ns.marshal_with(AppDTO.return_message)
    @auth_ns.response(401, 'username or password incorrect')
    @auth_ns.doc(security='JWT')
    @token_required
    def post(self):
        """ API interface for user registration """

        if not current_user.is_authenticated:
            return auth_ns.abort(401, 'Invalid user')

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
                subject = 'Please confirm your email'
                send_email(current_app, user.email, subject, html)

                return normal_response()
            else:
                status_code = 401
                msg = error or 'Unknown error in user registration'
        else:
            status_code = 401
            msg = form.extract_errors() or 'Invalid username or password'
        return auth_ns.abort(status_code, msg or 'Unknown error')
