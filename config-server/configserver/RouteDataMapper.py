import logging
import secrets
import uuid

from peewee import DoesNotExist

from .models import Route, get_route_json
from .UserLinkDataMapper import UserLinkDataMapper
from .errors import *

logger = logging.getLogger("config_server.route_data_mapper")

TOKEN_ID_LENGTH = 10

class RouteDataMapper:
    """
    Data mapper for the Route type.
    NOTE: This may be called by ConnextionDespatcher, so naming of arguments is important.
    NOTE: user_link_datamapper property needs to be instantiated before this class can be used
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
        """
        _generate_new_token: Generates a token with a tokenId at the front.
        The tokenId is used to for database lookups
        """
        token_id = secrets.token_urlsafe()[:TOKEN_ID_LENGTH]
        token = token_id + secrets.token_urlsafe()

        return token, token_id

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
        token_id = token[:TOKEN_ID_LENGTH]
        routes = Route.select().where(Route.token_id == token_id)

        if len(routes) != 1:
            raise InvalidRouteTokenError()
        else:
            if secrets.compare_digest(routes[0].token, token):
                return get_route_json(routes[0])
            else:
                raise InvalidRouteTokenError()

    def add(self, user: str, **kwargs):
        route_uuid = str(uuid.uuid4())
        token, token_id = RouteDataMapper._generate_new_token()

        route = Route(
            **kwargs,
            uuid=route_uuid,
            token=token,
            token_id=token_id)

        route.save()

        self._user_link_datamapper.add_user_link(user, route_uuid)

        return get_route_json(route)

    def regenerate_token(self, uuid: str):
        route = self._get_route_from_uuid(uuid)
        new_token, new_token_id = RouteDataMapper._generate_new_token()
        route.token = new_token
        route.token_id = new_token_id
        route.save()

        return {
            **get_route_json(route),
            "token": new_token
        }