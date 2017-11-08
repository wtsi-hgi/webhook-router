from abc import ABC, ABCMeta
import logging

from pythonjsonlogger import jsonlogger
import connexion
import flask
from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist, BooleanField

class AbstractBaseUserLinks(Model):
    user = CharField()
    route = CharField()

def get_user_link_model(db: Database):
    """
    Gets the route model for a given database (works around peewee's irregularities)
    """
    class UserLink(AbstractBaseUserLinks):
        class Meta:
            database = db

    return UserLink

class UserLinkDataMapper:
    """
    Data mapper for the UserLink type.
    NOTE: This may be called by ConnextionDespatcher, so naming of arguments is important
    """
    def __init__(self, db: Database):
        self._UserLink = get_user_link_model(db)
        db.create_tables([self._UserLink], True)

    def _try_get_link(self, user: str, uuid: str):
        return self._UserLink.get((self._UserLink.route_uuid == uuid) & (self._UserLink.user == user))

    def add_user_link(self, user: str, uuid: str):
        try:
            link = self._try_get_link(user, uuid)
        except DoesNotExist:
            route = self._UserLink(
                user=user,
                route_uuid=uuid
            )

            route.save()

            return route
        else:
            return link

    def get_users_links(self, user: str):
        return self._UserLink.select().where(self._UserLink.user == user)

    def remove_user_link(self, user: str, uuid: str):
        try:
            link = self._try_get_link(user, uuid)
        except DoesNotExist as e:
            pass # Make this idempotent
        else:
            link.delete_instance()