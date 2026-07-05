from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings


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
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        # O username agora é opcional, então não o passamos como argumento obrigatório
        return self.create_user(email, password, **extra_fields)


class UserGesthar(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        VENDEDOR = 'VENDEDOR', 'Vendedor'

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
    birth_date = models.DateField(
        blank=True, verbose_name="Data de Nascimento", null=True
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VENDEDOR,
        verbose_name="Perfil de Acesso",
    )
    notes = models.TextField(
        verbose_name="Observações", blank=True, null=True
    )
    exit_date = models.DateField(
        blank=True, verbose_name="Data de Saída", null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username or self.email or f"Usuário #{self.pk}"

    def get_full_name(self):
        full_name = super().get_full_name().strip()
        if full_name:
            return full_name
        if self.username:
            return self.username
        return self.email.split('@')[0] if self.email else f"Usuário #{self.pk}"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class UserActionLog(models.Model):

    class ActionType(models.TextChoices):
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        EDIT = 'EDIT', 'Edição'
        CREATE = 'CREATE', 'Cadastro'
        DELETE = 'DELETE', 'Exclusão'
        OTHER = 'OTHER', 'Outro'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs',
        verbose_name='Usuário',
    )
    action = models.CharField(max_length=255, verbose_name='Ação')
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        default=ActionType.OTHER,
        verbose_name='Tipo de Ação',
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name='Endereço IP'
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')

    class Meta:
        verbose_name = 'Log de Atividade'
        verbose_name_plural = 'Logs de Atividade'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} — {self.action} ({self.timestamp:%d/%m/%Y %H:%M})"
