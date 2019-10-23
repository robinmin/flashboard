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
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path,
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


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/api/user/login',
            data={
                'username': username,
                'password': password
            }
        )

    def logout(self):
        return self._client.get('/api/user/logout')


@pytest.fixture
def auth(client):
    """ User Authentication fixture """
    return AuthActions(client)


def post_json(client, url, json_dict):
    """ Send dictionary json_dict as a json to the specified url """
    return client.post(url, data=json.dumps(json_dict), content_type='application/json')


def json_of_response(response):
    """ Decode json from response """
    return json.loads(response.data.decode('utf8'))
