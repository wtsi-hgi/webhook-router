from functools import wraps
from typing import Type, Callable
from urllib.parse import urlparse
from http import HTTPStatus

from .RouteDataMapper import RouteDataMapper
from .UserLinkDataMapper import UserLinkDataMapper
from .logging import ConfigServerLogger
from .route_statistics import get_route_stats
from .errors import *


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

ignore_auth = [
    "get_by_token"
]

# Which functions to automatically add status codes to
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

    Dispaches to the RouteDataMapper, UserLinkDataMapper, and get_route_stats.
    """
    def __init__(self,  auth: Callable[[], str], 
                        route_data_mapper: RouteDataMapper,
                        user_link_data_mapper: UserLinkDataMapper,
                        logger: ConfigServerLogger):
        self._auth = auth
        self._route_data_mapper = route_data_mapper
        self._user_link_data_mapper = user_link_data_mapper
        self._logger = logger

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
            A warpper for all routing functions, which auths the request
            if needed, passing `user` as a parameter if needed and logs the request.

            This also automatically adds NO_CONTENT if needed.
            """
            user = "<NONE>" # for logging unauthed requests
            try:
                if name not in ignore_auth:
                    user = self._auth()
                    if "user" in func.__code__.co_varnames:
                        resp = func(user=user, *args, **kwargs)
                    else:
                        resp = func(*args, **kwargs)
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
        try:
            url_ob = urlparse(new_route["destination"])
        except SyntaxError:
            raise InvalidURLError()
        if url_ob.scheme == '':
            destination = "http://" + new_route["destination"]
        else:
            destination = new_route["destination"]

        route = self._route_data_mapper.add(
            user=user,
            destination=destination,
            name=new_route["name"],
            no_ssl_verification=new_route.get("no_ssl_verification", False))

        return route

    def add_route_link(self, user: str, uuid: str):
        # This also checks if the uuid exists
        route = self._route_data_mapper.get(uuid)
        
        self._user_link_data_mapper.add_user_link(user, uuid)

        return route

    def get_route_statistics(self, uuid: str):
        # make sure the uuid is actually valid
        self._route_data_mapper.get(uuid)

        return get_route_stats(uuid)