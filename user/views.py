from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login,logout

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

