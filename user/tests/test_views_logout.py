from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class LogoutViewTests(TestCase):
    """Testes para a view de logout"""
    
    def setUp(self):
        """Configuração inicial para os testes de logout"""
        self.client = Client()
        self.logout_url = reverse('user:logout')
        self.login_url = reverse('user:login')
        self.user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
    
    def test_logout_usuario_autenticado(self):
        """Teste logout de usuário autenticado"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        response = self.client.get(self.logout_url)
        # Verifica redirecionamento sem seguir (302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.login_url)
    
    def test_logout_destroi_sessao(self):
        """Teste se logout destrói a sessão do usuário"""
        self.client.login(username='teste@exemplo.com', password='senha123')
        self.assertIn('_auth_user_id', self.client.session)
        
        self.client.get(self.logout_url)
        
        # Verifica se a sessão foi limpa
        self.assertNotIn('_auth_user_id', self.client.session)
    
    def test_logout_funciona_sem_autenticacao(self):
        """Teste se logout funciona mesmo para usuário não autenticado"""
        # O importante é que não dê erro
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        # Logout sempre redireciona para login
        self.assertEqual(response.url, self.login_url)