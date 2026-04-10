from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from user.form import UserGestharCreationForm
from .forms import EmailAuthenticationForm


def login_view(request):
    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("base:home")
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
            return redirect("base:home")
    else:
        form = UserGestharCreationForm()
    return render(request, "accounts/register.html", {"form": form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_create_view(request):
    """View para criar novo usuário (administrativo)"""
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

            return redirect("user:user-profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})
