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
    destination = CharField()
    write_users = CharField() # Store as a json list for now
    token = CharField()

    def get_json(self):
        return {
            "owner": self.owner,
            "destination": self.destination,
            "write_users": json.loads(self.write_users),
            "token": self.token
        }

    class Meta:
        database = db

class AuthException(Exception):
    pass

class InvalidRouteID(Exception):
    pass

# Helper functions

def get_current_user():
    userId = flask.request.headers.get("userId")
    if userId is None:
        raise AuthException()

    return userId

def token2route(token: str) -> Route:
    routes = Route.select().where(Route.token == token)
    if len(routes) != 1:
        raise InvalidRouteID()
    else:
        return routes[0]

def generate_new_token():
    return str(uuid.uuid4())

# Swagger called functions

def patch_route(token, new_info):
    token2route(token).update(**new_info).execute()

def delete_route(token):
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
        raise Exception("Invalid URL")

    route = Route(
        owner=get_current_user(),
        destination=destination,
        write_users=json.dumps(new_route["write_users"]),
        token=generate_new_token())

    route.save()

    return route.get_json()

def resolveSwaggerName(name):
    return globals()[name]

db.create_tables([Route], True)
# TODO connect to the database on request sent
app = connexion.FlaskApp(__name__, specification_dir=".")
app.add_api('swagger.yaml', resolver=Resolver(resolveSwaggerName))
app.run(port=8081, host="127.0.0.1")

@app.errorhandler(InvalidRouteID)
def handle_invalid_routeID():
    return flask.make_response(flask.jsonify({'error': 'Invalid route ID'}), 404)

@app.errorhandler(AuthException)
def handle_auth_exception():
    return flask.make_response(flask.jsonify({'error': 'Invalid credentials'}), 403)