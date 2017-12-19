from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, MultiSearch
from .models import extract_route_dict
import os
import json

class StatisticQueryier:
    def __init__(self):
        self._es = Elasticsearch(f"http://elastic:changeme@elasticsearch:9200")
        self._es_search = Search(using=self._es, index="whr_routing_server")

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

    def _logs_query(self, uuid, success):
        return self._es_search \
            .query("match", uuid=uuid) \
            .query("match", success=False)

    def get_route_logs(self, uuid: str):
        """
        Get failure logs from elasticsearch
        """

        # NOTE: this only returns the 10 most recent searches
        # see https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
        return self.logs_query(uuid, False).sort("-@timestamp").execute()

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

        successes = self.logs_query(uuid, False).params(search_type="count").count()
        failures = self.logs_query(uuid, True).params(search_type="count").count()

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
