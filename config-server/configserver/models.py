from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist, ForeignKeyField, BooleanField
from peewee import Proxy

proxy_db = Proxy()

class Route(Model):
    uuid = CharField()
    owner = CharField()
    name = CharField()
    destination = CharField()
    no_ssl_verification = BooleanField()
    token = CharField()

    class Meta:
        database = proxy_db

def get_route_json(route: Route):
    """
    Gets the json respresentation of given route, for returning to the user
    """
    public_fields = ["uuid", "owner", "name", "destination", "token", "no_ssl_verification"]
    new_ob = {}

    for field in public_fields:
        new_ob[field] = getattr(route, field)

    return new_ob

class UserLink(Model):
    user = CharField()
    route_uuid = ForeignKeyField(Route, to_field="uuid")

    class Meta:
        database = proxy_db