import pytest

from .conftest import post_json, json_of_response


class ApiProxy(object):
    api_url_login = '/api/user/login'
    api_url_logout = '/api/user/logout'
    api_url_refresh = '/api/user/refresh'
    api_url_register = '/api/user/register'

    def __init__(self, client):
        self._client = client
        self.access_token = None

    #############################
    #
    # API proxy
    #
    #############################
    def login(self, email, password):
        return post_json(self._client, self.api_url_login, {
            'email': 'luonbin@hotmail.com',
            'password': 'Test001'
        })

    def logout(self):
        return self._client.get(self.api_url_logout, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + (self.access_token or '')}
        )

    def refresh(self, refresh_token):
        return post_json(self._client, self.api_url_refresh, {
            'refresh_token': refresh_token
        })

    def register(self, name, email, password):
        return post_json(self._client, self.api_url_register, {
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

    def assert_normal_logout(self, resp):
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


def test_login(client, auth):
    proxy = ApiProxy(client)

    # test that viewing the page renders without template errors
    proxy.assert_invalid_method(client.get(ApiProxy.api_url_login))

    try:
        # normal login
        access_token, refresh_token = proxy.assert_normal_login(
            proxy.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token into proxy
        proxy.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
        # login after login
        new_access_token, new_refresh_token = proxy.assert_normal_login(
            proxy.login('luonbin@hotmail.com', 'Test001')
        )

        # logout with the old access token
        proxy.assert_invalid_token(proxy.logout())

        # update access token
        proxy.access_token = new_access_token
    finally:
        # normal logout
        proxy.assert_normal_logout(proxy.logout())


def test_loout(client, auth):
    proxy = ApiProxy(client)

    # test that viewing the page renders without template errors
    proxy.assert_invalid_method2(client.get(ApiProxy.api_url_logout))

    try:
        # logout before login
        proxy.assert_invalid_token2(proxy.logout())

        # normal login
        access_token, refresh_token = proxy.assert_normal_login(
            proxy.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token into proxy
        proxy.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
    finally:
        # normal logout
        proxy.assert_normal_logout(proxy.logout())

    # logout again after logout
    proxy.assert_invalid_token(proxy.logout())


def test_refresh(client, auth):
    proxy = ApiProxy(client)

    # test that viewing the page renders without template errors
    proxy.assert_invalid_method(client.get(ApiProxy.api_url_refresh))

    try:
        # normal login
        access_token, refresh_token = proxy.assert_normal_login(
            proxy.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token into proxy
        proxy.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
        # register user
        new_access_token, new_refresh_token = proxy.assert_normal_refresh(
            proxy.refresh(refresh_token)
        )

        assert new_access_token != access_token and new_refresh_token != refresh_token, \
            'read new access token and refresh token'

        # use the cached access token to logout
        proxy.assert_invalid_token(proxy.logout())

        # refresh cached access token
        proxy.access_token = new_access_token
    finally:
        # normal logout
        proxy.assert_normal_logout(proxy.logout())


def test_register(client, auth):
    proxy = ApiProxy(client)

    # test that viewing the page renders without template errors
    proxy.assert_invalid_method(client.get(ApiProxy.api_url_register))

    try:
        # normal login
        access_token, refresh_token = proxy.assert_normal_login(
            proxy.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token into proxy
        proxy.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
        # TODO : register user
    finally:
        # normal logout
        proxy.assert_normal_logout(proxy.logout())
