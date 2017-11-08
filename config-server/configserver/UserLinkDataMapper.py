from abc import ABC, ABCMeta
import logging
from .errors import *
from .models import UserLink, Route, get_route_json

from pythonjsonlogger import jsonlogger
import connexion
import flask
from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist, ForeignKeyField

class UserLinkDataMapper:
    """
    Data mapper for the UserLink type.
    NOTE: This may be called by ConnextionDespatcher, so naming of arguments is important
    """
    def __init__(self):
        self.route_datamapper = None # type: RouteDataMapper

    def _try_get_link(self, user: str, uuid: str):
        return UserLink.get((UserLink.route == uuid) & (UserLink.user == user))

    def add_user_link(self, user: str, uuid: str):
        try:
            link = self._try_get_link(user, uuid)
        except DoesNotExist:

            link = UserLink(
                user=user,
                route=uuid
            )

            link.save()

    def get_users_links(self, user: str):
        routes = Route.select().join(UserLink).where(UserLink.user == user)

        return [get_route_json(route) for route in routes]

    def remove_user_link(self, user: str, uuid: str):
        try:
            link = self._try_get_link(user, uuid)
        except DoesNotExist as e:
            pass # Make this idempotent
        else:
            link.delete_instance()

from .RouteDataMapper import RouteDataMapper