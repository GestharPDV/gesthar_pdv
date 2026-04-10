from django.urls import path
from .views import profile_edit_view, UserDetailView, UserListView, UserDeleteView

app_name = "user"

urlpatterns = [
    path("profile/<int:pk>/", UserDetailView.as_view(), name="user-profile"),
    path("list/", UserListView.as_view(), name="user-list"),
    path("profile/edit/<int:pk>/", profile_edit_view, name="user-edit"),
    path("<int:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
]