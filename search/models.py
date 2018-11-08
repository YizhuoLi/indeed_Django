from django.db import models

# Create your models here.
from elasticsearch_dsl import Document, Keyword, Text, Completion

from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections
# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return{}

ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])

class IndeedType(Document):
    #完成搜索建议
    suggest = Completion(analyzer=ik_analyzer)#理论上可以这样
    #要保存在elasticsearch中的数据类型
    job_title = Text(analyzer="ik_max_word")
    job_location = Text(analyzer="ik_max_word")
    job_summary = Text(analyzer="ik_max_word")
    job_salary = Text(analyzer="ik_max_word")
    company_name = Text(analyzer="ik_max_word")
    job_href = Text(analyzer="ik_max_word")
    job_star = Text(analyzer="ik_max_word")
    job_review = Text(analyzer="ik_max_word")


    class Meta:
        index = "Indeed"
        doc_type = "data_science"

    class Index:
        name = "indeed"
        doc_type = "data_science"

    # Display cluster health
    print(connections.get_connection().cluster.health())


if __name__ == "__main__":
    IndeedType.init()
