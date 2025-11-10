from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from user.form import EmailAuthenticationForm

User = get_user_model()


class LoginViewTests(TestCase):
    """Testes para a view de login"""
    
    def setUp(self):
        """Configuração inicial para os testes de login"""
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.home_url = reverse('global:home')
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123',
            cpf='123.456.789-00',
            first_name='Teste',
            last_name='Usuario'
        )
    
    def test_login_page_carrega_com_get(self):
        """Teste se a página de login carrega corretamente via GET"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user/login_page.html')
    
    def test_login_page_contem_formulario(self):
        """Teste se a página de login contém o formulário"""
        response = self.client.get(self.login_url)
        self.assertIsInstance(response.context['form'], EmailAuthenticationForm)
    
    def test_login_com_credenciais_validas(self):
        """Teste login com credenciais válidas"""
        response = self.client.post(self.login_url, {
            'username': 'teste@exemplo.com',
            'password': 'senha123'
        }, follow=True)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.email, 'teste@exemplo.com')
    
    def test_login_com_senha_incorreta(self):
        """Teste login com senha incorreta"""
        response = self.client.post(self.login_url, {
            'username': 'teste@exemplo.com',
            'password': 'senhaerrada'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_com_email_inexistente(self):
        """Teste login com email que não existe"""
        response = self.client.post(self.login_url, {
            'username': 'naoexiste@exemplo.com',
            'password': 'senha123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_com_email_vazio(self):
        """Teste login com email vazio"""
        response = self.client.post(self.login_url, {
            'username': '',
            'password': 'senha123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertFormError(response.context['form'], 'username', 'Este campo é obrigatório.')
    
    def test_login_com_senha_vazia(self):
        """Teste login com senha vazia"""
        response = self.client.post(self.login_url, {
            'username': 'teste@exemplo.com',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertFormError(response.context['form'], 'password', 'Este campo é obrigatório.')
    
    def test_login_cria_sessao(self):
        """Teste se o login cria uma sessão"""
        self.client.post(self.login_url, {
            'username': 'teste@exemplo.com',
            'password': 'senha123'
        })
        self.assertIn('_auth_user_id', self.client.session)

