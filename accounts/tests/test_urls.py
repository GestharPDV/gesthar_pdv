from django.test import TestCase
from django.urls import reverse


class PasswordResetUrlsTest(TestCase):
    """Testes básicos de roteamento para o fluxo de recuperação de senha"""

    def test_password_reset_form_retorna_200(self):
        response = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_form.html")

    def test_password_reset_done_retorna_200(self):
        response = self.client.get(reverse("accounts:password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_done.html")

    def test_password_reset_complete_retorna_200(self):
        response = self.client.get(reverse("accounts:password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_complete.html")
