from django.test import TestCase, Client

from user.models import UserGesthar
from user.form import UserGestharCreationForm
from user.tests.test_permissions import make_user


class CPFValidationTests(TestCase):
    """Testes de validação de CPF nos formulários."""

    def setUp(self):
        self.admin = make_user('adm@test.com', role=UserGesthar.Role.ADMIN)
        self.client = Client()
        self.client.force_login(self.admin)

    def test_cpf_invalido_rejeitado(self):
        """CPF com menos de 11 dígitos deve ser rejeitado no formulário."""
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
