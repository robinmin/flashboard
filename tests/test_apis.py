import pytest

from flashboard.models import UserModel, RolesUsers
from .conftest import post_json, json_of_response


def test_login(client, api):
    # test that viewing the page renders without template errors
    api.assert_invalid_method(client.get(api.api_url_login))

    try:
        # normal login
        access_token, refresh_token = api.assert_normal_login(
            api.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token
        api.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
        # login after login
        new_access_token, new_refresh_token = api.assert_normal_login(
            api.login('luonbin@hotmail.com', 'Test001')
        )

        # logout with the old access token
        api.assert_invalid_token(api.logout())

        # update access token
        api.access_token = new_access_token
    finally:
        # normal logout
        api.assert_normal_logout(api.logout())


def test_logout(client, api):
    # test that viewing the page renders without template errors
    api.assert_invalid_method2(client.get(api.api_url_logout))

    try:
        # logout before login
        api.assert_invalid_token2(api.logout())

        # normal login
        access_token, refresh_token = api.assert_normal_login(
            api.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token
        api.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
    finally:
        # normal logout
        api.assert_normal_logout(api.logout())

    # logout again after logout
    api.assert_invalid_token(api.logout())


def test_refresh(client, api):
    # test that viewing the page renders without template errors
    api.assert_invalid_method(client.get(api.api_url_refresh))

    try:
        # normal login
        access_token, refresh_token = api.assert_normal_login(
            api.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token
        api.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
        # register user
        new_access_token, new_refresh_token = api.assert_normal_refresh(
            api.refresh(refresh_token)
        )

        assert new_access_token != access_token and new_refresh_token != refresh_token, \
            'read new access token and refresh token'

        # use the cached access token to logout
        api.assert_invalid_token(api.logout())

        # refresh cached access token
        api.access_token = new_access_token
    finally:
        # normal logout
        api.assert_normal_logout(api.logout())


def test_register(client, api):
    # test that viewing the page renders without template errors
    api.assert_invalid_method(client.get(api.api_url_register))

    try:
        # normal login
        access_token, refresh_token = api.assert_normal_login(
            api.login('luonbin@hotmail.com', 'Test001')
        )

        # cache access token
        api.access_token = access_token

        ###########################################
        #
        # Core test cases start from here
        #
        ###########################################
        # TODO : register user
        count_user = UserModel.query.count()
        count_ru = RolesUsers.query.count()

    finally:
        # normal logout
        api.assert_normal_logout(api.logout())
