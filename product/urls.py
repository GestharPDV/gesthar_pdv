from django.urls import path
from . import views

urlpatterns = [
    path('visualizar/', views.visualizar_produtos, name='visualizar_produtos'),
]
