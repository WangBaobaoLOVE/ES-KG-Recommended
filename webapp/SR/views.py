from django.shortcuts import render, redirect
from django.http import HttpResponse

# jieba -> import
import jieba
import re
from collections import Counter   #引入Counter
from elasticsearch import Elasticsearch
es = Elasticsearch(['localhost:9200'])

######################
# the functions defined by myself
#######################

def splitWords(text):
    words_splited = jieba.cut_for_search(text)
    words_string = ','.join(words_splited)
    words_list = words_string.split(',')
    print(words_list)
    return words_list

def wordsClassifiter(text):
    edu_dic = ['专业', '大学', '高校', '毕业', '深造', '本科', '硕士', '博士', '学生', '研究生', '学院', '学', '大']
    work_dic = ['工作', '就业']
    project_dic = ['项目']
    dics = [edu_dic, work_dic, project_dic]
    symbol = '，|。|：|；|？|“|”|！|、|‘|’'

    text = re.split(symbol, text)
    text.reverse()
    print(text)

    before = -1
    edu_work_project = [[],[],[]]
    for words in text:
        if words:
            for dic_num in range(len(dics)):
                status = 0
                for word in dics[dic_num]:
                    if word in words:
                        edu_work_project[dic_num].append(words)
                        before = dic_num
                        status = 1
                        break

                if status:
                    break
            if status == 0 and before >= 0:
                edu_work_project[before].append(words)

    return edu_work_project

def wordClassifiter(words):
    edu_work_project_words = [[], [], []]
    for words_num in range(len(edu_work_project_words)):
        print(words_num)
        for word in words[words_num]:
            if not word:
                break
            print(word)
            edu_work_project_words[words_num] += splitWords(word)

    print(edu_work_project_words)
    return edu_work_project_words

def edu_select(word):
    edu_ids = []
    filed_names = ["school_name","discipline_name"]
    for each_word in word:
        if len(each_word)<2:
            continue
        for filed_name in filed_names:
            if len(each_word) < 4 and filed_name == "school_name":
                continue
            results_edu = es.search(
                index='eke_education',
                body={
                    "query": {
                        "match":{
                            filed_name: each_word,
                        }
                        # 还需要添加一个学历本科，硕士和博士的筛选
                    },
                    "size": 100
                },
                filter_path=["hits.hits._id"]
            )

            for result_edu in results_edu['hits']['hits']:
                edu_ids.append(result_edu['_id'])
    return list(set(edu_ids))

def work_select(word):
    work_ids = []

    for each_word in word:
        results_work = es.search(
            index='eke_work',
            body={
                "query": {
                    "multi_match":{
                        "query": each_word,
                        "fields":["responsibilities","achievement","corporation_name","industry_name","architecture_name","position_name"]
                    }
                    # 还需要添加years的筛选
                }
            },
            filter_path=["hits.hits._id"]
        )


        for result_work in results_work['hits']['hits']:
            work_ids.append(result_work['_id'])

    return list(set(work_ids))

def project_select(word):
    project_ids = []

    for each_word in word:
        results_project = es.search(
            index='eke_project',
            body={
                "query": {
                    "multi_match":{
                        "query": each_word,
                        "fields":["name","describe","responsibilities"]
                    }
                    # 还需要添加years的筛选
                }
            },
            filter_path=["hits.hits._id"]
        )


        for result_project in results_project['hits']['hits']:
            project_ids.append(result_project['_id'])

    return list(set(project_ids))

def acount_select(word):
    acount_ids_all = []
    filed_names = ['education', 'work', 'project']
    for each_filed in range(len(filed_names)):
        for each_word in word[each_filed]:
            results_acount = es.search(
                index='eke_acount',
                body = {
                    "query": {
                        "match":{
                            filed_names[each_filed]: each_word
                        }
                    }
                },
                filter_path=["hits.hits._id"]
            )
            for result_acount in results_acount['hits']['hits']:
                acount_ids_all.append(result_acount['_id'])

    acount_ids = dict(Counter(acount_ids_all))
    return acount_ids

def select(word):
    edu_work_project_ids = [[], [], []]

    edu_work_project_ids[0] += edu_select(word[0])
    edu_work_project_ids[1] += work_select(word[1])
    edu_work_project_ids[2] += project_select(word[2])

    acount_ids = acount_select(edu_work_project_ids)

    return acount_ids

def sort():
    pass

##########################
# Create your views here.
#
###########################

def search(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        if not text:
            return render(request, 'SR/search.html',{'status': '输入为空，请重新输入'})

        # 分句
        words = wordsClassifiter(text)
        print(words)

        effect = 0
        for word in words:
            if word:
                effect = 1
                break
        if not effect:
            return render(request, 'SR/search.html',{'status': '输入无效，请输入有效的语句'})

        # 分词
        word = wordClassifiter(words)

        effect = 0
        for word_ in word:
            if word_:
                effect = 1
                break
        if not effect:
            return render(request, 'SR/search.html',{'status': '输入无效，请输入有效的语句'})

        # select
        acount_ids_nums = select(word)
        print(acount_ids_nums)

        # sort


        return redirect('results')
    return render(request, 'SR/search.html')

def results(request):
    if request.method == 'POST':
        print('this is post')
        return render(request, 'SR/results.html')
    return render(request, 'SR/results.html')

def profile(request):
    return render(request, 'SR/profile.html')