import uuid
import json
import argparse
from urllib.parse import urlparse, urlunparse

import connexion
import flask
from connexion.resolver import Resolver
from google.oauth2 import id_token
from google.auth.transport import requests
from functools import wraps
from flask.testing import FlaskClient
from peewee import CharField, Proxy, Model, SqliteDatabase


def get_route_model(db):
    class Route(Model):
        owner = CharField()
        name = CharField()
        destination = CharField()
        token = CharField()

        def get_json(self):
            return {
                "owner": self.owner,
                "destination": self.destination,
                "token": self.token,
                "name": self.name
            }

        class Meta:
            database = db

    return Route


class InvalidCredentials(Exception):
    pass


class NotAuthorised(Exception):
    pass


class InvalidRouteID(Exception):
    pass


class InvalidURL(Exception):
    pass

# Helper functions

# Intended to be called inside Server


def _auth_and_log_req(func):
    @wraps(func)
    def new_func(self, *args, **kw_args):
        current_user = self._get_current_user()  # includes auth

        self._log_function_call(func.__name__, current_user, args)

        return func(self, *args, **kw_args)

    return new_func


google_oauth_clientID = "859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.self.apps.googleusercontent.com"


class Server:
    def _get_current_user(self):
        token = flask.request.headers.get("Google-Auth-Token")

        if self.debug and token == "test_user":
            return "test_user@sanger.ac.uk"

        if token is None:
            raise InvalidCredentials()

        try:
            token_info = id_token.verify_oauth2_token(token, requests.Request(), google_oauth_clientID)
        except ValueError as ve:
            raise InvalidCredentials() from ve

        if token_info["hd"] != "sanger.ac.uk":
            raise InvalidCredentials()

        if token_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise InvalidCredentials()

        return token_info["email"]

    def _log_function_call(self, name, user, parameters):
        print(f"{user}: {name}({parameters})")

    def _token2route(self, token: str) -> get_route_model(None):
        routes = self.Route.select().where(self.Route.token == token)
        if len(routes) != 1:
            raise InvalidRouteID()
        else:
            return routes[0]

    def _generate_new_token(self):
        return str(uuid.uuid4())

    # Swagger called functions

    @_auth_and_log_req
    def patch_route(self, token, new_info):
        self._token2route(token).update(**new_info).execute()

    @_auth_and_log_req
    def delete_route(self, token):
        try:
            self._token2route(token).delete().execute()
        except InvalidRouteID:
            pass  # DELETE requests are supposed to be idempotent

        return None, 204

    def get_route(self, token):
        return self._token2route(token).get_json()

    @_auth_and_log_req
    def get_all_routes(self):
        routes = self.Route.select().where(self.Route.owner == self._get_current_user())

        return [route.get_json() for route in routes]

    @_auth_and_log_req
    def add_route(self, new_route):
        try:
            url_ob = urlparse(new_route["destination"])
            if url_ob.scheme == '':
                destination = "http://" + new_route["destination"]
            else:
                destination = new_route["destination"]
        except SyntaxError:
            raise InvalidURL()

        route = self.Route(
            owner=self._get_current_user(),
            destination=destination,
            name=new_route["name"],
            token=self._generate_new_token())

        route.save()

        return route.get_json(), 201

    def close(self):
        self.db.close()

    def resolve_name(self, name):
        return getattr(self, name)

    def _set_error_handler(self, error_class, error_message, error_code):
        def handler(error):
            return flask.make_response(flask.jsonify({'error': error_message}), error_code)
        self.app.add_error_handler(error_class, handler)

    def __init__(self, debug, memory_db):
        if memory_db:
            self.db = SqliteDatabase(':memory:')
        else:
            self.db = SqliteDatabase('db.db')

        self.debug = debug
        self.db.connect()
        self.Route = get_route_model(self.db)
        self.db.create_tables([self.Route], True)
        self.app = connexion.FlaskApp(__name__, specification_dir=".", debug=debug)

        self._set_error_handler(InvalidRouteID, "Invalid route ID", 404)
        self._set_error_handler(NotAuthorised, "Not Authorised", 403)
        self._set_error_handler(InvalidURL, "Invalid URL in destination", 400)
        self._set_error_handler(InvalidCredentials, "Invalid credentials", 403)

        self.app.add_api('swagger.yaml', resolver=Resolver(self.resolve_name), validate_responses=debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generates CWL files from the GATK documentation')
    parser.add_argument("--debug", help="Enable debugging mode", action="store_true")
    parser.add_argument("--port", help="Port to serve requests over", type=int, default=8081)
    parser.add_argument("--host", help="Host to serve requests from", default="127.0.0.1")

    options = parser.parse_args()

    server = Server(options.debug, False)
    server.app.run(port=options.port, host=options.host)
