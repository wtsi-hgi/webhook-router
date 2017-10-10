import connexion
import flask
import uuid
from urllib.parse import urlparse, urlunparse
from connexion.resolver import Resolver
import json

from peewee import *

db = SqliteDatabase('db.db')

class Route(Model):
    owner = CharField()
    name = CharField()
    destination = CharField()
    write_users = CharField() # Store as a json list for now
    token = CharField()

    def get_json(self):
        return {
            "owner": self.owner,
            "destination": self.destination,
            "write_users": json.loads(self.write_users),
            "token": self.token,
            "name": self.name
        }

    class Meta:
        database = db

class InvalidCredentials(Exception):
    pass

class NotAuthorised(Exception):
    pass

class InvalidRouteID(Exception):
    pass

class InvalidURL(Exception):
    pass

# Helper functions

def get_current_user():
    # TODO do this using proper authentication
    userId = flask.request.headers.get("userId")
    if userId is None:
        raise InvalidCredentials()

    return userId

def token2route(token: str) -> Route:
    routes = Route.select().where(Route.token == token)
    if len(routes) != 1:
        raise InvalidRouteID()
    else:
        return routes[0]

def generate_new_token():
    return str(uuid.uuid4())

def has_write_permission(token):
    route = token2route(token)
    current_user = get_current_user()

    return current_user in route.write_users

# Swagger called functions

def patch_route(token, new_info):
    if not has_write_permission(token):
        raise InvalidCredentials()

    token2route(token).update(**new_info).execute()

def delete_route(token):
    if not has_write_permission(token):
        raise InvalidCredentials()

    try:
        token2route(token).delete().execute()
    except InvalidRouteID:
        pass # DELETE requests are supposed to be idempotent

def get_route(token):
    return token2route(token).get_json()

def get_all_routes():
    routes = Route.select().where(Route.owner == get_current_user())

    return [route.get_json() for route in routes]

def add_route(new_route):
    try:
        url_ob = urlparse(new_route["destination"])
        if url_ob.scheme == '':
            destination = "http://" + new_route["destination"]
        else:
            destination = new_route["destination"]
    except SyntaxError:
        raise InvalidURL()

    route = Route(
        owner=get_current_user(),
        destination=destination,
        write_users=json.dumps(new_route["write_users"]),
        name=new_route["name"],
        token=generate_new_token())

    route.save()

    return route.get_json()

def resolveSwaggerName(name):
    return globals()[name]

db.connect()
db.create_tables([Route], True)
app = connexion.FlaskApp(__name__, specification_dir=".")

def handle_invalid_routeID(e):
    return flask.make_response(flask.jsonify({'error': 'Invalid route ID'}), 404)
app.add_error_handler(InvalidRouteID, handle_invalid_routeID)

def handle_not_authorised(e):
    return flask.make_response(flask.jsonify({'error': 'Not Authorised'}), 404)
app.add_error_handler(NotAuthorised, handle_not_authorised)

def handle_invalid_URL(e):
    return flask.make_response(flask.jsonify({'error': 'Invalid URL in destination'}), 404)
app.add_error_handler(InvalidURL, handle_invalid_URL)

def handle_invalid_credentials(e):
    return flask.make_response(flask.jsonify({'error': 'Invalid credentials'}), 403)
app.add_error_handler(InvalidCredentials, handle_invalid_credentials)

app.add_api('swagger.yaml', resolver=Resolver(resolveSwaggerName))
app.run(port=8081, host="127.0.0.1")