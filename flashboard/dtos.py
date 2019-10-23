from flask_restplus import Resource, Namespace, fields, Api


class AppDTO:
    api = Namespace('app', description='application related operations')

    return_message = api.model('return_message', {
        'message': fields.String(description='message')
    })

    auth_details = api.model('auth_details', {
        'email': fields.String(required=True, description='The email address'),
        'password': fields.String(required=True, description='The user password '),
    })

    return_token = api.model('return_token', {
        'access_token': fields.String(required=True, description='API access token'),
        'refresh_token': fields.String(required=True, description='API refresh token'),
    })

    refresh_details = api.model('refresh_details', {
        'refresh_token': fields.String(required=True, description='API refresh token'),
    })
