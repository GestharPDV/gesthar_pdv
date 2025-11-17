from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from user.models import UserGesthar


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail", widget=forms.EmailInput())


def superuser_required(user):
    return user.is_superuser


class UserGestharCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Nome",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Sobrenome",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cpf = forms.CharField(
        max_length=14,
        required=True,
        label="CPF",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        label="Telefone",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    hire_date = forms.DateField(
        required=False,
        label="Data de Contratação",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    class Meta:
        model = UserGesthar
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "cpf",
            "phone_number",
            "hire_date",
            "password1",
            "password2",
        ]


class SuperUserCreationForm(UserGestharCreationForm):
    """
    Formulário para criação de superusuários.
    Apenas superusuários podem usar este formulário.
    """
    is_staff = forms.BooleanField(
        required=False,
        initial=True,
        label="É funcionário (Staff)",
        help_text="Permite acesso à área administrativa do Django.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    is_superuser = forms.BooleanField(
        required=False,
        initial=True,
        label="É superusuário",
        help_text="Concede todas as permissões do sistema.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Usuário ativo",
        help_text="Desative para impedir login sem excluir o usuário.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = UserGesthar
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "cpf",
            "phone_number",
            "hire_date",
            "password1",
            "password2",
            "is_staff",
            "is_superuser",
            "is_active",
        ]

    def save(self, commit=True):
        """
        Salva o usuário usando create_superuser se is_superuser for True,
        ou create_user caso contrário.
        """
        # Primeiro, obtém os dados limpos do formulário
        is_superuser = self.cleaned_data.get("is_superuser", False)
        is_staff = self.cleaned_data.get("is_staff", False)
        is_active = self.cleaned_data.get("is_active", True)
        password = self.cleaned_data["password1"]
        
        if commit:
            if is_superuser:
                # Usa create_superuser para garantir que todas as flags estejam corretas
                user = UserGesthar.objects.create_superuser(
                    email=self.cleaned_data["email"],
                    password=password,
                    username=self.cleaned_data.get("username") or None,
                    first_name=self.cleaned_data.get("first_name") or "",
                    last_name=self.cleaned_data.get("last_name") or "",
                    cpf=self.cleaned_data["cpf"],
                    phone_number=self.cleaned_data.get("phone_number") or None,
                    hire_date=self.cleaned_data.get("hire_date") or None,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                    is_active=is_active,
                )
            else:
                # Usa create_user para usuários normais
                user = UserGesthar.objects.create_user(
                    email=self.cleaned_data["email"],
                    password=password,
                    username=self.cleaned_data.get("username") or None,
                    first_name=self.cleaned_data.get("first_name") or "",
                    last_name=self.cleaned_data.get("last_name") or "",
                    cpf=self.cleaned_data["cpf"],
                    phone_number=self.cleaned_data.get("phone_number") or None,
                    hire_date=self.cleaned_data.get("hire_date") or None,
                    is_staff=is_staff,
                    is_active=is_active,
                )
            return user
        else:
            # Se commit=False, cria uma instância sem salvar (não recomendado para este caso)
            user = super().save(commit=False)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_active = is_active
            return user
