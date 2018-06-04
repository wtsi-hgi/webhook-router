from urllib.parse import urlparse
import socket
import ipaddress
import connexion
from flask_cors import CORS
import flask
from http import HTTPStatus
import json
from .auth import google_auth
from .errors import *
from functools import partial

class Rule:
    def __init__(self, from_port: int, to_port: int, cidr: str):
        self.from_port = from_port
        self.to_port = to_port
        self.cidr = cidr

    def does_pass_rule(self, ip_address: str, port: int):
        has_correct_port = self.from_port <= port <= self.to_port
        has_correct_ip = ipaddress.ip_address(ip_address) in ipaddress.ip_network(self.cidr, strict=False)

        return has_correct_port and has_correct_ip

class ConfigInterface:
    def __init__(self, config_json):
        self.firewallRules = []
        for rule in config_json["firewallRules"]:
            self.firewallRules.append(Rule(**rule))

        self.adminUsers = config_json["adminUsers"]

    def is_admin(self, user: str):
        return user in self.adminUsers

    def is_url_valid(self, url: str):
        parsed_url = urlparse(url)

        ip_addresses = socket.gethostbyname_ex(parsed_url.hostname)[2]
        port = parsed_url.port if parsed_url.port is not None else 80

        for rule in self.firewallRules:
            if all(rule.does_pass_rule(ip_address, port) for ip_address in ip_addresses):
                return True

        return False

class FileInterface:
    def __init__(self, file_name: str):
        self.file_name = file_name

    def get(self):
        with open(self.file_name, "r") as file:
            return file.read()

    def set(self, value):
        with open(self.file_name, "w") as file:
            file.write(value)

class ConnextionDespacher:
    def __init__(self, ioInterface, auth):
        self.ioInterface = ioInterface
        self.auth = auth

        self.config = ConfigInterface(json.loads(ioInterface.get()))

    def auth_admin(self):
        email = self.auth()

        if not self.config.is_admin(email):
            raise NotAuthorisedError()

    def auth_user(self):
        return self.auth()

    def get_config(self):
        self.auth_admin()

        return json.loads(self.ioInterface.get())

    def set_config(self, new_config):
        self.auth_admin()

        self.ioInterface.set(json.dumps(new_config))

        self.config = ConfigInterface(new_config)

        return None, 204

    def is_url_valid(self, url: str):
        return self.config.is_url_valid(url)

    def is_admin(self):
        email = self.auth_user()

        return self.config.is_admin(email)

class FirewallConfigServer:
    def resolve_name(self, name: str):
        return getattr(self.despatcher, name)

    def _set_error_handler(self, error_class, error_num, error_message, error_code):
        """
        For a given Error class, sets response that would be returned
        """
        def handler(error):
            return flask.make_response(flask.jsonify({
                "error": error_message,
                "error_num": error_num
            }), error_code)
        self.app.add_error_handler(error_class, handler)

    def __init__(self, auth, ioInterface=FileInterface("config.json")):
        self.despatcher = ConnextionDespacher(ioInterface, auth)

        self.app = connexion.App(__name__, specification_dir=".", server='tornado')

        self._set_error_handler(NotAuthorisedError, 3, "Not Authorised", HTTPStatus.FORBIDDEN)
        self._set_error_handler(InvalidCredentialsError, 5, "Invalid credentials", HTTPStatus.BAD_REQUEST)

        CORS(self.app.app)

        self.app.add_api(
            '../swagger.yaml',
            validate_responses=True,
            resolver=connexion.Resolver(self.resolve_name)
        )

def main():
    server = FirewallConfigServer(
        partial(google_auth, "859663336690-q39h2o7j9o2d2vdeq1hm1815uqjfj5c9.apps.googleusercontent.com")
    )

    server.app.run(port=80, host="0.0.0.0")

if __name__ == "__main__":
    main()