from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import (
    UserGestharCreationForm,
    EmailAuthenticationForm,
    SuperUserCreationForm,
    superuser_required,
)


def login_view(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("global:home")
    else:
        form = EmailAuthenticationForm()
    return render(request, "accounts/login_page.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


def register_view(request):
    if request.method == "POST":
        form = UserGestharCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("global:home")
    else:
        form = UserGestharCreationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            return redirect("user:user-profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})


@login_required
@user_passes_test(superuser_required)
def register_admin_view(request):
    """
    View protegida para criar superusuários.
    Apenas superusuários podem acessar esta página.
    """
    if request.method == "POST":
        form = SuperUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Superusuário {user.email} criado com sucesso!",
            )
            return redirect("accounts:register-admin")
    else:
        form = SuperUserCreationForm()
    return render(request, "accounts/register_admin.html", {"form": form})


@login_required
def profile_view(request):
    """
    View para exibir o perfil do usuário logado.
    """
    user = request.user
    return render(request, "accounts/profile.html", {"user_obj": user})
