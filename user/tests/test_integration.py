from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class IntegrationTests(TestCase):
    """Testes de integração - fluxo completo"""
    
    def setUp(self):
        """Configuração inicial para testes de integração"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='integracao@exemplo.com',
            password='senha123',
            first_name='Usuario',
            last_name='Integracao'
        )
    
    def test_fluxo_completo_login_logout(self):
        """Teste o fluxo completo: login -> verificar autenticação -> logout"""
        # Login
        login_response = self.client.post(reverse('user:login'), {
            'username': 'integracao@exemplo.com',
            'password': 'senha123'
        }, follow=True)
        
        self.assertTrue(login_response.wsgi_request.user.is_authenticated)
        self.assertEqual(login_response.wsgi_request.user.email, 'integracao@exemplo.com')
        
        # Logout
        logout_response = self.client.get(reverse('user:logout'), follow=True)
        self.assertFalse(logout_response.wsgi_request.user.is_authenticated)
    
    def test_superusuario_tem_permissoes(self):
        """Teste se superusuário tem as permissões corretas"""
        admin = User.objects.create_superuser(
            email='admin@exemplo.com',
            password='admin123'
        )
        
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.has_perm('any.permission'))  # Superuser tem todas as permissões

