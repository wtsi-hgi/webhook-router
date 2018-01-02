import argparse
import json
import os
from functools import partial
from http import HTTPStatus
from typing import Callable, Type

import connexion
import flask
from flask_cors import CORS
from peewee import Database, PostgresqlDatabase, SqliteDatabase, OperationalError

from .auth import *
from .ConnexionDespatcher import ConnexionDespatcher
from .errors import *
from .logging import *
from .models import Route, UserLink, proxy_db
from .RouteDataMapper import RouteDataMapper
from .StatisticQueryier import StatisticQueryier
from .UserLinkDataMapper import UserLinkDataMapper

logger = ConfigServerLogger()

class ConfigServer:
    """
    Main class for serving requests
    """
    def __init__(self, debug: bool, db: Database, auth: Callable[[], str], config_JSON: any):
        self._db = db
        self._auth = auth
        proxy_db.initialize(db)
        db.create_tables([Route, UserLink], True)

        user_link_dm = UserLinkDataMapper()
        route_dm = RouteDataMapper(user_link_dm)
        stat_queryier = StatisticQueryier()

        self.depatcher = ConnexionDespatcher(
            self._auth,
            route_dm,
            user_link_dm,
            stat_queryier,
            logger
        )

        self.app = connexion.App(__name__, specification_dir=".", server='tornado')
        CORS(self.app.app, origins=f"{config_JSON['frontEnd']}*")

        self._set_error_handlers()
        self._setup_logging()

        self.app.app.after_request(self.on_after_request)

        self.app.add_api(
            '../swagger.yaml',
            resolver=connexion.Resolver(self.depatcher.resolve_name),
            validate_responses=True
        )

    def _setup_logging(self):
        """
        Code that sets up hooks for logging requests.
        Note: swagger_requests are logged directly by the ConnexionDespatcher class
        """
        # Turn off tornado.access logging, as we handle it using our own logs
        logging.getLogger("tornado.access").setLevel(logging.CRITICAL)

        add_file_log_handler(logging.root)
        logging.root.addHandler(logging.StreamHandler())

        # This is needed, as flask logs aren't propogated to the root logger
        add_file_log_handler(self.app.app.logger)

    @staticmethod
    def on_after_request(response):
        logger.log_http_request(response)

        return response

    def _set_error_handler(self, error_class: Type[Exception], error_num: int, error_message: str, error_code: int):
        """
        For a given Error class, sets response that would be returned
        """
        def handler(error):
            return flask.make_response(flask.jsonify({
                "error": error_message,
                "error_num": error_num
            }), error_code)
        self.app.add_error_handler(error_class, handler)

    def _set_error_handlers(self):
        self._set_error_handler(InvalidRouteUUIDError, 1, "Invalid route UUID", HTTPStatus.NOT_FOUND)
        self._set_error_handler(InvalidRouteTokenError, 2, "Invalid route token", HTTPStatus.NOT_FOUND)
        self._set_error_handler(NotAuthorisedError, 3, "Not Authorised", HTTPStatus.FORBIDDEN)
        self._set_error_handler(InvalidURLError, 4, "Invalid URL in destination", HTTPStatus.BAD_REQUEST)
        self._set_error_handler(InvalidCredentialsError, 5, "Invalid credentials", HTTPStatus.BAD_REQUEST)
        self._set_error_handler(RouteLinkNotFound, 6, "Route link doesn't exist", HTTPStatus.NOT_FOUND)

    def close(self):
        self._db.close()

def get_postgres_db():
    return PostgresqlDatabase(
            os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            autorollback=True
        )

def start_server(debug: bool, port: int, host: str, config_JSON: any):
    client_id = config_JSON.get("clientId", None)

    if not debug and not client_id:
        raise TypeError("server: main(...) - debug=False requires client_id to have a value")
    server = ConfigServer(
        debug=debug,
        db=SqliteDatabase('db.db') if debug else get_postgres_db(),
        auth=test_auth if debug else partial(google_auth, client_id),
        config_JSON=config_JSON
    )

    logger.info("Server running", extra={
        "port": port,
        "host": host
    })

    server.app.run(port=port, host=host)

def main():
    parser = argparse.ArgumentParser(description='Generates CWL files from the GATK documentation')
    parser.add_argument("--debug", help="Enable debugging mode", action="store_true")
    parser.add_argument("--port", help="Port to serve requests over", type=int, default=8081)
    parser.add_argument("--host", help="Host to serve requests from", default="127.0.0.1")
    parser.add_argument("--config_JSON", help="Location of a JSON file which contains non secret configuration information", default="config.json")

    options = parser.parse_args()

    with open(options.config_JSON) as config_file:
        config_JSON = json.load(config_file)

    start_server(options.debug, options.port, options.host, config_JSON)

if __name__ == "__main__":
    main()
