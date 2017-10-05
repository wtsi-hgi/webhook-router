import connexion
import flask
import requests
import uuid
import urlparse

from peewee import *

db = SqliteDatabase('db.db')

class Route(Model):
    owner = CharField()
    destination = CharField()
    write_users = CharField()
    token = CharField()

    def get_json(self):
        return {
            "owner": self.owner,
            "destination": self.destination,
            "write_users": self.write_users,
            "token": self.token
        }

    class Meta:
        database = db

class AuthException(Exception):
    pass

def get_current_user():
    userId = flask.request.headers.get("userId")
    if userId is None:
        raise AuthException()

    return userId

def route_webhook(token):
    route = Route.select().where(Route.token == token)
    if route is None:
        return {
            "error": "Invalid route"
        }
    else:
        route = route[0]

    print(f"Routing request to '{route.destination}'")

    # TODO think about what to do if the destination is invalid
    requests.post(route.destination,
        headers=flask.request.headers,
        data=flask.request.data)
    

def get_all_routes():
    routes = Route.select().where(Route.owner == get_current_user())

    return [route.get_json() for route in routes]

def generate_new_token():
    return str(uuid.uuid4())

def add_route(new_route):
    try:
        url_ob = urlparse(new_route["destination"])
    except SyntaxError:
        raise Exception("Invalid URL")

    if url_ob.scheme == '':
        url_ob.scheme = "http"

    route = Route(
        owner=get_current_user(),
        destination=urlparse.urlunparse(url_ob),
        write_users=new_route["write_users"],
        token=generate_new_token())

    route.save()

    return route.get_json()

app = connexion.FlaskApp(__name__, specification_dir=".")
app.add_api('swagger.yaml')
app.run(port=8080, host="127.0.0.1")