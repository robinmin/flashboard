from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.apps import custom_app_context as pwd_context

from flask_login import UserMixin

from .database import BaseModel


###############################################################################
class RolesUsers(BaseModel):
    __tablename__ = 'roles_users'

    id = Column(Integer(), primary_key=True, autoincrement=True)
    user_id = Column('user_id', Integer(), ForeignKey('users.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))


class RoleModel(BaseModel):
    __tablename__ = 'role'

    # define columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(255))

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

    # # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    # def __hash__(self):
    #     return hash(self.name)


class UserModel(UserMixin, BaseModel):
    __tablename__ = 'users'

    # define columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(64), nullable=False)
    private_salt = Column(String(64), nullable=False)

    actived = Column(Boolean(), default=False)
    authenticated = Column(Boolean(), default=False)
    last_login_at = Column(DateTime(), nullable=True)
    last_login_ip = Column(String(100), nullable=True)
    current_login_at = Column(DateTime(), nullable=True)
    current_login_ip = Column(String(100), nullable=True)
    login_count = Column(Integer(), default=0, nullable=False)
    signup_at = Column(DateTime(), nullable=True)
    confirmed_at = Column(DateTime(), nullable=True)

    # define relationship
    roles = relationship(
        'RoleModel',
        secondary='roles_users',
        backref=backref('users', lazy='dynamic')
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


class TokenModel(BaseModel):
    __tablename__ = 'token_mgr'

    id = Column(Integer(), primary_key=True, autoincrement=True)

    create_on = Column(DateTime(), nullable=False)
    expiry_on = Column(DateTime(), nullable=False)
    first_access_on = Column(DateTime(), nullable=True)
    last_access_on = Column(DateTime(), nullable=True)
    access_count = Column(Integer(), default=0, nullable=False)

    category = Column(Integer(), default=0, nullable=False)
    token = Column(String(172), nullable=False, unique=True)

    owner_id = Column('user_id', Integer(), ForeignKey('users.id'))

###############################################################################
