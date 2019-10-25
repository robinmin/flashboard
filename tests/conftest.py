import os
import json
import tempfile

import pytest

from flashboard.app import create_app
from flashboard.database import create_all_tables, db_trasaction
from flashboard.rbac import create_all_roles
from flashboard.services import UserService


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    # create the app with common test config
    app = create_app({
        # force into the testing model
        'TESTING': True,

        # leverage temp file system as the SQLite database
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path,

        # Disable CSRF tokens in the Forms (only valid for testing purposes!)
        'WTF_CSRF_ENABLED': False
    })

    # create the database and load test data
    with app.app_context():
        # import all models
        import flashboard.models

        # create them
        create_all_tables(app)

        # add meta data
        add_metadata_for_app(app)

        yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


# class AuthActions(object):
#     def __init__(self, client):
#         self._client = client

#     def login(self, username='test', password='test'):
#         return self._client.post(
#             '/api/user/login',
#             data={
#                 'username': username,
#                 'password': password
#             }
#         )

#     def logout(self):
#         return self._client.get('/api/user/logout')


# @pytest.fixture
# def auth(client):
#     """ User Authentication fixture """
#     return AuthActions(client)


@pytest.fixture
def api(client):
    """ User Authentication fixture """
    return ApiProxy(client)

###############################################################################


class ApiProxy(object):
    api_url_login = '/api/user/login'
    api_url_logout = '/api/user/logout'
    api_url_refresh = '/api/user/refresh'
    api_url_register = '/api/user/register'

    def __init__(self, client):
        self._client = client
        self.access_token = None

    def _api_get(self, url, with_token=True):
        headers = {
            'Accept': 'application/json',
        }
        if with_token:
            headers['Authorization'] = 'Bearer ' + (self.access_token or '')

        return self._client.get(url, headers=headers)

    def _api_post(self, url, data={}, with_token=True):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        if with_token:
            headers['Authorization'] = 'Bearer ' + (self.access_token or '')

        return self._client.post(url, data=json.dumps(data), headers=headers)

    #############################
    #
    # API proxy
    #
    #############################
    def login(self, email, password):
        return self._api_post(self.api_url_login, {
            'email': 'luonbin@hotmail.com',
            'password': 'Test001'
        }, with_token=False)

    def logout(self):
        return self._api_get(self.api_url_logout, with_token=True)

    def refresh(self, refresh_token):
        return self._api_post(self.api_url_refresh, {
            'refresh_token': refresh_token
        }, with_token=False)

    def register(self, name, email, password):
        return self._api_post(self.api_url_register, data={
            'name': name,
            'email': email,
            'password': password,
        })

    #############################
    #
    # Helper functions here
    #
    #############################

    def assert_dump(self, resp):
        print('=======================================>>')
        print('resp.status_code : ', resp.status_code)
        print(resp.get_json())
        print('<<=======================================')

    def assert_invalid_method(self, resp):
        assert resp and resp.status_code == 405

        json_resp = resp.get_json()
        assert json_resp and 'message' in json_resp \
            and json_resp['message'] == 'The method is not allowed for the requested URL.', \
            'Invalid HTTP method'

    def assert_invalid_method2(self, resp):
        assert resp and resp.status_code == 403

        json_resp = resp.get_json()
        print(json_resp)
        assert json_resp and 'message' in json_resp \
            and json_resp['message'] == 'Valid API Token required (Invalid header)', \
            'Invalid HTTP method'

    def assert_invalid_token(self, resp):
        assert resp and resp.status_code == 403

        json_resp = resp.get_json()
        assert json_resp and 'message' in json_resp \
            and json_resp['message'] == 'Valid API Token required (Invalid or expired token)', \
            'Invalid HTTP method'

    def assert_invalid_token2(self, resp):
        assert resp and resp.status_code == 403

        json_resp = resp.get_json()
        assert json_resp and 'message' in json_resp \
            and json_resp['message'] == 'Valid API Token required (Invalid owner_id)', \
            'Invalid HTTP method'

    def assert_normal_login(self, resp):
        assert resp and resp.status_code == 200

        json_resp = resp.get_json()
        assert json_resp and 'access_token' in json_resp and 'refresh_token' in json_resp \
            and json_resp['access_token'] and json_resp['refresh_token'], \
            'normal login on ' + ApiProxy.api_url_login

        return json_resp['access_token'], json_resp['refresh_token']

    def assert_normal_action(self, resp):
        assert resp and resp.status_code == 200

        json_resp = resp.get_json()
        assert json_resp and 'message' in json_resp and json_resp['message'] == 'OK', \
            'normal logout on ' + ApiProxy.api_url_login

    def assert_normal_refresh(self, resp):
        assert resp and resp.status_code == 200

        json_resp = resp.get_json()
        assert json_resp and 'access_token' in json_resp and 'refresh_token' in json_resp \
            and json_resp['access_token'] and json_resp['refresh_token'], \
            'normal refresh token on ' + ApiProxy.api_url_refresh

        return json_resp['access_token'], json_resp['refresh_token']

    def assert_invalid_register_exist(self, resp):
        assert resp and resp.status_code == 401

        json_resp = resp.get_json()
        assert json_resp and 'message' in json_resp \
            and json_resp['message'] == 'User name or email is already exist', \
            'Invalid username or email'


def add_metadata_for_app(app):
    # Add meta data for user-role
    create_all_roles()

    with db_trasaction() as txn:
        # add test user
        usvc = UserService()

        user, token, error = usvc.register_user(
            'robin', 'luonbin@hotmail.com', 'Test001')
        if user is None:
            app.logger.error(error or 'Unknown error in Sign Up')
        else:
            # user confirmation
            result, error = usvc.confirm_user(user, token.token)
            if not result:
                app.logger.error(error or 'Unknown error in comfirm user.')
