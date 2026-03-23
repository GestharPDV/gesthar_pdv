from django.urls import path
from .views import profile_edit_view, UserDetailView, UserListView, UserDeleteView, user_create_view

app_name = "user"

urlpatterns = [
    path("profile/<int:pk>/", UserDetailView.as_view(), name="user-profile"),
    path("list/", UserListView.as_view(), name="user-list"),
    path("create/", user_create_view, name="user-create"),
    path("profile/edit/<int:pk>/", profile_edit_view, name="user-edit"),
    path("<int:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
]