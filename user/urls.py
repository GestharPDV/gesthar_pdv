from django.urls import path
from .views import login_view, logout_view, password_change_view, profile_edit_view, register_view, UserDetailView, UserListView

app_name = 'user'

urlpatterns = [
    path('login/',login_view,name='login'),
    path('logout/',logout_view,name='logout'),
    path('register/',register_view,name='register'),
    path('profile/', UserDetailView.as_view(),name='user-profile'),
    path('list/', UserListView.as_view(), name='user-list'),
    path('profile/edit/', profile_edit_view, name="user-edit"),
    path('password_change/', password_change_view, name='user-password-change'),
]