from flask_restplus import Namespace, fields
from flask_babel import gettext as _


class AppDTO:
    api = Namespace('app', description=_('application related operations'))

    return_message = api.model('return_message', {
        'message': fields.String(description=_('message'))
    })

    auth_details = api.model('auth_details', {
        'email': fields.String(required=True, description=_('email address')),
        'password': fields.String(required=True, description=_('user password ')),
    })

    return_token = api.model('return_token', {
        'access_token': fields.String(required=True, description=_('API access token')),
        'refresh_token': fields.String(required=True, description=_('API refresh token')),
    })

    refresh_details = api.model('refresh_details', {
        'refresh_token': fields.String(required=True, description=_('API refresh token')),
    })

    register_details = api.model('register_details', {
        'name': fields.String(required=True, description=_('user name')),
        'email': fields.String(required=True, description=_('email address')),
        'password': fields.String(required=True, description=_('password')),
    })
