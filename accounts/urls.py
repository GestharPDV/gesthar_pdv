from django.urls import path
from .views import login_view, logout_view, password_change_view, register_view, user_create_view

app_name = "accounts"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("password_change/", password_change_view, name="user-password-change"),
    path("user/create/", user_create_view, name="user-create"),
]
