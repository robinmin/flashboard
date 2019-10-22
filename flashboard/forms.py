from wtforms import StringField, BooleanField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email
from flask_wtf import FlaskForm


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
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(6, 12),
    ])
    remember_me = BooleanField('Remember me', default=False)
    submit = SubmitField('Login')


class SignupForm(FlaskForm):
    # The first parameter is for form label
    name = StringField('User Name', validators=[
        DataRequired(message='User Name is required'),
        Length(3, 64),
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Length(3, 64),
        Email(message='Please input valid email, e.g. : username@domain.com'),
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(6, 12),
    ])
    password2 = PasswordField('Repeated Password', validators=[
        DataRequired(message='Repeated password is required too'),
        Length(6, 12),
    ])
    submit = SubmitField('Sign-up')
