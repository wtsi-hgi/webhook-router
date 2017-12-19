from elasticsearch import Elasticsearch
import os
import json

class StatisticQueryier:
    def __init__(self):
        self._es = Elasticsearch(f"http://elastic:changeme@elasticsearch:9200")

    @staticmethod
    def _create_uuid_query_string(uuid, query_success):
        return f'uuid:{uuid} AND success:{"true" if query_success else "false"}'

    @staticmethod
    def create_query_ob(uuid, query_success):
        return {
            "query": {
                "query_string": {
                    "query": StatisticQueryier._create_uuid_query_string(uuid, query_success)
                }
            }
        }

    def get_route_logs(self, uuid: str):
        """
        Get failure logs from elasticsearch
        """
        def extract_log(log):
            """Extract the correct output information from a log in elasticsearch"""
            return log["_source"]

        # NOTE: this function only returns the 10 most recent searches
        # see https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
        resp = self._es.search(
            index="whr_routing_server",
            body=StatisticQueryier.create_query_ob(uuid, False),
            sort="@timestamp:desc"
        )

        logs = list(map(extract_log, resp["hits"]["hits"]))

        return logs
    
    def get_route_stats(self, uuid: str):
        """
        Gets statistics for one route
        """
        def es_query(es_query_func, query_success):
            """Helper function for elasticsearch queries"""
            return es_query_func(
                index="whr_routing_server",
                body=StatisticQueryier.create_query_ob(uuid, query_success)
            )

        successes = es_query(self._es.count, True)["count"]
        failures = es_query(self._es.count, False)["count"]
        
        return {
            "successes": successes,
            "failures": failures
        }

    def get_many_routes_stats(self, uuids):
        """
        Batch query of statistics for many routes. Only returns number of successes and failures
        """
        def get_num_hits(item):
            return item["hits"]["total"]

        query_items = []

        for uuid in uuids:
            for query_success in [True, False]:
                query = StatisticQueryier.create_query_ob(uuid, query_success)
                query.update({
                    "size": 0
                })
                query_items.append("{}") # don't change the index that we're querying
                query_items.append(json.dumps(
                    query,
                    indent=None
                ))
        es_resp = self._es.msearch(
            body="\n".join(query_items),
            index="whr_routing_server"
        )
        counts = list(map(get_num_hits, es_resp["responses"]))

        assert len(counts) // 2 == len(counts) / 2

        route_stats = []
        for i in range(len(counts) // 2):
            route_stats.append({
                "successes": counts[i*2],
                "failures": counts[i*2 + 1]
            })

        return route_stats
