from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.cache import cache
from user.form import UserGestharCreationForm
from user.models import UserGesthar
from .forms import EmailAuthenticationForm

# Limite de tentativas de login por IP
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_LOCKOUT_SECONDS = 300  # 5 minutos


def _get_login_cache_key(ip):
    return f"login_attempts_{ip}"


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def login_view(request):
    ip = _get_client_ip(request)
    cache_key = _get_login_cache_key(ip)
    attempts = cache.get(cache_key, 0)

    if attempts >= _LOGIN_MAX_ATTEMPTS:
        messages.error(
            request,
            f'Muitas tentativas de login. Tente novamente em {_LOGIN_LOCKOUT_SECONDS // 60} minutos.',
        )
        return render(request, "accounts/login_page.html", {"form": EmailAuthenticationForm(), "locked": True})

    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                cache.delete(cache_key)
                login(request, user)
                return redirect("base:home")
        # Incrementa contador de tentativas falhas
        cache.set(cache_key, attempts + 1, timeout=_LOGIN_LOCKOUT_SECONDS)
    else:
        form = EmailAuthenticationForm()

    return render(request, "accounts/login_page.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def register_view(request):
    """Auto-cadastro desativado: apenas administradores podem criar usuários."""
    if not (request.user.role == UserGesthar.Role.ADMIN or request.user.is_superuser):
        messages.error(request, 'Acesso restrito: apenas administradores podem cadastrar usuários.')
        return redirect('base:home')
    # Redireciona para a view oficial de criação de usuário
    return redirect('accounts:user-create')


@login_required
def user_create_view(request):
    """View para criar novo usuário (restrita a Administradores)."""
    if not (request.user.role == UserGesthar.Role.ADMIN or request.user.is_superuser):
        messages.error(request, 'Acesso restrito: apenas administradores podem cadastrar usuários.')
        return redirect('base:home')

    if request.method == "POST":
        form = UserGestharCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuário "{user.get_full_name()}" cadastrado com sucesso!')
            return redirect("user:user-list")
    else:
        form = UserGestharCreationForm()

    return render(request, "user/user_form.html", {"form": form, "action": "Cadastrar"})


@login_required
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect("user:user-profile", pk=request.user.pk)
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})
