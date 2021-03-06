import json
import os
from typing import List
import sys

from elasticsearch import Elasticsearch
from elasticsearch_dsl import MultiSearch, Search
from elasticsearch.exceptions import NotFoundError

from .models import extract_route_dict


class StatisticQueryier:
    def __init__(self, elasticurl: str) -> None:
        self._es = Elasticsearch(elasticurl)
        self._index = "whr_routing_server*"

        # create the index if it doesn't exist
        self._es.indices.create(index=self._index, ignore=400)

    def _logs_query(self, uuid: str, success: bool):
        search = Search(using=self._es, index=self._index)

        return search \
            .query("match", uuid=uuid) \
            .query("match", success=success)

    def get_route_logs(self, uuid: str):
        """
        Get failure logs from elasticsearch
        """

        # NOTE: this only returns the 10 most recent searches
        # see https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
        return [x for x in self._logs_query(uuid, False).sort("-@timestamp").execute().hits]

    def get_route_stats(self, uuid: str):
        """
        Gets statistics for one route
        """

        successes = self._logs_query(uuid, True).count()
        failures = self._logs_query(uuid, False).count()

        return {
            "successes": successes,
            "failures": failures
        }

    def get_many_routes_stats(self, uuids: List[str]):
        """
        Batch query of statistics for many routes. Only returns number of successes and failures
        """

        msearch = MultiSearch(using=self._es, index=self._index)

        for uuid in uuids:
            msearch = msearch.add(self._logs_query(uuid, True))
            msearch = msearch.add(self._logs_query(uuid, False))

        responses = msearch.execute()

        assert len(responses) == len(uuids) * 2

        route_stats = []
        for i in range(len(uuids)):
            route_stats.append({
                "successes": responses[i*2].hits.total,
                "failures": responses[i*2 + 1].hits.total
            })

        return route_stats
