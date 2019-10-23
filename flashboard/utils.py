import os
import sys
import base64
import jwt
import datetime
from string import ascii_lowercase, ascii_uppercase, digits

from flask import current_app, request

PYTHON2 = sys.version_info < (3, 0)


def is_strong(password, min_len=6):
    """ check the strenth of the provided password """
    return len(password) >= min_len and \
        any([upper in password for upper in ascii_uppercase]) and \
        any([lower in password for lower in ascii_lowercase]) and \
        any([digit in password for digit in digits])


def prepare_for_hash(password, public_salt, private_salt):
    """ prepare string for hash """
    return "{}@@{}@@{}".format(password, public_salt, private_salt)


def enbase64(byte_str, altchars=None):
    """
    Encode bytes/strings to base64.
    Args:
        - ``byte_str``:  The string or bytes to base64 encode.
    Returns:
        - byte_str encoded as base64.
    """

    # Python 3: base64.b64encode() expects type byte
    if isinstance(byte_str, str) and not PYTHON2:
        byte_str = bytes(byte_str, 'utf-8')
    return base64.b64encode(byte_str, altchars)


def debase64(byte_str, altchars=None):
    """
    Decode base64 encoded bytes/strings.
    Args:
        - ``byte_str``:  The string or bytes to base64 encode.
    Returns:
        - decoded string as type str for python2 and type byte for python3.
    """
    # Python 3: base64.b64decode() expects type byte
    if isinstance(byte_str, str) and not PYTHON2:
        byte_str = bytes(byte_str, 'utf-8')
    return base64.b64decode(byte_str, altchars)


def generate_random_salt(byte_size=64):
    """
    Generate random salt to use with generate_password_hash().
    Optional Args:
        - ``byte_size``: The length of salt to return. default = 64.
    Returns:
        - str of base64 encoded random bytes.
    """
    return enbase64(os.urandom(byte_size), b'-_').decode('utf-8')


def as_map(dataset, key_name, val_name):
    if dataset is None or len(dataset) <= 0 or key_name is None or val_name is None:
        return None

    result = {}
    for row in dataset:
        if key_name in row and row[key_name] is not None:
            result[row[key_name]] = row[val_name] if val_name in row else None

    return result


def flatten(li):
    """ convert nested list to a flat list """

    return sum(([x] if not isinstance(x, list) else flatten(x) for x in li), [])


def strip_space(data):
    return data.strip() if data else None


def strip_space_lower(data):
    return data.strip().lower() if data else None


def encode_jwt_token(user_id, duration, random_seed=0):
    """ generate JWT token

    The JWT Token's payload contain:
        'uid' (user id),
        'exp' (expiration date of the token),
        'iat' (the time the token is generated),
        'rds' (random seed),
    """

    now = datetime.datetime.utcnow()
    return jwt.encode(
        {
            'uid': user_id,
            'exp': now + datetime.timedelta(seconds=duration),
            'iat': now,
            'rds': random_seed
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS512'
    ).decode('utf-8')


def decode_jwt_token(token):
    """ verify JWT token """

    payload = None
    msg = ''

    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithm='HS512'
        )
    except jwt.ExpiredSignatureError as exp:
        msg = str(exp)
    except (jwt.DecodeError, jwt.InvalidTokenError) as exp:
        msg = str(exp)
    except Exception as exp:
        msg = str(exp)

    return payload, msg


def extract_authorization_from_header():
    """ extract authorization from HTTP header """

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    access_token = auth_header.strip().split(' ')
    if access_token is None or len(access_token) <= 0:
        return None

    return access_token[len(access_token)-1]
