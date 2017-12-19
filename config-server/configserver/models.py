from peewee import CharField, Model, SqliteDatabase, Database, DoesNotExist, ForeignKeyField, BooleanField, IntegerField
from peewee import Proxy

proxy_db = Proxy()

class Route(Model):
    uuid = CharField(unique=True)
    name = CharField()
    destination = CharField()
    no_ssl_verification = BooleanField()
    rate_limit = IntegerField()
    token = CharField()
    # tokenId: A starting bit of the token, which is used for querying the token in the database
    token_id = CharField()

    class Meta:
        database = proxy_db

def extract_route_dict(route: Route):
    """
    Returns a dict of route properties from a instance with route properties
    """
    public_fields = ["uuid", "name", "destination", "token", "no_ssl_verification", "rate_limit"]
    new_ob = {}

    for field in public_fields:
        new_ob[field] = getattr(route, field)

    return new_ob

class UserLink(Model):
    user = CharField()
    route = ForeignKeyField(Route, to_field="uuid", on_delete="CASCADE")

    class Meta:
        database = proxy_db