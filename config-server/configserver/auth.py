"""Functions for authentication"""

import flask
from .errors import *

from google.oauth2 import id_token
from google.auth.transport import requests

def test_auth():
    """
    Test auth function
    """
    try:
        return flask.request.headers.get("user", "test_user@sanger.ac.uk")
    except:
        return "test_user@sanger.ac.uk"

def google_auth(google_oauth_clientID: str):
    """
    Authenticate using google authentication
    """
    token = flask.request.headers.get("Google-Auth-Token")

    if token is None:
        raise InvalidCredentialsError()

    try:
        token_info = id_token.verify_oauth2_token(token, requests.Request(), google_oauth_clientID)
    except ValueError as e:
        raise InvalidCredentialsError() from e

    if token_info["hd"] != "sanger.ac.uk":
        raise InvalidCredentialsError()

    if token_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise InvalidCredentialsError()

    return token_info["email"]