from django.shortcuts import render, redirect
from django.http import HttpResponse

# jieba -> import
import jieba
import re


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
    edu_dic = ['专业', '大学', '高校', '毕业', '深造', '本科', '硕士', '博士', '学生', '研究生', '学院', '学']
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

def select():
    pass

def sort():
    pass

# Create your views here.

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


        return redirect('results')
    return render(request, 'SR/search.html')

def results(request):
    if request.method == 'POST':
        print('this is post')
        return render(request, 'SR/results.html')
    return render(request, 'SR/results.html')

def profile(request):
    return render(request, 'SR/profile.html')