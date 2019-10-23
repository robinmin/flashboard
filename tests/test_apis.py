import pytest

from .conftest import post_json, json_of_response


class ApiProxy(object):
    api_url_login = '/api/user/login'
    api_url_logout = '/api/user/logout'
    api_url_refresh = '/api/user/refresh'

    def __init__(self, client):
        self._client = client
        self.access_token = None

    def login(self, email, password):
        return post_json(self._client, self.api_url_login, {
            'email': 'luonbin@hotmail.com',
            'password': 'Test001'
        })

    def logout(self):
        return self._client.get(self.api_url_logout, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token}
        )

    def refresh(self, refresh_token):
        return post_json(self._client, self.api_url_refresh, {
            'refresh_token': refresh_token
        })


def test_login(client, auth):
    # test that viewing the page renders without template errors
    resp = client.get(ApiProxy.api_url_login)
    assert resp.status_code == 405

    json_resp = resp.get_json()
    assert json_resp and 'message' in json_resp \
        and json_resp['message'] == 'The method is not allowed for the requested URL.', \
        'Invalid HTTP method on ' + ApiProxy.api_url_login

    proxy = ApiProxy(client)

    # normal login
    resp = proxy.login('luonbin@hotmail.com', 'Test001')
    assert resp.status_code == 200

    json_resp = resp.get_json()
    assert json_resp and 'access_token' in json_resp and 'refresh_token' in json_resp \
        and json_resp['access_token'] and json_resp['refresh_token'], \
        'normal login on ' + ApiProxy.api_url_login


def test_loout(client, auth):
    # test that viewing the page renders without template errors
    resp = client.post(ApiProxy.api_url_logout)
    assert resp.status_code == 405

    proxy = ApiProxy(client)

    # normal login
    resp = proxy.login('luonbin@hotmail.com', 'Test001')
    assert resp.status_code == 200

    json_resp = resp.get_json()
    assert json_resp and 'access_token' in json_resp and 'refresh_token' in json_resp \
        and json_resp['access_token'] and json_resp['refresh_token'], \
        'normal login on ' + ApiProxy.api_url_login

    # cache access token into proxy
    proxy.access_token = json_resp['access_token']

    # normal logout
    resp = proxy.logout()
    assert resp.status_code == 200

    json_resp = resp.get_json()
    assert json_resp and 'message' in json_resp and json_resp['message'] == 'OK', \
        'normal logout on ' + ApiProxy.api_url_login

    # logout again
    resp = proxy.logout()
    assert resp.status_code == 403

    json_resp = resp.get_json()
    assert json_resp and 'message' in json_resp and json_resp['message'] == 'Valid API Token required (Invalid or expired token)', \
        'logout again on ' + ApiProxy.api_url_login


def test_refresh(client, auth):
    # test that viewing the page renders without template errors
    resp = client.get(ApiProxy.api_url_refresh)
    assert resp.status_code == 405

    proxy = ApiProxy(client)

    # normal login
    resp = proxy.login('luonbin@hotmail.com', 'Test001')
    assert resp.status_code == 200

    json_resp = resp.get_json()
    assert json_resp and 'access_token' in json_resp and 'refresh_token' in json_resp \
        and json_resp['access_token'] and json_resp['refresh_token'], \
        'normal login on ' + ApiProxy.api_url_login

    # cache access token into proxy
    access_token = json_resp['access_token']
    refresh_token = json_resp['refresh_token']
    proxy.access_token = access_token

    # refresh token
    resp = proxy.refresh(refresh_token)
    assert resp.status_code == 200

    json_resp = resp.get_json()
    assert json_resp and 'access_token' in json_resp and 'refresh_token' in json_resp \
        and json_resp['access_token'] and json_resp['refresh_token'], \
        'normal refresh token on ' + ApiProxy.api_url_refresh

    new_access_token = json_resp['access_token']
    new_refresh_token = json_resp['refresh_token']
    assert new_access_token != access_token and new_refresh_token != refresh_token, \
        'read new access token and refresh token'

    # refresh cached access token
    proxy.access_token = new_access_token

    # normal logout
    resp = proxy.logout()
    assert resp.status_code == 200

    json_resp = resp.get_json()
    assert json_resp and 'message' in json_resp and json_resp['message'] == 'OK', \
        'normal logout on ' + ApiProxy.api_url_login
