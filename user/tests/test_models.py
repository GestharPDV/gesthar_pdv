from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class UserGestharModelTests(TestCase):
    """Testes para o modelo UserGesthar"""
    
    def test_criar_usuario_com_email_valido(self):
        """Teste se é possível criar um usuário com email válido"""
        user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123',
            first_name='Thiago',
            last_name='da Silva',
            cpf='123.456.789-00'
        )
        self.assertEqual(user.email, 'teste@exemplo.com')
        self.assertTrue(user.check_password('senha123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.cpf, '123.456.789-00')
    
    def test_criar_usuario_sem_email_levanta_erro(self):
        """Teste se criar usuário sem email levanta ValueError"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(email='', password='senha123')
        self.assertIn('obrigatório', str(context.exception))
    
    def test_criar_usuario_com_campos_minimos(self):
        """Teste criar usuário apenas com email e senha"""
        user = User.objects.create_user(
            email='minimo@exemplo.com',
            password='senha123'
        )
        self.assertEqual(user.email, 'minimo@exemplo.com')
        self.assertTrue(user.check_password('senha123'))
    
    def test_criar_usuario_com_campos_opcionais(self):
        """Teste criar usuário com campos opcionais"""
        from datetime import date
        user = User.objects.create_user(
            email='completo@exemplo.com',
            password='senha123',
            phone_number='(11) 98765-4321',
            hire_date=date(2025, 1, 15)
        )
        self.assertEqual(user.phone_number, '(11) 98765-4321')
        self.assertEqual(user.hire_date, date(2025, 1, 15))
    
    def test_email_normalizado(self):
        """Teste se o domínio do email é normalizado corretamente"""
        email = 'teste@EXEMPLO.COM'
        user = User.objects.create_user(email=email, password='senha123')
        self.assertEqual(user.email, 'teste@exemplo.com')
    
    def test_email_unico(self):
        """Teste se emails duplicados não são permitidos"""
        User.objects.create_user(email='teste@exemplo.com', password='senha123')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email='teste@exemplo.com', password='senha456')
    
    def test_senha_hasheada(self):
        """Teste se a senha é armazenada de forma segura (hash)"""
        password = 'senha123'
        user = User.objects.create_user(
            email='teste@exemplo.com',
            password=password
        )
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
    
    def test_username_opcional(self):
        """Teste se username pode ser None ou vazio"""
        user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123'
        )
        self.assertIsNone(user.username)
    
    def test_str_retorna_nome_completo(self):
        """Teste se __str__ retorna o nome completo quando disponível"""
        user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123',
            first_name='João',
            last_name='Silva'
        )
        self.assertEqual(str(user), 'João Silva')
    
    def test_str_retorna_username_sem_nome_completo(self):
        """Teste se __str__ retorna username quando não há nome completo"""
        user = User.objects.create_user(
            email='teste@exemplo.com',
            password='senha123',
            username='joao123'
        )
        self.assertEqual(str(user), 'joao123')
    
    def test_username_field_configurado(self):
        """Teste se USERNAME_FIELD está configurado como email"""
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_required_fields_configurado(self):
        """Teste se REQUIRED_FIELDS está vazio"""
        self.assertEqual(User.REQUIRED_FIELDS, [])

