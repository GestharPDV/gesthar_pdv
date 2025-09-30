from django.urls import path, include
from user.views import login_view
from . import views

app_name = "global"

urlpatterns = [
    path('', login_view, name='login'),
    path('home/', views.home_view, name='home'),
]
    