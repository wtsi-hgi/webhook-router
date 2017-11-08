from abc import ABC, ABCMeta
import logging
import secrets
import uuid

from .errors import *
from pythonjsonlogger import jsonlogger
import connexion
import flask
from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist, BooleanField

class AbstractBaseRoute(Model):
    uuid = CharField()
    owner = CharField()
    name = CharField()
    destination = CharField()
    no_ssl_verification = BooleanField()
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
    public_fields = ["uuid", "owner", "name", "destination", "token", "no_ssl_verification"] # i.e. not id
    new_ob = {}

    for field in public_fields:
        new_ob[field] = getattr(route, field)

    return new_ob

class RouteDataMapper:
    """
    Data mapper for the Route type.
    NOTE: This may be called by ConnextionDespatcher, so naming of arguments is important
    """
    def __init__(self, db: Database):
        self._Route = get_route_model(db)
        db.create_tables([self._Route], True)

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
        try:
            route = self._get_route_from_uuid(uuid)
        except InvalidRouteUUIDError:
            pass # Make this idempotent
        else:
            route.delete_instance()

    def get(self, uuid: str):
        return get_route_json(self._get_route_from_uuid(uuid))

    def get_by_token(self, token: str):
        # TODO look at timing attacks here
        routes = self._Route.select().where(self._Route.token == token)

        if len(routes) != 1:
            raise InvalidRouteTokenError()
        else:
            return get_route_json(routes[0])

    def get_all(self, user: str):
        routes = self._Route.select().where(self._Route.owner == user)

        return [get_route_json(route) for route in routes]

    def add(self, owner: str, destination: str, name: str, no_ssl_verification: bool):
        route = self._Route(
            owner=owner,
            destination=destination,
            name=name,
            no_ssl_verification=no_ssl_verification,
            uuid=str(uuid.uuid4()),
            token=RouteDataMapper._generate_new_token())

        route.save()

        return get_route_json(route)

    def regenerate_token(self, uuid: str):
        route = self._get_route_from_uuid(uuid)
        new_token = RouteDataMapper._generate_new_token()
        route.token = new_token
        route.save()

        return {
            **get_route_json(route),
            "token": new_token
        }
