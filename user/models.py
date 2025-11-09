from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Devido à customização para usar o email como identificador único,
# é necessário criar um gerenciador de usuário customizado para lidar com a criação
# de usuários e superusuários.
class CustomUserManager(BaseUserManager):
    """
    Gerenciador de usuário customizado onde o e-mail é o identificador único
    para autenticação em vez do username.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Cria e salva um usuário com o e-mail e a senha fornecidos.
        """
        if not email:
            raise ValueError("O campo E-mail é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Cria e salva um superusuário com o e-mail e a senha fornecidos.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        # O username agora é opcional, então não o passamos como argumento obrigatório
        return self.create_user(email, password, **extra_fields)


''''Modelo de usuário customizado no django'''
class UserGesthar(AbstractUser):
    # O campo 'username' é opcional para a proposta do sistema
    # Como se trata de um campo herdado e obrigatório, ele é mantido
    # mas configurado para permitir valores nulos e em branco.
    username = models.CharField(
        max_length=150,
        unique=False,
        verbose_name="Nome de Usuário",
        blank=True,
        null=True,
    )
    cpf = models.CharField(max_length=14, verbose_name="CPF")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    phone_number = models.CharField(
        max_length=15, verbose_name="Telefone", blank=True, null=True
    )
    hire_date = models.DateField(
        blank=True, verbose_name="Data de Contratação", null=True
    )

    # Definindo o campo de autenticação para ser o email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # Definindo o gerenciador customizado
    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username
