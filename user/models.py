from django.db import models
from django.contrib.auth.models import AbstractUser


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
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
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

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username
