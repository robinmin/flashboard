from wtforms import StringField, BooleanField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, InputRequired
from wtforms.fields.html5 import EmailField
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _

from .utils import strip_space, strip_space_lower, flatten
###############################################################################


class FormMixin(object):
    def skip_csrf_validation(self):
        if hasattr(self, '_fields') and 'csrf_token' in self._fields:
            del self._fields['csrf_token']

    def extract_errors(self, sep='; '):
        return sep.join(flatten(self.errors.values())) if self.errors and len(self.errors) > 0 else ''


class LoginForm(FlaskForm, FormMixin):
    # The first parameter is for form label
    # username = StringField('User Name', validators=[
    #     InputRequired('User Name is required'),
    #     Length(3, 64),
    # ])
    next = HiddenField('next')
    email = EmailField(_('Email'), validators=[
        InputRequired(_('Email is required')),
        Length(3, 64),
        Email(_('Please input valid email, e.g. : username@domain.com')),
    ], filters=[strip_space_lower])
    password = PasswordField(_('Password'), validators=[
        InputRequired(_('Password is required')),
        Length(6, 12),
    ], filters=[strip_space])
    remember_me = BooleanField(_('Remember me'), default=False)
    submit = SubmitField(_('Login'))


class SignupForm(FlaskForm, FormMixin):
    # The first parameter is for form label
    name = StringField(_('User Name'), validators=[
        DataRequired(_('User Name is required')),
        Length(3, 64),
    ], filters=[strip_space])
    email = EmailField(_('Email'), validators=[
        DataRequired(_('Email is required')),
        Length(3, 64),
        Email(_('Please input valid email, e.g. : username@domain.com')),
    ], filters=[strip_space_lower])
    password = PasswordField(_('Password'), validators=[
        DataRequired(_('Password is required')),
        Length(6, 12),
    ], filters=[strip_space])
    password2 = PasswordField(_('Repeated Password'), validators=[
        DataRequired(_('Repeated password is required too')),
        Length(6, 12),
    ], filters=[strip_space])
    submit = SubmitField(_('Sign up'))
