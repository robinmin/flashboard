from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from passlib.apps import custom_app_context as pwd_context

from flask_login import UserMixin

from .base import BaseModel
###############################################################################


class RoleModel(BaseModel):
    __tablename__ = 'sys_role'

    # define columns
    id = Column('n_role_id', Integer(), primary_key=True,
                autoincrement=True, comment='Role ID')
    name = Column('c_name', String(64), unique=True,
                  nullable=False, index=True, comment='Role Name')
    description = Column('c_desc', String(255), comment='Description')

    # define methods
    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Role %r>' % (self.name)

    # __str__ is required by Flask-Admin, so we can have human-readable values for the Role when editing a User.
    # If we were using Python 2.7, this would be __unicode__ instead.
    def __str__(self):
        return self.name

    # # __hash__ is required to avoid the exception TypeError: unhashable type: 'sys_role' when saving a User
    # def __hash__(self):
    #     return hash(self.name)


class UserModel(UserMixin, BaseModel):
    __tablename__ = 'sys_user'

    # define columns
    id = Column('n_user_id', Integer(), primary_key=True,
                autoincrement=True, comment='User ID')
    name = Column('c_name', String(64), unique=True,
                  nullable=False, index=True, comment='Name')
    email = Column('c_email', String(128), unique=True, nullable=False,
                   index=True, comment='Email')
    password = Column('c_password', String(
        256), nullable=False, comment='Password')
    private_salt = Column('c_private_salt', String(
        256), nullable=False, comment='Private salt for password hash')

    actived = Column('b_actived', Boolean(),
                     default=False, comment='Active flag')
    authenticated = Column('b_authenticated', Boolean(),
                           default=False, comment='Authentication flag')
    last_login_at = Column('d_last_login_at', DateTime(),
                           comment='Last login timestamp')
    last_login_ip = Column('c_last_login_ip', String(
        128), comment='Last login IP')
    current_login_at = Column('d_current_login_at',
                              DateTime(), comment='Current login timestamp')
    current_login_ip = Column('c_current_login_ip', String(
        128), comment='Current login IP')
    login_count = Column('n_login_count', Integer(), default=0,
                         nullable=False, comment='Login count')
    signup_at = Column('d_signup_at', DateTime(), comment='Sign-up date')
    confirmed_at = Column('d_confirmed_at', DateTime(),
                          comment='Comfirm date')

    # define relationship
    roles = relationship(
        'RoleModel',
        secondary='sys_map_r2u',
        backref=backref('sys_user', lazy='dynamic')
    )

    # define methods
    @property
    def is_active(self):
        """ True, as all users are active """

        return self.actived

    @property
    def is_authenticated(self):
        """ Return True if the user is authenticated """
        return self.authenticated

    @property
    def is_anonymous(self):
        """ False, as anonymous users aren't supported """

        return False

    def get_id(self):
        """ Return the email address to satisfy Flask-Login's requirements """
        try:
            return unicode(self.email)  # python 2
        except NameError:
            return str(self.email)      # python 3

    def __init__(self, name=None, password=None, email=None):
        self.name = name
        self.password = password
        self.email = email

    def __repr__(self):
        return '<User %r>' % (self.name)

    def hash_password(self, password):
        self.password = pwd_context.hash(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)


class RolesUsers(BaseModel):
    __tablename__ = 'sys_map_r2u'

    id = Column('n_map_r2u', Integer(), primary_key=True,
                autoincrement=True, comment='Map ID of rule to user')
    user_id = Column('n_user_id', Integer(), ForeignKey(
        'sys_user.n_user_id'), comment='User ID')
    role_id = Column('n_role_id', Integer(), ForeignKey(
        'sys_role.n_role_id'), comment='Role ID')


class TokenModel(BaseModel):
    __tablename__ = 'sys_token_mgr'

    id = Column('n_token_id', Integer(), primary_key=True,
                autoincrement=True, comment='Token ID')

    create_on = Column('d_create', DateTime(),
                       nullable=False, default=func.now(), comment='Create date')
    expiry_on = Column('d_expiry', DateTime(),
                       nullable=False, comment='Expiry date')
    first_access_on = Column('d_first_access', DateTime(),
                             nullable=True, comment='First access date')
    last_access_on = Column('d_last_access', DateTime(),
                            nullable=True, comment='Last access date')
    access_count = Column('n_access_count', Integer(), default=0,
                          nullable=False, comment='Access count')

    category = Column('n_category', Integer(), default=0,
                      nullable=False, comment='Token category')
    token = Column('c_token', String(256), nullable=False,
                   unique=True, comment='Token')
    random_seed = Column('n_random_seed', Integer(),
                         default=0, nullable=True, comment='Random seed')

    owner_id = Column('n_owner_id', Integer(),
                      ForeignKey('sys_user.n_user_id'), comment='Owner ID')
