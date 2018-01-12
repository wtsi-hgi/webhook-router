import argparse
import json
import os
from functools import partial
from http import HTTPStatus
from typing import Callable, Type
import time

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
DB_CONNECT_RETRY_ATTEMPTS = 10

class ConfigServer:
    """
    Main class for serving requests
    """
    def __init__(self, use_test_auth: bool, db: Database, config_JSON: any):
        self._db = db

        # wait until the database is up until we create tables if not present
        # and start the server
        for i in range(DB_CONNECT_RETRY_ATTEMPTS):
            try:
                db.connect()
            except OperationalError:
                logger.warning("Failed connecting to database.", extra={
                    "attempts": i + 1,
                    "maximum_attempts": DB_CONNECT_RETRY_ATTEMPTS
                })

                if i + 1 == DB_CONNECT_RETRY_ATTEMPTS - 1:
                    raise
            else:
                logger.info("Connected to the database.")
                break

            time.sleep(1)

        proxy_db.initialize(db)
        db.create_tables([Route, UserLink], True)
        db.close()

        user_link_dm = UserLinkDataMapper()
        route_dm = RouteDataMapper(user_link_dm)
        stat_queryier = StatisticQueryier(f"http://{os.environ['ELASTICSEARCH_USER']}:{os.environ['ELASTICSEARCH_PASSWORD']}@{os.environ['ELASTICSEARCH_HOST']}:9200")

        self.depatcher = ConnexionDespatcher(
            use_test_auth,
            route_dm,
            user_link_dm,
            stat_queryier,
            logger
        )

        self.app = connexion.App(__name__, specification_dir=".", server='tornado', auth_all_paths=(not use_test_auth))
        CORS(self.app.app, origins=f"{config_JSON['frontEnd']}*")

        self._set_error_handlers()
        self._setup_logging()

        self.app.app.after_request(self.on_after_request)

        sanger_security = {
            "name": "googleOAuth",
            "auth_url": "https://accounts.google.com/o/oauth2/auth",
            "token_url": "https://accounts.google.com/o/oauth2/tokeninfo"
        }

        self.app.add_api(
            '../swagger.yaml',
            resolver=connexion.Resolver(self.depatcher.resolve_name),
            validate_responses=True,
            arguments={
                "securities": [] if use_test_auth else sanger_security,
                "use_security": not use_test_auth
            }
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
        raise TypeError("server: main(...) - test=False requires client_id to have a value")
    server = ConfigServer(
        use_test_auth=debug,
        db=SqliteDatabase('db.db') if debug else get_postgres_db(),
        config_JSON=config_JSON
    )

    logger.info("Server running", extra={
        "port": port,
        "host": host
    })

    server.app.run(port=port, host=host)

def main():
    parser = argparse.ArgumentParser(description='Generates CWL files from the GATK documentation')
    parser.add_argument("--test", help="Enable debugging mode", action="store_true")
    parser.add_argument("--port", help="Port to serve requests over", type=int, default=8081)
    parser.add_argument("--host", help="Host to serve requests from", default="127.0.0.1")
    parser.add_argument("--config_JSON", help="Location of a JSON file which contains non secret configuration information", default="config.json")

    options = parser.parse_args()

    with open(options.config_JSON) as config_file:
        config_JSON = json.load(config_file)

    start_server(options.debug, options.port, options.host, config_JSON)

if __name__ == "__main__":
    main()
