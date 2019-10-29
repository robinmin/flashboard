import datetime
import random

from sqlalchemy import or_
from flask_login import login_user, logout_user
from flask_babel import lazy_gettext as _

from config.rbac import DEFAULT_ROLE
from .database import db_trasaction, save_item, BaseModel
from .models import UserModel, RoleModel, RolesUsers, TokenModel
from .utils import is_strong, prepare_for_hash, generate_random_salt, encode_jwt_token, decode_jwt_token


class BaseService(object):
    def __init__(self):
        self.klass = BaseModel

    def get_all(self):
        """ get all items """
        return self.klass.query.all()

    def get_item(self, **kwargs):
        """ get one item by provided conditions """
        return self.klass.query.filter(**kwargs)

    def get_first(self, **kwargs):
        """ get one item by provided conditions """
        return self.get_item(**kwargs).first()

    def save_item(self, obj):
        """ save one item into database """
        return save_item(obj)


class UserService(BaseService):
    def __init__(self):
        self.klass = UserModel

    def load_user(self, user_id):
        """ load user information by id """
        if user_id is not None:
            return self.klass.query.filter(self.klass.email == user_id).first()

    def load_raw_user(self, user_info):
        """ load valid user information by user information """
        if hasattr(user_info, 'authenticated'):
            return user_info
        elif isinstance(user_info, str):
            if user_info.find('@'):
                return self.klass.query.filter(
                    self.klass.email == user_info
                ).first()
            return self.klass.query.filter(
                self.klass.name == user_info
            ).first()
        elif isinstance(user_info, int):
            return self.klass.query.get(user_info)
        else:
            return None

    def load_valid_user(self, user_info, password, include_inactive=False):
        """ load valid user information and check password """

        user = self.load_raw_user(user_info)
        if user:
            from flask import current_app
            public_salt = current_app.config['SECURITY_PASSWORD_SALT']
            if not user.verify_password(prepare_for_hash(
                password, public_salt, user.private_salt
            )):
                return None

            return user if user.is_active or include_inactive else None
        return None

    def login_user(self, user_info, remember, login_ip, force=False):
        """ process user login information """

        user = self.load_raw_user(user_info)
        if not user:
            return None

        user.authenticated = True
        user.last_login_at = user.current_login_at
        user.last_login_ip = user.current_login_ip
        user.current_login_at = datetime.datetime.utcnow()
        user.current_login_ip = login_ip
        user.login_count = user.login_count + 1

        if self.save_item(user):
            return login_user(user, remember=remember, force=force)
        return None

    def logout_user(self, user):
        if hasattr(user, 'authenticated'):
            user.authenticated = False
            if self.save_item(user):
                return logout_user()
        return None

    def register_user(self, name, email, password):
        msg = ''

        # check complecity of password
        if not is_strong(password):
            msg = _(
                'Password is not strong engough(Must including upper case and lower case and digit)')
        else:
            # check existence of user name and email
            user = self.klass.query.filter(or_(
                self.klass.name == name,
                self.klass.email == email
            )).first()
            if user:
                msg = _('User name or email is already exist')
            else:
                from flask import current_app
                public_salt = current_app.config['SECURITY_PASSWORD_SALT']

                # insert into database
                user = self.klass(name=name, email=email)
                user.authenticated = False
                user.activate = False
                user.signup_at = datetime.datetime.utcnow()
                user.private_salt = generate_random_salt(64)
                user.hash_password(prepare_for_hash(
                    password, public_salt, user.private_salt
                ))

                msg = ''
                token = None
                try:
                    with db_trasaction() as txn:
                        # add user
                        txn.try_assert(
                            not txn.save_item(user),
                            _('Failed to add user into user table')
                        )

                        # generate activation token
                        tsvc = TokenService()
                        token = tsvc.create(
                            category=TokenService.TOKEN_USER_ACTIVATION,
                            user_id=user.id,
                            duration=7200
                        )
                        txn.try_assert(
                            not token, _('Failed to add activation token')
                        )

                        # grant default role
                        txn.try_assert(
                            not self.grant_role(user, DEFAULT_ROLE),
                            _('Failed to grant default role')
                        )
                except Exception as exp:
                    msg = str(exp)
                    user = None
                    token = None
                return user, token, msg
        return None, None, msg

    def confirm_user(self, user_info, act_token):
        """ confirm user activation """

        msg = ''
        result = True
        tsvc = TokenService()
        try:
            with db_trasaction() as txn:
                user = self.load_raw_user(user_info)
                txn.try_assert(
                    user is None,
                    _('Invalid user with activation token')
                )
                token, rsp_msg = tsvc.verify(
                    TokenService.TOKEN_USER_ACTIVATION, user.id, act_token
                )
                txn.try_assert(
                    token is None or token.access_count is None,
                    rsp_msg or _('Invalid activation token')
                )
                txn.try_assert(
                    token.access_count != 1,
                    _('Used activation token')
                )
                user.actived = True
                user.confirmed_at = datetime.datetime.utcnow()
                txn.try_assert(
                    not txn.save_item(user),
                    _('Failed to update actived flag')
                )
        except Exception as exp:
            msg = str(exp)
            result = False
        return result, msg

    def has_role(self, user_info, role):
        """
            Returns `True` if the user identifies with the specified role.
              :param role: A role name or `Role` instance
        """
        if not user_info or not role:
            return False

        # get user information
        user = self.load_raw_user(user_info)
        if user is None:
            return False

        if isinstance(role, str):
            return role in (role.name for role in user.roles)
        else:
            return role in self.roles

    def grant_role(self, user_info, role):
        """ grant particular role to current user """

        # sanity checks
        if not user_info or not role:
            return False

        # get user information
        user = self.load_raw_user(user_info)
        if user is None:
            return False

        # check role existence and retrieve role_id
        if isinstance(role, str):
            role_info = RoleModel.query.filter(RoleModel.name == role).first()
        else:
            role_info = RoleModel.query.get(role)
        if not role_info:
            return False

        new_obj = RolesUsers()
        new_obj.user_id = user.id
        new_obj.role_id = role_info.id
        return save_item(new_obj)

    def revoke_role(self, user_info, role):
        """ revoke particular role from current user """

        # sanity checks
        if not user_info or not role:
            return False

        # get user information
        user = self.load_raw_user(user_info)
        if user is None:
            return False

        # check role existence and retrieve role_id
        if isinstance(role, str):
            role_info = RoleModel.query.filter(RoleModel.name == role).first()
        else:
            role_info = RoleModel.query.get(role)
        if not role_info:
            return False

        row_count = RolesUsers.query.filter(
            RolesUsers.id == role_info.id
        ).delete()
        if not row_count or row_count <= 0:
            return False

        return True


