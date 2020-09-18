from django.shortcuts import render
from django.http import HttpResponse

# jieba -> import
import jieba

# Create your views here.

def search(request):
    if request.method == 'POST':
        print('this is post')
        return render(request, 'SR/search.html')
    return render(request, 'SR/search.html')

def results(request):
    if request.method == 'POST':
        print('this is post')
        return render(request, 'SR/results.html')
    return render(request, 'SR/results.html')

def profile(request):
    if request.method == 'POST':
        print('this is post')
        return render(request, 'SR/profile.html')
    return render(request, 'SR/profile.html')