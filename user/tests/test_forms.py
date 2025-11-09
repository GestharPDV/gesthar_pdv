from django.test import TestCase
from django import forms
from user.form import EmailAuthenticationForm


class EmailAuthenticationFormTests(TestCase):
    """Testes para o formulário de autenticação por email"""
    
    def test_form_usa_email_field(self):
        """Teste se o formulário usa EmailField para username"""
        form = EmailAuthenticationForm()
        self.assertIsInstance(form.fields['username'], forms.EmailField)
    
    def test_label_correto(self):
        """Teste se o label do campo é 'E-mail'"""
        form = EmailAuthenticationForm()
        self.assertEqual(form.fields['username'].label, 'E-mail')
    
    def test_widget_correto(self):
        """Teste se o widget é EmailInput"""
        form = EmailAuthenticationForm()
        self.assertIsInstance(form.fields['username'].widget, forms.EmailInput)

