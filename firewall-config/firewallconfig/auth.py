"""Functions for authentication"""

import functools

import flask
import requests
import sys

from .errors import *

def test_auth():
    """
    Test auth function
    """
    try:
        return flask.request.headers.get("user", "test_user@example.com")
    except:
        return "test_user@example.com"

def normal_auth(google_oauth_clientID: str) -> str:
    """
    Authenticate using google authentication
    """
    token = flask.request.headers.get("Authorization")[len("Bearer "):] # type: str

    if token is None:
        raise InvalidCredentialsError("No token provided")

    if token.find("=") == -1:
        raise InvalidCredentialsError("Token did not contain an '=' with the token provider")

    token_type = token[:token.find("=")]
    token_content = token[token.find("=")+1:]

    if token_type == "google":
        google_info_request = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {token_content}"
            }
        )

        if google_info_request.status_code != 200:
            raise InvalidCredentialsError()

        if google_info_request.json()["hd"] != "sanger.ac.uk":
             raise InvalidCredentialsError("Google Auth doesn't have an address of sanger.ac.uk")

        return google_info_request.json()["email"]
    elif token_type == "sanger":
        sanger_info_request = requests.get("https://www.sanger.ac.uk/oa2/Info",
            headers={
                "Authorization": f"Bearer {token_content}"
            }
        )

        if sanger_info_request.status_code != 200:
            raise InvalidCredentialsError()

        return sanger_info_request.json()["email"]
    else:
        raise InvalidCredentialsError(f"Unknown token provider {token_type}")
