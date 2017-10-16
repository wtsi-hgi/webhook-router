import uuid
import argparse
from urllib.parse import urlparse
from functools import wraps

import connexion
import flask
from google.oauth2 import id_token
from google.auth.transport import requests
from peewee import CharField, Model, SqliteDatabase
from playhouse.shortcuts import model_to_dict
from typing import TypeVar

"""
Gets the Route model for a given database (works around peewee's irregularities)
"""
def get_route_model(db):
    class Route(Model):
        owner = CharField()
        name = CharField()
        destination = CharField()
        token = CharField()

        class Meta:
            database = db

    return Route

# Generate a Route type
def _helper() -> get_route_model:
    return None

Route = _helper()

"""
Gets the json respresentation of given route, for returning to the user
"""
def get_route_json(route: Route):
    return model_to_dict(route)

class InvalidCredentials(Exception):
    pass


class NotAuthorised(Exception):
    pass


class InvalidRouteID(Exception):
    pass


class InvalidURL(Exception):
    pass

class TestAuth:
    def get_user(self):
        return "test_user@sanger.ac.uk"

google_oauth_clientID = "859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.self.apps.googleusercontent.com"

class Auth:
    def get_user(self):
        token = flask.request.headers.get("Google-Auth-Token")

        if token is None:
            raise InvalidCredentials()

        try:
            token_info = id_token.verify_oauth2_token(token, requests.Request(), google_oauth_clientID)
        except ValueError as e:
            raise InvalidCredentials() from e

        if token_info["hd"] != "sanger.ac.uk":
            raise InvalidCredentials()

        if token_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise InvalidCredentials()

        return token_info["email"]

class Server:
    def _auth_request(func):
        @wraps(func)
        def new_func(self, *args, **kw_args):
            current_user = self.auth.get_user()  # includes auth

            self._log_function_call(func.__name__, current_user, args)

            return func(self, *args, **kw_args)

        return new_func

    def _log_function_call(self, name, user, parameters):
        # TODO
        pass

    def _token2route(self, token: str) -> get_route_model(None):
        routes = self.Route.select().where(self.Route.token == token)
        if len(routes) != 1:
            raise InvalidRouteID()
        else:
            return routes[0]

    def _generate_new_token(self):
        return str(uuid.uuid4())

    # Swagger called functions

    @_auth_request
    def patch_route(self, token, new_info):
        self._token2route(token).update(**new_info).execute()

        return None, 204

    @_auth_request
    def delete_route(self, token):
        try:
            self._token2route(token).delete().execute()
        except InvalidRouteID:
            pass  # DELETE requests are supposed to be idempotent

        return None, 204

    def get_route(self, token):
        return get_route_json(self._token2route(token))

    @_auth_request
    def get_all_routes(self):
        routes = self.Route.select().where(self.Route.owner == self.auth.get_user())

        return [get_route_json(route) for route in routes]

    @_auth_request
    def add_route(self, new_route):
        try:
            url_ob = urlparse(new_route["destination"])
        except SyntaxError:
            raise InvalidURL()
        if url_ob.scheme == '':
            destination = "http://" + new_route["destination"]
        else:
            destination = new_route["destination"]

        route = self.Route(
            owner=self.auth.get_user(),
            destination=destination,
            name=new_route["name"],
            token=self._generate_new_token())

        route.save()

        return get_route_json(route), 201

    @_auth_request
    def regenerate_token(self, token):
        route = self._token2route(token)
        new_token = self._generate_new_token()
        route.update(token=new_token).execute()

        return {
            **get_route_json(route),
            "token": new_token
        }

    def close(self):
        self.db.close()

    def resolve_name(self, name):
        return getattr(self, name)

    def _set_error_handler(self, error_class, error_message, error_code):
        def handler(error):
            return flask.make_response(flask.jsonify({'error': error_message}), error_code)
        self.app.add_error_handler(error_class, handler)

    def __init__(self, debug, db, auth):
        self.db = db
        self.auth = auth
        self.db.connect()
        self.Route = get_route_model(self.db)
        self.db.create_tables([self.Route], True)
        self.app = connexion.FlaskApp(__name__, specification_dir=".", debug=debug)

        self._set_error_handler(InvalidRouteID, "Invalid route ID", 404)
        self._set_error_handler(NotAuthorised, "Not Authorised", 403)
        self._set_error_handler(InvalidURL, "Invalid URL in destination", 400)
        self._set_error_handler(InvalidCredentials, "Invalid credentials", 403)

        self.app.add_api('swagger.yaml', resolver=connexion.Resolver(self.resolve_name), validate_responses=True)


def main(debug, port, host):
    server = Server(
        debug=debug,
        db=SqliteDatabase('db.db'),
        auth=TestAuth() if options.debug else Auth()
    )

    server.app.run(port=port, host=host)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generates CWL files from the GATK documentation')
    parser.add_argument("--debug", help="Enable debugging mode", action="store_true")
    parser.add_argument("--port", help="Port to serve requests over", type=int, default=8081)
    parser.add_argument("--host", help="Host to serve requests from", default="127.0.0.1")

    options = parser.parse_args()

    main(options.debug, options.port, options.host)
