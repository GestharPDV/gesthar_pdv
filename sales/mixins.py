# sales/mixins.py
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CashRegister


class CashRegisterRequiredMixin(AccessMixin):
    """
    Mixin de View que verifica se o usuário logado tem um caixa aberto.
    Se não tiver, redireciona para a página de abertura de caixa.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Este método é executado antes do 'get' ou 'post' da view.
        """

        # 1. Verifica se o usuário tem um caixa com status "OPEN"
        has_open_cash_register = CashRegister.objects.filter(
            user=request.user, status=CashRegister.CashRegisterStatus.OPEN
        ).exists()

        # 2. Se NÃO tiver, execute a lógica de "porteiro"
        if not has_open_cash_register:
            messages.error(
                request, "Você precisa abrir seu caixa para iniciar as vendas."
            )
            # Redireciona para a URL 'sales:cash-register-open'
            return redirect(reverse_lazy("sales:cash-register-open"))

        # 3. Se tiver, deixe o fluxo continuar (chama o 'get' ou 'post' da view)
        return super().dispatch(request, *args, **kwargs)
