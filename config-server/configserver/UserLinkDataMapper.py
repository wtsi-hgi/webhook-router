from abc import ABC, ABCMeta
import logging
from .errors import *
from .models import UserLink, Route, extract_route_dict

from peewee import DoesNotExist

class UserLinkDataMapper:
    """
    Data mapper for the UserLink type.
    NOTE: This may be called by ConnextionDespatcher, so naming of arguments is important
    """

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

    def has_user_link(self, user: str, uuid: str):
        try:
            self._try_get_link(user, uuid)
        except DoesNotExist:
            return False

        return True

    def get_users_links(self, user: str):
        routes = Route.select().join(UserLink).where(UserLink.user == user)

        return [extract_route_dict(route) for route in routes]

    def remove_user_link(self, user: str, uuid: str):
        try:
            link = self._try_get_link(user, uuid)
        except DoesNotExist as e:
            pass # Make this idempotent
        else:
            link.delete_instance()