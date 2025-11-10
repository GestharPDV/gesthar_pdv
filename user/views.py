from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, ListView
from django.shortcuts import get_object_or_404

from .models import UserGesthar
from .form import UserGestharChangeForm


class UserDetailView(LoginRequiredMixin, DetailView):
    model = UserGesthar
    template_name = "user/user_detail.html"
    context_object_name = "user_obj"

    def get_object(self):
        return get_object_or_404(UserGesthar, pk=self.request.user.pk)


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserGesthar
    template_name = "user/user_list.html"
    context_object_name = "users"

    def test_func(self):
        return self.request.user.is_staff


@login_required
def profile_edit_view(request):
    user = request.user
    if request.method == "POST":
        form = UserGestharChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect("user:user-profile")
    else:
        form = UserGestharChangeForm(instance=user)
    return render(request, "user/user_form.html", {"form": form})


def superuser_required(user):
    return user.is_superuser


@login_required
@user_passes_test(superuser_required)
def user_delete_view(request, pk):
    user_to_delete = get_object_or_404(UserGesthar, pk=pk)

    if user_to_delete == request.user:
        return render(
            request,
            "user/user_confirm_delete.html",
            {
                "user_to_delete": user_to_delete,
                "error_message": "Você não pode excluir a si mesmo.",
            },
        )

    if request.method == "POST":
        user_to_delete.delete()
        return redirect("user:user-list")

    return render(
        request, "user/user_confirm_delete.html", {"user_to_delete": user_to_delete}
    )
