from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('alertas/', views.AlertasView.as_view(), name='alertas'),
    path('<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark-read'),
    path('read-all/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-read'),
]
