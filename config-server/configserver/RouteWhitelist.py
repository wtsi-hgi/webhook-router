from urllib.parse import urlparse
from jsonpath_ng import jsonpath, parse

logger = logging.getLogger("config_server.route_data_mapper")

TOKEN_ID_LENGTH = 10

class AllowedRoutesGetter:
   def get_whitelist_rules(self):
        pass

    def set_whitelist_rules(self, new_rules: str):
        pass
    
    def is_url_valid(self, url: str):
        query_fields = ["scheme", "netloc", "path", "params", "query", "fragment", "username", "password", "hostname", "port"]

        parsed_url = urlparse(url)
        url_dict = {}

        for key in dir(parsed_url):
            if key in query_fields:
                url_dict[key] = getattr(parsed_url, key)

        



