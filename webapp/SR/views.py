from django.shortcuts import render, redirect
from django.http import HttpResponse

# jieba -> import
import jieba


######################
# the functions defined by myself
#######################

def splitWords(text):
    words_splited = jieba.cut_for_search(text)
    words_string = ','.join(words_splited)
    words_list = words_string.split(',')
    return words_list

def wordsClassifiter(words_list):
    edu_work_project = [[],[],[]]
    return edu_work_project

def select():
    pass

def sort():
    pass

# Create your views here.

def search(request):
    if request.method == 'POST':
        print('this is post')
        text = request.POST.get('text')
        if not text:
            print('empty')
            return render(request, 'SR/search.html',{'status': '输入为空，请重新输入'})

        words = wordsClassifiter(splitWords(text))

        effect = 0
        for word in words:
            if word:
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