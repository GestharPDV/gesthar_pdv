from django.urls import path
from .views import (
    login_view,
    logout_view,
    password_change_view,
    register_view,
    register_admin_view,
    profile_view,
)

app_name = "accounts"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("register/admin/", register_admin_view, name="register-admin"),
    path("profile/", profile_view, name="profile"),
    path("password_change/", password_change_view, name="user-password-change"),
]
