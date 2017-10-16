import uuid
import argparse
from urllib.parse import urlparse
from functools import wraps, partial

import connexion
import flask
from flask.ext.api import status
from google.oauth2 import id_token
from google.auth.transport import requests
from peewee import CharField, Model, SqliteDatabase, Database
from playhouse.shortcuts import model_to_dict
from typing import TypeVar

"""
Gets the Route model for a given database (works around peewee's irregularities)
"""
def get_route_model(db: Database):
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

class StatusCodes:
    CREATED = 201
    NO_CONTENT = 205
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404


"""
Gets the json respresentation of given route, for returning to the user
"""
def get_route_json(route: Route):
    return model_to_dict(route)

class InvalidCredentialsError(Exception):
    pass


class NotAuthorisedError(Exception):
    pass


class InvalidRouteIDError(Exception):
    pass


class InvalidURLError(Exception):
    pass

"""
Test auth function
"""
def test_auth():
    return "test_user@sanger.ac.uk"

"""
Authenticate using google authentication
"""
def google_auth(google_oauth_clientID):
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

class RouterDataMapper:
    def __init__(self, Route: get_route_model):
        self.Route = Route

    def _get_route_from_token(self, token: str) -> Route:
        routes = self.Route.select().where(self.Route.token == token)
        if len(routes) != 1:
            raise InvalidRouteIDError()
        else:
            return routes[0]
    
    def _generate_new_token(self):
        return str(uuid.uuid4())

    def update(self, token, new_info):
        self._get_route_from_token(token).update(**new_info).execute()

    def delete(self, token):
        self._get_route_from_token(token).delete().execute()

    def get(self, token):
        return self._get_route_from_token(token)

    def get_all(self, user):
        return self.Route.select().where(self.Route.owner == user)

    def add(self, owner, destination, name):
        route = self.Route(
            owner=owner,
            destination=destination,
            name=name,
            token=self._generate_new_token())

        route.save()

        return route

    def regenerate_token(self, token):
        route = self._get_route_from_token(token)
        new_token = self._generate_new_token()
        route.update(token=new_token).execute()

        return {
            **get_route_json(route),
            "token": new_token
        }

class Server:
    def patch_route(self, token, new_info):
        self.auth()
        self.data_mapper.update(token, new_info)

        return None, StatusCodes.NO_CONTENT

    def delete_route(self, token):
        self.auth()

        try:
            self.data_mapper.delete(token)
        except InvalidRouteIDError:
            pass  # DELETE requests are supposed to be idempotent

        return None, StatusCodes.NO_CONTENT

    def get_route(self, token):
        return get_route_json(self.data_mapper.get(token))

    def get_all_routes(self):
        user_email = self.auth()
        routes = self.data_mapper.get_all(user_email)

        return [get_route_json(route) for route in routes]

    def add_route(self, new_route):
        user = self.auth()

        try:
            url_ob = urlparse(new_route["destination"])
        except SyntaxError:
            raise InvalidURLError()
        if url_ob.scheme == '':
            destination = "http://" + new_route["destination"]
        else:
            destination = new_route["destination"]

        route = self.data_mapper.add(
            owner=user,
            destination=destination,
            name=new_route["name"])

        return get_route_json(route), StatusCodes.CREATED

    def regenerate_token(self, token):
        self.auth()

        return self.data_mapper.regenerate_token(token)

    def close(self):
        self.db.close()

    def resolve_name(self, name):
        return getattr(self, name)

    def _set_error_handler(self, error_class, error_message, error_code):
        def handler(error):
            return flask.make_response(flask.jsonify({'error': error_message}), error_code)
        self.app.add_error_handler(error_class, handler)

    def _set_error_handlers(self):
        self._set_error_handler(InvalidRouteIDError, "Invalid route ID", StatusCodes.NOT_FOUND)
        self._set_error_handler(NotAuthorisedError, "Not Authorised", StatusCodes.FORBIDDEN)
        self._set_error_handler(InvalidURLError, "Invalid URL in destination", StatusCodes.BAD_REQUEST)
        self._set_error_handler(InvalidCredentialsError, "Invalid credentials", StatusCodes.BAD_REQUEST)

    def __init__(self, debug, db, auth):
        self.db = db
        self.auth = auth
        self.db.connect()
        Route = get_route_model(self.db)
        self.data_mapper = RouterDataMapper(Route)
        self.db.create_tables([Route], True)
        self.app = connexion.FlaskApp(__name__, specification_dir=".", debug=debug)

        self._set_error_handlers()

        self.app.add_api('swagger.yaml', resolver=connexion.Resolver(self._resolve_name), validate_responses=True)


def main(debug: bool, port: int, host: str, client_id: str=None):
    if not debug and not client_id:
        raise TypeError("server: main(...) - debug=False requires client_id to have a value")
    server = Server(
        debug=debug,
        db=SqliteDatabase('db.db'),
        auth=test_auth if debug else partial(google_auth, client_id)
    )

    server.app.run(port=port, host=host)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generates CWL files from the GATK documentation')
    parser.add_argument("--debug", help="Enable debugging mode", action="store_true")
    parser.add_argument("--port", help="Port to serve requests over", type=int, default=8081)
    parser.add_argument("--host", help="Host to serve requests from", default="127.0.0.1")
    parser.add_argument("--client_id", help="Google client ID for oauth authentication", default="127.0.0.1")

    options = parser.parse_args()

    main(options.debug, options.port, options.host)
