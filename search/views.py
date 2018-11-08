from django.shortcuts import render
import json
from django.views.generic.base import View
from search.models import IndeedType
from django.http import HttpResponse

# Create your views here.
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