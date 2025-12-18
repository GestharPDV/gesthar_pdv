from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserManagerTests(TestCase):
    """Testes para o CustomUserManager"""
    
    def test_create_superuser_com_flags_corretas(self):
        """Teste se superusuário é criado com as flags corretas"""
        admin = User.objects.create_superuser(
            email='admin@exemplo.com',
            password='admin123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
    
    def test_create_superuser_sem_email_levanta_erro(self):
        """Teste se criar superusuário sem email levanta erro"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(email='', password='admin123')
    
    def test_create_superuser_is_staff_false_levanta_erro(self):
        """Teste se criar superusuário com is_staff=False levanta erro"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email='admin@exemplo.com',
                password='admin123',
                is_staff=False
            )
        self.assertIn('is_staff=True', str(context.exception))
    
    def test_create_superuser_is_superuser_false_levanta_erro(self):
        """Teste se criar superusuário com is_superuser=False levanta erro"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email='admin@exemplo.com',
                password='admin123',
                is_superuser=False
            )
        self.assertIn('is_superuser=True', str(context.exception))

