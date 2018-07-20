import copy
from functools import wraps
from http import HTTPStatus
from typing import Callable, Type
from urllib.parse import urlparse
import flask

from .errors import *
from .auth import *
from .logging import ConfigServerLogger
from .models import extract_route_dict
from .RouteDataMapper import RouteDataMapper
from .StatisticQueryier import StatisticQueryier
from .UserLinkDataMapper import UserLinkDataMapper

# Configuration for mapping from the data mapper to the connextion object
route_data_mapper_mappings = {
    "delete_route": "delete",
    "get_route": "get",
    "patch_route": "update",
    "get_by_token": "get_by_token",
    "regenerate_token": "regenerate_token"
}
user_link_data_mapper_mapppings = {
    "delete_route_link": "remove_user_link",
    "get_all_routes": "get_users_links"
}

# Which functions to automatically add status codes to
# PR for this: https://github.com/zalando/connexion/issues/539
status_codes = {
    "delete_route": 204,
    "patch_route": 204,
    "create_route": 201,
    "add_route_link": 201,
    "delete_route_link": 204
}

class ConnexionDespatcher:
    """
    Class, who's main function is resolve_name (see below for docs of that function).

    Dispaches to the RouteDataMapper, UserLinkDataMapper, and StatisticQueryier.
    """
    def __init__(self,  use_test_auth: bool,
                        route_data_mapper: RouteDataMapper,
                        user_link_data_mapper: UserLinkDataMapper,
                        statistic_queryier: StatisticQueryier,
                        logger: ConfigServerLogger,
                        google_oauth_client_id: str):
        self._use_test_auth = use_test_auth
        self._route_data_mapper = route_data_mapper
        self._user_link_data_mapper = user_link_data_mapper
        self._statistic_queryier = statistic_queryier
        self._logger = logger
        self._google_oauth_client_id = google_oauth_client_id

    def resolve_name(self, name: str):
        """
        From a swagger operationId, returns the correct function to use.

        Each returned value is wrapped by the function below.
        """
        try:
            func = getattr(self._route_data_mapper, route_data_mapper_mappings[name])
        except KeyError:
            try:
                func = getattr(self._user_link_data_mapper,
                    user_link_data_mapper_mapppings[name])
            except KeyError:
                func = getattr(self, name)

        @wraps(func)
        def connextion_wrapper(*args, **kwargs):
            """
            A wrapper for all routing functions, which auths the request
            if needed, passing `user` as a parameter if needed and logs the request.

            This also automatically adds NO_CONTENT if needed.
            """
            user = "<NONE>"
            try:
                # NOTE: Connexion implements oauth, but we can't use it, as it doesn't
                # work with Google's method of oauth (the token has to be passed in parameters).
                # See https://github.com/zalando/connexion/issues/555.
                if name != "get_by_token":
                    if self._use_test_auth:
                        user = test_auth()
                    else:
                        user = normal_auth(self._google_oauth_client_id)

                if "user" in func.__code__.co_varnames:
                    resp = func(*args, user=user, **kwargs)
                else:
                    resp = func(*args, **kwargs)

                code = status_codes.get(name)
                # Add status codes
                if code is not None:
                    resp = (resp, code)
            except:
                resp = "<ERROR>"
                raise
            finally:
                self._logger.log_swagger_request(name, kwargs, resp, user)

            return resp

        return connextion_wrapper

    def create_route(self, new_route: object, user: str):
        # Custom validation and replacement for expected behaviour specified in https://github.com/zalando/connexion/issues/351
        acceptable_schemes = ["http", "https"]

        new_route = copy.deepcopy(new_route)
        new_route["no_ssl_verification"]=new_route.get("no_ssl_verification", False)
        new_route["rate_limit"]=new_route.get("rate_limit", 30)

        try:
            url_ob = urlparse(new_route["destination"])
        except SyntaxError:
            raise InvalidURLError()

        if url_ob.scheme not in acceptable_schemes:
            raise InvalidURLError()

        route = self._route_data_mapper.add(
            user=user,
            **new_route)

        return route


    def add_route_link(self, user: str, uuid: str):
        # This also checks if the uuid exists
        route = self._route_data_mapper.get(uuid)

        self._user_link_data_mapper.add_user_link(user, uuid)

        return route

    def get_all_routes_stats(self, user: str):
        user_routes = self._user_link_data_mapper.get_users_links(user)
        uuids = [route["uuid"] for route in user_routes]

        if len(uuids) == 0:
            return []

        stats = self._statistic_queryier.get_many_routes_stats(uuids)

        for (i, stat) in enumerate(stats):
            stat["uuid"] = uuids[i]

        return stats

    def get_route_link(self, user: str, uuid: str):
        if not self._user_link_data_mapper.has_user_link(user, uuid):
            raise RouteLinkNotFound()

        return self._route_data_mapper.get(uuid)

    def get_route_logs(self, uuid: str):
        # make sure the uuid is actually valid
        self._route_data_mapper.get(uuid)

        return self._statistic_queryier.get_route_logs(uuid)

    def get_route_stats(self, uuid: str):
        # make sure the uuid is actually valid
        self._route_data_mapper.get(uuid)

        return self._statistic_queryier.get_route_stats(uuid)
