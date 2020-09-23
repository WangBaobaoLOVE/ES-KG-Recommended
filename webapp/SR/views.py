from django.shortcuts import render, redirect
from django.http import HttpResponse

# jieba -> import
import jieba
import re
from collections import Counter   #引入Counter
from elasticsearch import Elasticsearch
es = Elasticsearch(['localhost:9200'])
import pandas as pd
schoolRange = pd.read_excel('static/files/schoolRange.xlsx')
import math

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
    if not word:
        return []

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

    if not word:
        return []

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

    if not word:
        return []

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

    # acount_ids = dict(Counter(acount_ids_all))
    return acount_ids_all

def select(word):
    edu_work_project_ids = [[], [], []]

    edu_work_project_ids[0] += edu_select(word[0])
    edu_work_project_ids[1] += work_select(word[1])
    edu_work_project_ids[2] += project_select(word[2])

    acount_ids = acount_select(edu_work_project_ids)

    return acount_ids

def score_edu(edu_ids):
    for edu_index in [0, -1]:
        edu_search = es.search(
                index='eke_education',
                body = {
                    "query": {
                        "match": {
                            "_id": edu_ids[edu_index]
                        }
                    }
                },
                filter_path=["hits.hits._source"]
            )
        if edu_index == 0:
            edu = edu_search['hits']['hits'][0]['_source']['school_name']
        else:
            d = edu_search['hits']['hits'][0]['_source']['sort_id']
            if d > 3:
                d = 3
    print(edu)
    # print(d)

    edu_range = schoolRange[schoolRange['学校名称'] == edu]
    if not edu_range.shape[0]:
        s = 60
        m = 1
    else:
        s = edu_range['综合得分'].iloc[0]
        m = edu_range['星级排名'].iloc[0]

    E = (d * d) * (s / 10) * m / 9
    print('d = {}; m = {}; s = {}; E = {}.'.format(d,m,s,E))
    return E

def score_work(work_ids):
    scale_list = []
    for work_index in range(len(work_ids)):
        work = es.search(
                index='eke_work',
                body = {
                    "query": {
                        "match": {
                            "_id": work_ids[work_index]
                        }
                    }
                },
                filter_path=["hits.hits._source"]
            )
        work = work['hits']['hits'][0]['_source']
        # print(work)

        symbol = '，|。|：|；|？|“|”|！|、|‘|’|-|人'
        # print(re.split(symbol, work['scale']))
        if not work['scale']:
            scale_list.append(10)
        else:
            for each_scale in re.split(symbol, work['scale']):
                try:
                    if isinstance(int(each_scale), int):
                        scale_list.append(int(each_scale))
                except:
                    pass
                # print(each_scale)

        if work_index == 0:
            if not work['end_time']:
                y_end = work['start_time'].split('年')[0]
            else:
                y_end = work['end_time'].split('年')[0]
            # print(y_end)

            if len(work_ids) == 1:
                y_start = work['start_time'].split('年')[0]
        elif work_index == len(work_ids)-1:
            y_start = work['start_time'].split('年')[0]

    # print('this is work')
    # print(scale_list)
    c = max(scale_list)
    if c < 10:
        c = 10
    # print(c)
    # print(y_end)
    # print(y_start)
    y = int(y_end) - int(y_start) if int(y_end) > int(y_start) else int(y_start) - int(y_end)
    y_ = y/len(work_ids)
    W = 10*math.log10(y+1)*y_*(math.log10(c))*(math.log10(c))/16
    print('c={};y={};y_={};W={}'.format(c,y,y_,W))
    return W

def score_project(project_ids):
    P = 0
    for project_id in project_ids:
        project = es.search(
                index='eke_project',
                body = {
                    "query": {
                        "match": {
                            "_id": project_id
                        }
                    }
                },
                filter_path= ["hits.hits._source"]
            )
        project = project['hits']['hits'][0]['_source']
        # print(project)
    return 0

def score(acount_id):
    a = 0.4
    b = 0.3
    c = 0.3
    # print(acount_id)
    acount = es.search(
                index='eke_acount',
                body = {
                    "query": {
                        "match": {
                            "_id": acount_id
                        }
                    }
                },
                filter_path=["hits.hits._source"]
            )
    acount = acount['hits']['hits'][0]['_source']

    edu_ids = acount["education"]
    work_ids = acount["work"]
    project_ids = acount["project"]

    E = score_edu(edu_ids)
    W = score_work(work_ids)
    P = score_project(project_ids)
    Score = a * E + b * W + c * P
    return Score

def sort(acount_selected):
    acount_sorted = {}
    print('this is sort!')

    for each_acount in acount_selected:
        acount_sorted[each_acount] = score(each_acount)

    print(acount_sorted)
    return acount_sorted

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
        # print(words)

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
        acount_ids = select(word)
        # print(acount_ids)

        # sort
        acount_sorted = sort(acount_ids)

        return redirect('results')
    return render(request, 'SR/search.html')

def results(request):
    if request.method == 'POST':
        print('this is post')
        return render(request, 'SR/results.html')
    return render(request, 'SR/results.html')

def profile(request):
    return render(request, 'SR/profile.html')