import uuid
import secrets
import argparse
from urllib.parse import urlparse
from functools import partial
from abc import ABC, ABCMeta

import connexion
import flask
from google.oauth2 import id_token
from google.auth.transport import requests
from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist
from playhouse.shortcuts import model_to_dict
from typing import Type, Callable
from flask_cors import CORS

class AbstractBaseRoute(Model):
    uuid = CharField()
    owner = CharField()
    name = CharField()
    destination = CharField()
    token = CharField()

def get_route_model(db: Database):
    """
    Gets the Route model for a given database (works around peewee's irregularities)
    """
    class Route(AbstractBaseRoute):
        class Meta:
            database = db

    return Route

def get_route_json(route: AbstractBaseRoute):
    """
    Gets the json respresentation of given route, for returning to the user
    """
    return model_to_dict(route)

class StatusCodes:
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404

# User generated errors

class InvalidCredentialsError(Exception):
    pass


class NotAuthorisedError(Exception):
    pass


class InvalidRouteUUIDError(Exception):
    pass


class InvalidURLError(Exception):
    pass

class InvalidRouteTokenError(Exception):
    pass


def test_auth():
    """
    Test auth function
    """
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

class RouterDataMapper:
    """
    Data mapper for the Route type
    """
    def __init__(self, Route: Type[AbstractBaseRoute]):
        self._Route = Route

    def _get_route_from_uuid(self, uuid: str) -> AbstractBaseRoute:
        try:
            return self._Route.get(self._Route.uuid == uuid)
        except DoesNotExist as e:
            raise InvalidRouteUUIDError() from e
    
    @staticmethod
    def _generate_new_token():
        return str(secrets.token_urlsafe())

    def update(self, uuid: str, new_info: object):
        route = self._get_route_from_uuid(uuid)
        for key in new_info:
            setattr(route, key, new_info[key])

        route.save()

    def delete(self, uuid: str):
        route = self._get_route_from_uuid(uuid)
        route.delete_instance()

    def get(self, uuid: str):
        return self._get_route_from_uuid(uuid)

    def get_by_token(self, token: str):
        # TODO look at timing attacks here
        routes = self._Route.select().where(self._Route.token == token)

        if len(routes) != 1:
            raise InvalidRouteTokenError()
        else:
            return routes[0]

    def get_all(self, user: str):
        return self._Route.select().where(self._Route.owner == user)

    def add(self, owner: str, destination: str, name: str):
        route = self._Route(
            owner=owner,
            destination=destination,
            name=name,
            uuid=str(uuid.uuid4()),
            token=RouterDataMapper._generate_new_token())

        route.save()

        return route

    def regenerate_token(self, uuid: str):
        route = self._get_route_from_uuid(uuid)
        new_token = RouterDataMapper._generate_new_token()
        route.token = new_token
        route.save()

        return {
            **get_route_json(route),
            "token": new_token
        }

class Server:
    """
    Main class for serving requests
    """
    def __init__(self, debug: bool, db: Database, auth: Callable[[], str]):
        self._db = db
        self._auth = auth
        self._db.connect()
        Route = get_route_model(self._db)
        self._data_mapper = RouterDataMapper(Route)
        self._db.create_tables([Route], True)
        self.app = connexion.FlaskApp(__name__, specification_dir=".", debug=debug)
        CORS(self.app.app)

        self._set_error_handlers()

        self.app.add_api('swagger.yaml', resolver=connexion.Resolver(self._resolve_name), validate_responses=True)
    
    def _resolve_name(self, name: str):
        """
        From a swagger operationId, returns the correct class
        """
        return getattr(self, name)

    def _set_error_handler(self, error_class: Type[Exception], error_message: str, error_code: int):
        """
        For a given Error class, sets response that would be returned
        """
        def handler(error):
            return flask.make_response(flask.jsonify({'error': error_message}), error_code)
        self.app.add_error_handler(error_class, handler)

    def _set_error_handlers(self):
        self._set_error_handler(InvalidRouteUUIDError, "Invalid route UUID", StatusCodes.NOT_FOUND)
        self._set_error_handler(InvalidRouteTokenError, "Invalid route token", StatusCodes.NOT_FOUND)
        self._set_error_handler(NotAuthorisedError, "Not Authorised", StatusCodes.FORBIDDEN)
        self._set_error_handler(InvalidURLError, "Invalid URL in destination", StatusCodes.BAD_REQUEST)
        self._set_error_handler(InvalidCredentialsError, "Invalid credentials", StatusCodes.BAD_REQUEST)

    def close(self):
        self._db.close()

    def patch_route(self, uuid: str, new_info: object):
        self._auth()
        self._data_mapper.update(uuid, new_info)

        return None, StatusCodes.NO_CONTENT

    def get_by_token(self, token: str):
        return get_route_json(self._data_mapper.get_by_token(token))

    def delete_route(self, uuid: str):
        self._auth()

        try:
            self._data_mapper.delete(uuid)
        except InvalidRouteUUIDError:
            pass  # DELETE requests are supposed to be idempotent

        return None, StatusCodes.NO_CONTENT

    def get_route(self, uuid: str):
        return get_route_json(self._data_mapper.get(uuid))

    def get_all_routes(self):
        user_email = self._auth()
        routes = self._data_mapper.get_all(user_email)

        return [get_route_json(route) for route in routes]

    def add_route(self, new_route: object):
        user = self._auth()

        try:
            url_ob = urlparse(new_route["destination"])
        except SyntaxError:
            raise InvalidURLError()
        if url_ob.scheme == '':
            destination = "http://" + new_route["destination"]
        else:
            destination = new_route["destination"]

        route = self._data_mapper.add(
            owner=user,
            destination=destination,
            name=new_route["name"])

        return get_route_json(route), StatusCodes.CREATED

    def regenerate_token(self, uuid: str):
        self._auth()

        return self._data_mapper.regenerate_token(uuid)


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
