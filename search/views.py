from django.shortcuts import render
import json
from django.views.generic.base import View
from search.models import IndeedType
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
import redis

client = Elasticsearch(hosts=["localhost"])
redis_cli = redis.StrictRedis()

# Create your views here.


class IndexView(View):
    #首页
    def get(self, request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        return render(request, "index.html", {"topn_search":topn_search})


class SearchSuggest(View):
    """搜索建议"""
    def get(self, request):
        key_words = request.GET.get('s', '')
        # current_type = request.GET.get('s_type', '')
        # if current_type == "title":
        re_data = []
        if key_words:
            s = IndeedType.search()
            """fuzzy模糊搜索, fuzziness 编辑距离, prefix_length前面不变化的前缀长度"""
            s = s.suggest('my_suggest', key_words, completion={
                "field": "suggest", "fuzzy": {
                    "fuzziness": 2
                },
                "size": 10
            })
            suggestions = s.execute()
            for match in suggestions.suggest.my_suggest[0].options:
                source = match._source
                re_data.append(source["job_title"])
        return HttpResponse(json.dumps(re_data), content_type="application/json")
        # else:
        #     pass


class SearchView(View):

    def get(self, request):
        key_words = request.GET.get("q", "")
        page = request.GET.get("p", "1")
        try:
            page = int(page)
        except:
            page = 1


        # 实现搜索关键词keyword加1操作
        redis_cli.zincrby("search_keywords_set", key_words)
        # 获取topn个搜索词
        topn_search_clean = []
        topn_search = redis_cli.zrevrangebyscore(
            "search_keywords_set", "+inf", "-inf", start=0, num=5)
        for topn_key in topn_search:
            topn_key = str(topn_key, encoding="utf-8")
            topn_search_clean.append(topn_key)
        topn_search = topn_search_clean


        job_count = redis_cli.get("job_count")
        start_time = datetime.now()
        response = client.search(
            index="indeed",
            request_timeout=60,
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["job_title", "job_location", "job_summary"]
                    }
                },
                "from": (page-1)*10,
                "size": 10,
                "highlight": {
                    "pre_tags": ['<span style="color:red">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "job_title": {},
                        "job_summary": {},
                    }
                }
            }
        )

        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        total_nums = response["hits"]["total"]
        page_nums = int(total_nums//10 + 1)
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            if "job_title" in hit["highlight"]:
                hit_dict["job_title"] = "".join(hit["highlight"]["job_title"])
            else:
                hit_dict["job_title"] = hit["_source"]["job_title"]
            if "job_summary" in hit["highlight"]:
                hit_dict["job_summary"] = "".join(hit["highlight"]["job_summary"])
            else:
                hit_dict["job_summary"] = hit["_source"]["job_summary"]

            hit_dict["company_name"] = hit["_source"]["company_name"]
            hit_dict["job_href"] = hit["_source"]["job_href"]
            # hit_dict["job_location"] = hit["_source"]["job_location"]
            hit_dict["score"] = hit["_score"]
            hit_list.append(hit_dict)

        return render(request, "result.html", {"page": page,
                                               "all_hits": hit_list,
                                               "key_words": key_words,
                                               "total_num": total_nums,
                                               "page_num": page_nums,
                                               "last_seconds": last_seconds,
                                               "job_count": job_count,
                                               "topn_search": topn_search,
                                               })
