from wtforms import StringField, BooleanField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email
from flask_wtf import FlaskForm

from .utils import strip_space, strip_space_lower
###############################################################################


class LoginForm(FlaskForm):
    # The first parameter is for form label
    # username = StringField('User Name', validators=[
    #     DataRequired(message='User Name is required'),
    #     Length(3, 64),
    # ])
    next = HiddenField('next')
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Length(3, 64),
        Email(message='Please input valid email, e.g. : username@domain.com'),
    ], filters=[strip_space_lower])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(6, 12),
    ], filters=[strip_space])
    remember_me = BooleanField('Remember me', default=False)
    submit = SubmitField('Login')


class SignupForm(FlaskForm):
    # The first parameter is for form label
    name = StringField('User Name', validators=[
        DataRequired(message='User Name is required'),
        Length(3, 64),
    ], filters=[strip_space])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Length(3, 64),
        Email(message='Please input valid email, e.g. : username@domain.com'),
    ], filters=[strip_space_lower])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(6, 12),
    ], filters=[strip_space])
    password2 = PasswordField('Repeated Password', validators=[
        DataRequired(message='Repeated password is required too'),
        Length(6, 12),
    ], filters=[strip_space])
    submit = SubmitField('Sign-up')
