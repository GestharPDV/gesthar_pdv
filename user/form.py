from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import UserGesthar

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail",widget=forms.EmailInput())

class UserGestharCreationForm(UserCreationForm):
    class Meta:
        model = UserGesthar
        fields = ["username", "email", "password1", "password2"]