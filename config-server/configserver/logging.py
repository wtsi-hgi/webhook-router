import logging

import flask
from pythonjsonlogger import jsonlogger
from cmreslogging.handlers import CMRESHandler
import os
import sys
import requests
import time

LOGGING_CONFIG = "(asctime) (message) (levelname)"

def add_file_log_handler(logger):
    """
    Configures the given logger to output to the log file "logs.log", in order to be picked up
    by a fluent-bit parser
    """
    handler = logging.FileHandler("logs.log")
    json_formatter = jsonlogger.JsonFormatter(LOGGING_CONFIG)
    handler.setFormatter(json_formatter)
    logger.addHandler(handler)

class ConfigServerLogger:
    def __init__(self):
        logger = logging.getLogger("config_server")
        logger.propagate = False
        logger.setLevel(logging.INFO)
        json_formatter = jsonlogger.JsonFormatter(LOGGING_CONFIG)

        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(json_formatter)
        logger.addHandler(stdout_handler)

        # Wait for elastic search to boot before starting

        first_time_check = True
        while True:
            try:
                es_json = requests.get(f"""http://{os.environ["ELASTICSEARCH_HOST"]}:9200/_cluster/health""").json()
                if es_json["status"] != "red":
                    logger.info(f"Elasticsearch is up with status {es_json['status']}!")
                    break
            except requests.exceptions.ConnectionError:
                pass

            if first_time_check:
                logger.warn("Elasticsearch is not avaliable, will wait for it to launch ...")
            else:
                logger.debug("Failed poll of elasticsearch")
            first_time_check = False

            time.sleep(1)


        print("Adding logger ...", file=sys.stderr)
        es_handler = CMRESHandler(
            hosts=[{
                'host': os.environ["ELASTICSEARCH_HOST"],
                'port': 9200
            }],
            auth_type=CMRESHandler.AuthType.BASIC_AUTH,
            es_index_name="whr_config_server"
        )
        logger.addHandler(es_handler)
        logger.warn("Test log")
        print("Added logger", file=sys.stderr)


        self.logger = logger
        self.info = logger.info
        self.warning = logger.warning
        self.error = logger.error

    def log_http_request(self, response: flask.Response):
        request = flask.request
        if response.status_code < 400:
            log_method = self.logger.info
        elif 400 <= response.status_code < 500:
            log_method = self.logger.warning
        else:
            log_method = self.logger.error

        log_method("Http request", extra={
            "method": request.method,
            "url": request.url,
            "ip": request.remote_addr,
            "user_agent": str(request.user_agent),
            "status_code": response.status_code
        })

    def log_swagger_request(self, method_name, swagger_params, response, user):
        self.logger.info("Swagger access", extra={
            "method_name": method_name,
            "params": swagger_params,
            "user": user,
            "response": response
        })
