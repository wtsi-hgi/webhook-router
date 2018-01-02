"""Functions for authentication"""

import functools

import flask
from google.auth.transport import requests
from google.oauth2 import id_token

from .errors import *


def test_auth():
    """
    Test auth function
    """
    try:
        return flask.request.headers.get("user", "test_user@example.com")
    except:
        return "test_user@example.com"

def google_auth(google_oauth_clientID: str):
    """
    Authenticate using google authentication
    """
    token = flask.request.headers.get("Google-Auth-Token")

    if token is None:
        raise InvalidCredentialsError()

    try:
        req_timeout = functools.partial(requests.Request(), timeout=3)
        token_info = id_token.verify_oauth2_token(token, req_timeout, google_oauth_clientID)
    except ValueError as e:
        raise InvalidCredentialsError() from e

    if token_info["hd"] != "sanger.ac.uk":
        raise InvalidCredentialsError()

    if token_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise InvalidCredentialsError()

    return token_info["email"]
