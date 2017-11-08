from elasticsearch import Elasticsearch

def get_route_stats(uuid: str):
    es = Elasticsearch("http://elastic:changeme@elasticsearch:9200")

    def get_query_object(query):
        return {
            "query": {
                "query_string": {
                    "query": query
                }
            }
        }
    
    def es_query(es_query_func, query_success):
        """Helper function for elasticsearch queries"""
        return es_query_func(
            index="whr_routing_server",
            body=get_query_object(f'uuid:{uuid} AND success:{"true" if query_success else "false"}')
        )

    def extract_log(log):
        """Extract the correct output information from a log in elasticsearch"""
        return log["_source"]

    num_successes = es_query(es.count, True)["count"]
    num_failures = es_query(es.count, False)["count"]
    # NOTE: this function only returns the 10 most recent searches
    # see https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
    last_failures = list(map(extract_log, es_query(es.search, False)["hits"]["hits"]))

    return {
        "num_successes": num_successes,
        "num_failures": num_failures,
        "last_failures": last_failures
    }