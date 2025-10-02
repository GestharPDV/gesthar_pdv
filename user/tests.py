from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import models

User = get_user_model()

class CustomUserManagerTests(TestCase):
    def test_create_user_with__user_password(self):
        user = User.objects.create_user(
            email = "user@example.com",
            password = "password123"
        )
        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(user.is_superuser)


    
