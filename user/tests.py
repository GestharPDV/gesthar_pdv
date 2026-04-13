from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import check_password

from .models import UserGesthar


def make_user(email, role=UserGesthar.Role.VENDEDOR, password='Senha@123', **kwargs):
    """Utilitário para criar usuários nos testes."""
    user = UserGesthar.objects.create_user(
        email=email,
        password=password,
        first_name='Teste',
        last_name='Usuario',
        cpf='52998224725',
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


class UserModelTests(TestCase):
    """Testes de integridade do modelo UserGesthar."""

    def test_senha_nao_salva_em_texto_plano(self):
        """A senha deve ser armazenada como hash, nunca em texto plano."""
        user = make_user('hash@test.com', password='MinhaSenha@Segura')
        user.refresh_from_db()
        self.assertNotEqual(user.password, 'MinhaSenha@Segura')
        self.assertTrue(check_password('MinhaSenha@Segura', user.password))

    def test_role_default_e_vendedor(self):
        """O perfil padrão de um novo usuário deve ser VENDEDOR."""
        user = UserGesthar.objects.create_user(
            email='default@test.com',
            password='Senha@123',
            cpf='52998224725',
        )
        self.assertEqual(user.role, UserGesthar.Role.VENDEDOR)

    def test_is_admin_property(self):
        """A property is_admin deve retornar True apenas para ADMIN."""
        admin = make_user('adm2@test.com', role=UserGesthar.Role.ADMIN)
        vendedor = make_user('vend2@test.com', role=UserGesthar.Role.VENDEDOR)
        self.assertTrue(admin.is_admin)
        self.assertFalse(vendedor.is_admin)


class CPFValidationTests(TestCase):
    """Testes de validação de CPF nos formulários."""

    def setUp(self):
        self.admin = make_user('adm@test.com', role=UserGesthar.Role.ADMIN)
        self.client = Client()
        self.client.force_login(self.admin)

    def test_cpf_invalido_rejeitado(self):
        """CPF com menos de 11 dígitos deve ser rejeitado no formulário."""
        from .form import UserGestharCreationForm
        data = {
            'first_name': 'Teste',
            'last_name': 'CPF',
            'email': 'cpf@test.com',
            'cpf': '12345678',   # inválido — menos de 11 dígitos
            'hire_date': '2020-01-01',
            'birth_date': '1990-01-01',
            'role': UserGesthar.Role.VENDEDOR,
            'password1': 'Senha@123',
            'password2': 'Senha@123',
        }
        form = UserGestharCreationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)

    def test_cpf_duplicado_rejeitado(self):
        """CPF já cadastrado deve ser rejeitado na criação de novo usuário."""
        from .form import UserGestharCreationForm
        make_user('outro@test.com', cpf='52998224725')  # CPF já usado
        data = {
            'first_name': 'Dup',
            'last_name': 'CPF',
            'email': 'dup@test.com',
            'cpf': '529.982.247-25',
            'hire_date': '2020-01-01',
            'birth_date': '1990-01-01',
            'role': UserGesthar.Role.VENDEDOR,
            'password1': 'Senha@123',
            'password2': 'Senha@123',
        }
        form = UserGestharCreationForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)


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