class TokenService(BaseService):
    # user configuration token
    TOKEN_USER_ACTIVATION = 0

    # JWT access token
    TOKEN_JWT_ACCESS = 1

    # JWT refresh token
    TOKEN_JWT_REFRESH = 2

    def __init__(self):
        self.klass = TokenModel

    def create(self, category, user_id, duration=7200, random_seed=0):
        """ generate new token """

        token = self.klass()
        token.create_on = datetime.datetime.utcnow()
        token.expiry_on = token.create_on + \
            datetime.timedelta(seconds=duration)
        token.category = category
        token.owner_id = user_id
        token.random_seed = random_seed

        # generate token
        if category == self.TOKEN_JWT_ACCESS or category == self.TOKEN_JWT_REFRESH:
            token.token = encode_jwt_token(user_id, duration, random_seed)
        else:
            token.token = generate_random_salt(128)

        if self.save_item(token):
            return token
        return None

    def get_last_one(self, category, owner_id):
        """ get last available token """
        from sqlalchemy import and_, desc

        now = datetime.datetime.utcnow()
        return self.klass.query.filter(and_(
            self.klass.category == category,
            self.klass.owner_id == owner_id,
            self.klass.create_on <= now,
            now < self.klass.expiry_on
        )).order_by(desc(self.klass.create_on)).first()

    def verify(self, category, owner_id, token):
        """
            verify provided token and retrieve the account counte.
            It will return the token object if token is valid, otherwise return None.
        """

        if not token:
            return None, _('Invalid token')

        if owner_id is None and category in [self.TOKEN_JWT_ACCESS, self.TOKEN_JWT_REFRESH]:
            # decode owner_id from provided token
            payload, msg = decode_jwt_token(token)
            if payload and 'uid' in payload:
                owner_id = int(payload['uid'])

        if not owner_id:
            return None, _('Invalid owner_id')

        # retrieve stored token and check with provided one
        stored_token = self.get_last_one(category, owner_id)
        act_token = stored_token.token if stored_token else ''
        if isinstance(act_token, bytes):
            act_token = act_token.decode('utf-8')
        if stored_token and act_token == token:
            now = datetime.datetime.utcnow()

            if stored_token.first_access_on is None:
                stored_token.first_access_on = now
            stored_token.last_access_on = now
            stored_token.access_count = (stored_token.access_count or 0) + 1
            if self.save_item(stored_token):
                return stored_token, ''
        return None, _('Invalid or expired token')

    def purge(self, category, owner_id, token):
        """ purge current access token if any valid token has been provided """

        result = False
        with db_trasaction():
            if self.klass.query.filter(
                self.klass.category == category,
                self.klass.owner_id == owner_id,
                self.klass.token == token
            ).delete() == 1:
                result = True
        return result

    def generate_auth_tokens(self, user_id):
        """ generate access token and refresh token """

        # generate random integer as the pair refference
        random.seed(datetime.datetime.utcnow())
        random_seed = random.randint(0, 65535)

        access_token = self.create(
            self.TOKEN_JWT_ACCESS, user_id, 115 * 60, random_seed
        )
        refresh_token = self.create(
            self.TOKEN_JWT_REFRESH, user_id, 30 * 24 * 60 * 60, random_seed
        )
        return access_token.token if access_token else None, refresh_token.token if refresh_token else None

    def purge_auth_tokens(self, token):
        """ purge access token and refresh token """

        # sanity check
        if token is None or token.__class__.__name__ != self.klass.__name__:
            return None
        if token.token is None or token.category != self.TOKEN_JWT_REFRESH:
            return None

        # cache random seed
        random_seed = token.random_seed
        owner_id = token.owner_id

        result = True
        with db_trasaction():
            # purge refresh token
            if self.klass.query.filter(
                self.klass.category == self.TOKEN_JWT_REFRESH,
                self.klass.owner_id == owner_id,
                self.klass.token == token.token
            ).delete() != 1:
                result = False

            # purge access token
            if self.klass.query.filter(
                self.klass.category == self.TOKEN_JWT_ACCESS,
                self.klass.owner_id == owner_id,
                self.klass.random_seed == random_seed
            ).delete() != 1:
                result = False

        return result
