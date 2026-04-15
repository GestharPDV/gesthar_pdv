from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import check_password

from user.models import UserGesthar


def make_user(email, role=UserGesthar.Role.VENDEDOR, password='Senha@123', cpf='52998224725', **kwargs):
    """Utilitário para criar usuários nos testes."""
    user = UserGesthar.objects.create_user(
        email=email,
        password=password,
        first_name='Teste',
        last_name='Usuario',
        cpf=cpf,
        role=role,
        **kwargs,
    )
    return user


class RBACPermissionTests(TestCase):
    """Testes de controle de acesso baseado em perfil (RBAC)."""

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin@test.com', role=UserGesthar.Role.ADMIN)
        self.vendedor = make_user('vendedor@test.com', role=UserGesthar.Role.VENDEDOR)

    def test_vendedor_nao_acessa_lista_usuarios(self):
        """Vendedor deve receber redirect ao tentar acessar /user/list/."""
        self.client.force_login(self.vendedor)
        response = self.client.get(reverse('user:user-list'))
        # AdminRequiredMixin redireciona para home
        self.assertNotEqual(response.status_code, 200)

    def test_admin_acessa_lista_usuarios(self):
        """Admin deve conseguir acessar /user/list/."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('user:user-list'))
        self.assertEqual(response.status_code, 200)

    def test_vendedor_nao_acessa_cadastro_usuario(self):
        """Vendedor deve ser redirecionado ao tentar cadastrar usuário."""
        self.client.force_login(self.vendedor)
        response = self.client.get(reverse('accounts:user-create'))
        self.assertRedirects(response, reverse('base:home'))

    def test_admin_acessa_cadastro_usuario(self):
        """Admin deve conseguir acessar a view de cadastro de usuário."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('accounts:user-create'))
        self.assertEqual(response.status_code, 200)

    def test_vendedor_nao_acessa_edicao_usuario(self):
        """Vendedor não deve conseguir editar outro usuário."""
        self.client.force_login(self.vendedor)
        response = self.client.get(reverse('user:user-edit', kwargs={'pk': self.admin.pk}))
        self.assertRedirects(response, reverse('base:home'))

    def test_usuario_nao_autenticado_redirecionado(self):
        """Usuário não logado deve ser redirecionado para o login."""
        response = self.client.get(reverse('user:user-list'))
        self.assertNotEqual(response.status_code, 200)


class LastAdminProtectionTests(TestCase):
    """Testes da proteção do último administrador."""

    def setUp(self):
        self.admin = make_user('unico_admin@test.com', role=UserGesthar.Role.ADMIN)
        self.client = Client()
        self.client.force_login(self.admin)

    def test_nao_pode_rebaixar_ultimo_admin(self):
        """Não deve ser possível alterar o role do único admin para VENDEDOR."""
        response = self.client.post(
            reverse('user:user-edit', kwargs={'pk': self.admin.pk}),
            data={
                'first_name': self.admin.first_name,
                'last_name': self.admin.last_name,
                'email': self.admin.email,
                'cpf': '529.982.247-25',
                'hire_date': '2020-01-01',
                'birth_date': '1990-01-01',
                'role': UserGesthar.Role.VENDEDOR,  # tenta rebaixar
                'is_active': True,
            },
        )
        self.admin.refresh_from_db()
        # O role deve permanecer ADMIN
        self.assertEqual(self.admin.role, UserGesthar.Role.ADMIN)
