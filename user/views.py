from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.generic import DetailView, ListView
from django.shortcuts import get_object_or_404

from .models import UserGesthar
from .form import UserGestharCreationForm
from .form import UserGestharChangeForm

from .form import EmailAuthenticationForm


# Create your views here.
def login_view(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("global:home")  # Redireciona para a página inicial após o login bem-sucedido
    else:
        form = EmailAuthenticationForm()
    return render(request, "user/login_page.html", {"form": form}) # Renderiza o template de login com o formulário

def logout_view(request):
    logout(request)
    return redirect("user:login")  # Redireciona para a página inicial após o logout

def register_view(request):
    if request.method == 'POST':
        form = UserGestharCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('global:home')
    else:
        form = UserGestharCreationForm()

    return render(request, 'user/register.html', {'form': form})

class UserDetailView(LoginRequiredMixin, DetailView):
    model = UserGesthar
    template_name = 'user/user_detail.html'
    context_object_name = 'user'

    def get_object(self):
        #Retorna o usuario logado
        return get_object_or_404(UserGesthar, pk=self.request.user.pk)

class UserListView(LoginRequiredMixin, ListView):
    model = UserGesthar
    template_name = 'user/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        #Só admins tem acesso
        return self.request.user.is_staff

@login_required
def profile_edit_view(request):
    user = request.user # usuario logado

    if request.method == 'POST':
        form = UserGestharChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile') #redireciona para a pagina de perfil
    else:
        form = UserGestharChangeForm(instance=user)

    return render(request, 'users/user_form.html', {'form': form})

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) # mantém o usuario logado
            return redirect('user-profile')

    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/password_change.html', {'form': form})


# apenas superusuarios podem excluir
def superuser_required(user):
    return user.is_superuser

@login_required
@user_passes_test(superuser_required)
def user_delete_view(request, pk):
    user_to_delete = get_object_or_404(UserGesthar, pk=pk)

    if user_to_delete == request.user:
        return render(request, 'users/user_confirm_delete.html', {
            'user_to_delete': user_to_delete,
            'error_message': 'Você não pode excluir a si mesmo.'
        })

    if request.method == 'POST':
        user_to_delete.delete()
        return redirect('user-list') # depois de excluir volta para lista de usuarios
    
    return render(request, 'users/user_confirm_delete.html', {'user_to_delete': user_to_delete})