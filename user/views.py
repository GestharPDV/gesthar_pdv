from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, ListView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
import re  # Importação necessária para limpar a busca

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
            # Cria uma versão da busca contendo apenas números para comparar com CPF/Telefone
            query_numbers = re.sub(r'[^0-9]', '', query)

            # Monta os filtros
            q_filter = Q(first_name__icontains=query) | \
                       Q(last_name__icontains=query) | \
                       Q(email__icontains=query) | \
                       Q(role__icontains=query)

            # Se a busca tiver números, adiciona filtro por CPF e Telefone usando a versão limpa
            if query_numbers:
                q_filter |= Q(cpf__icontains=query_numbers)
                q_filter |= Q(phone_number__icontains=query_numbers)

            queryset = queryset.filter(q_filter)
            
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
            is_active = form.cleaned_data.get('is_active')
            
            if user == request.user and is_active is False:
                form.add_error(None, "Ação bloqueada: Você não pode inativar seu próprio usuário, pois isso o desconectaria do sistema.")
            else:
                form.save()
                return redirect("user:user-list") 
    else:
        form = UserGestharChangeForm(instance=user)
    
    return render(request, "user/user_form.html", {"form": form, "action": "Editar"})


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View para deletar usuário com confirmação.
    """
    model = UserGesthar
    template_name = 'user/user_confirm_delete.html'
    success_url = reverse_lazy('user:user-list')
    context_object_name = 'user_to_delete'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # Verifica se é tentativa de deletar a si mesmo comparando os IDs (pk)
        if user_obj.pk == self.request.user.pk:
            context['error_message'] = "Você não pode deletar sua própria conta."
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Impede que o usuário delete sua própria conta capturando a requisição POST
        if self.object.pk == request.user.pk:
            messages.error(request, "Ação bloqueada: Você não pode deletar sua própria conta.")
            return redirect("user:user-profile", pk=self.object.pk)
        
        user_name = self.object.get_full_name()
        messages.success(request, f'Usuário "{user_name}" removido com sucesso!')
        
        # Prossegue com a exclusão padrão se não for o próprio usuário
        return super().post(request, *args, **kwargs)


def superuser_required(user):
    return user.is_superuser