from flask import Blueprint, request
from flask_restplus import Resource, Namespace, fields, Api
from flask_restplus.errors import abort as api_abort
from flask_login import current_user

from .forms import LoginForm
from .services import UserService
from .factories import normal_response, token_required
from .utils import extract_authorization_from_header
from .services import UserService, TokenService
from .dtos import AppDTO
###############################################################################


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


# get the namespaces of authentication
# auth_ns = AppDTO.api
# auth_ns = Namespace('app', description='application related operations')

# api.add_namespace(auth_ns, path='/user')

# @auth_ns.route('/register')
# class Register(Resource):
#     # 4-16 symbols, can contain A-Z, a-z, 0-9, _ (_ can not be at the begin/end and can not go in a row (__))
#     USERNAME_REGEXP = r'^(?![_])(?!.*[_]{2})[a-zA-Z0-9._]+(?<![_])$'

#     # 6-64 symbols, required upper and lower case letters. Can contain !@#$%_  .
#     PASSWORD_REGEXP = r'^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])[\w\d!@#$%_]{6,64}$'

#     @auth_ns.expect(register_model, validate=True)
#     @auth_ns.marshal_with(User.user_resource_model)
#     @auth_ns.response(400, 'username or password incorrect')
#     def post(self):
#         pass
#         if not re.search(self.USERNAME_REGEXP, v1_api.payload['username']):
#             raise ValidationException(error_field_name='username',
#                                       message='4-16 symbols, can contain A-Z, a-z, 0-9, _ \
#                                       (_ can not be at the begin/end and can not go in a row (__))')

#         if not re.search(self.PASSWORD_REGEXP, v1_api.payload['password']):
#             raise ValidationException(error_field_name='password',
#                                       message='6-64 symbols, required upper and lower case letters. Can contain !@#$%_')

#         if User.query.filter_by(username=v1_api.payload['username']).first():
#             raise ValidationException(
#                 error_field_name='username', message='This username is already exists')

#         user = User(
#             username=v1_api.payload['username'], password=v1_api.payload['password'])
#         db.session.add(user)
#         db.session.commit()
#         return user

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
        form = LoginForm()
        form.skip_csrf_validation()
        form.email = email
        form.password = password
        form.remember_me = remember_me

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
            msg = 'Invalid username or password'
        return auth_ns.abort(status_code, msg or 'Unknown error')


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.response(200, 'Success', AppDTO.return_message)
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
    def post(self):
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
