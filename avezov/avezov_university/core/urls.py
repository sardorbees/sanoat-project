from django.urls import path
from .views import get_csrf, test_post
from .views import home

urlpatterns = [
    path('api/csrf/', get_csrf),
    path('api/test-post/', test_post),
    path('', home, name='home'),
]
