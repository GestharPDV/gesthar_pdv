from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, ListView
from django.db.models import Q

from .models import UserGesthar
from .form import UserGestharChangeForm


class UserDetailView(LoginRequiredMixin, DetailView):
    model = UserGesthar
    template_name = "user/user_detail.html"
    context_object_name = "user_obj"


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserGesthar
    template_name = "user/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(cpf__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        return context


@login_required
def profile_edit_view(request, pk):
    user = get_object_or_404(UserGesthar, pk=pk) 
    
    if request.method == "POST":
        form = UserGestharChangeForm(request.POST, instance=user)
        if form.is_valid():
            # Verifica se o usuário está tentando inativar a si mesmo
            is_active = form.cleaned_data.get('is_active')
            
            # Se for o próprio usuário e ele estiver tentando desmarcar o ativo (is_active=False)
            if user == request.user and is_active is False:
                # Adiciona o erro aos "non_field_errors" (None) para aparecer no alerta do topo da página
                form.add_error(None, "Ação bloqueada: Você não pode inativar seu próprio usuário, pois isso o desconectaria do sistema.")
            else:
                form.save()
                return redirect("user:user-list") 
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