from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"message": "CSRF cookie set"})

from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect


@csrf_protect
def my_view(request):
    c = {}
    # ...
    return render(request, "a_template.html", c)