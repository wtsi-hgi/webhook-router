from abc import ABC, ABCMeta
import logging
import secrets
import uuid

from .models import Route, get_route_json
from .errors import *
from .UserLinkDataMapper import UserLinkDataMapper
from pythonjsonlogger import jsonlogger
import connexion
import flask
from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist, BooleanField

class RouteDataMapper:
    """
    Data mapper for the Route type.
    NOTE: This may be called by ConnextionDespatcher, so naming of arguments is important
    """
    def __init__(self, user_link_datamapper: UserLinkDataMapper):
        self._user_link_datamapper = user_link_datamapper

    def _get_route_from_uuid(self, uuid: str) -> Route:
        try:
            return Route.get(Route.uuid == uuid)
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
        routes = Route.select().where(Route.token == token)

        if len(routes) != 1:
            raise InvalidRouteTokenError()
        else:
            return get_route_json(routes[0])

    def add(self, user: str, destination: str, name: str, no_ssl_verification: bool):
        route_uuid = str(uuid.uuid4())

        route = Route(
            destination=destination,
            name=name,
            no_ssl_verification=no_ssl_verification,
            uuid=route_uuid,
            token=RouteDataMapper._generate_new_token())

        self._user_link_datamapper.add_user_link(user, route_uuid)

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
