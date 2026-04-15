from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
import re

from .models import UserGesthar, UserActionLog
from .form import UserGestharChangeForm
from .permissions import AdminRequiredMixin


class UserDetailView(LoginRequiredMixin, DetailView):
    model = UserGesthar
    template_name = "user/user_detail.html"
    context_object_name = "user_obj"


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = UserGesthar
    template_name = "user/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')

        if query:
            query_numbers = re.sub(r'[^0-9]', '', query)
            q_filter = (
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(role__icontains=query)
            )
            if query_numbers:
                q_filter |= Q(cpf__icontains=query_numbers)
                q_filter |= Q(phone_number__icontains=query_numbers)
            queryset = queryset.filter(q_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        return context


def _is_last_admin(user):
    """Retorna True se o usuário for o único administrador ativo."""
    return (
        user.role == UserGesthar.Role.ADMIN
        and UserGesthar.objects.filter(role=UserGesthar.Role.ADMIN, is_active=True).count() <= 1
    )


@login_required
def profile_edit_view(request, pk):
    if not (request.user.role == UserGesthar.Role.ADMIN or request.user.is_superuser):
        messages.error(request, 'Acesso restrito: apenas administradores podem editar usuários.')
        return redirect('base:home')

    user = get_object_or_404(UserGesthar, pk=pk)

    if request.method == "POST":
        original_role = user.role
        form = UserGestharChangeForm(request.POST, instance=user)
        if form.is_valid():
            is_active = form.cleaned_data.get('is_active')
            new_role = form.cleaned_data.get('role')

            # Impede inativar a si mesmo
            if user == request.user and is_active is False:
                form.add_error(
                    None,
                    "Ação bloqueada: você não pode inativar seu próprio usuário.",
                )
            # Impede rebaixar o último admin
            elif (
                original_role == UserGesthar.Role.ADMIN
                and new_role != UserGesthar.Role.ADMIN
                and UserGesthar.objects.filter(role=UserGesthar.Role.ADMIN, is_active=True).count() <= 1
            ):
                form.add_error(
                    'role',
                    "Ação bloqueada: não é possível remover o perfil do único administrador ativo.",
                )
            else:
                form.save()
                UserActionLog.objects.create(
                    user=request.user,
                    action=f"Editou usuário #{user.pk} ({user.get_full_name()})",
                )
                messages.success(request, f'Usuário "{user.get_full_name()}" atualizado com sucesso!')
                return redirect("user:user-list")
    else:
        form = UserGestharChangeForm(instance=user)

    return render(request, "user/user_form.html", {"form": form, "action": "Editar", "user_obj": user})


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = UserGesthar
    template_name = 'user/user_confirm_delete.html'
    success_url = reverse_lazy('user:user-list')
    context_object_name = 'user_to_delete'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        if user_obj.pk == self.request.user.pk:
            context['error_message'] = "Você não pode deletar sua própria conta."
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.pk == request.user.pk:
            messages.error(request, "Ação bloqueada: você não pode deletar sua própria conta.")
            return redirect("user:user-profile", pk=self.object.pk)

        if _is_last_admin(self.object):
            messages.error(
                request,
                "Ação bloqueada: não é possível excluir o único administrador ativo.",
            )
            return redirect("user:user-profile", pk=self.object.pk)

        # Soft delete: inativa em vez de excluir fisicamente
        self.object.is_active = False
        self.object.save()
        UserActionLog.objects.create(
            user=request.user,
            action=f"Inativou usuário #{self.object.pk} ({self.object.get_full_name()})",
        )
        messages.success(request, f'Usuário "{self.object.get_full_name()}" inativado com sucesso!')
        return redirect(self.success_url)
