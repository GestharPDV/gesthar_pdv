from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserChangeForm
from .models import UserGesthar

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail",widget=forms.EmailInput())

class UserGestharCreationForm(UserCreationForm):
    class Meta:
        model = UserGesthar
        fields = ["username", "email", "password1", "password2"]

class UserGestharChangeForm(UserChangeForm):
    class Meta:
        model = UserGesthar
        fields = ["first_name", "last_name", "email", "cpf", "phone_number", "hire_date"]
