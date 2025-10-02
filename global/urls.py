from django.urls import path, include
from user.views import login_view
from . import views

app_name = "global"

urlpatterns = [
    path('', views.home_view, name='home'),
]
    