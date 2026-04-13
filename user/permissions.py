from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


class AdminRequiredMixin(UserPassesTestMixin):
    """Restringe o acesso à view apenas para usuários com role ADMIN."""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.role == 'ADMIN' or user.is_superuser)

    def handle_no_permission(self):
        messages.error(
            self.request,
            'Acesso restrito: apenas administradores podem acessar esta página.',
        )
        return redirect('base:home')
