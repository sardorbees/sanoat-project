from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import json

@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({'success': True})


@csrf_protect
def test_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        return JsonResponse({'status': 'ok', 'data': data})


from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
