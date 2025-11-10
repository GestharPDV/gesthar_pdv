# sales/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from decimal import Decimal

# Importe os models e serviços que JÁ CRIAMOS
from .models import CashRegister, Sale
from .services import complete_sale, SaleCompletionError

# (Vamos precisar de um formulário simples para o valor de abertura)
from .forms import CashRegisterOpenForm # (Criaremos este form no próximo passo)


class CashRegisterOpenView(LoginRequiredMixin, View):
    """
    View para o usuário abrir um novo caixa.
    """
    template_name = 'sales/cash_register_open.html'
    
    def get(self, request, *args, **kwargs):
        # Primeiro, o usuário já tem um caixa aberto?
        if CashRegister.objects.filter(user=request.user, status="OPEN").exists():
            messages.info(request, "Você já possui um caixa aberto. Redirecionando para o PDV.")
            return redirect(reverse_lazy('sales:pdv')) # Vamos criar o 'pdv' em breve

        # Se não, mostre o formulário para abrir um
        form = CashRegisterOpenForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        # Se ele já tem um caixa aberto, não permita abrir outro
        if CashRegister.objects.filter(user=request.user, status="OPEN").exists():
            messages.error(request, "Ação inválida. Você já possui um caixa aberto.")
            return redirect(reverse_lazy('sales:pdv'))

        form = CashRegisterOpenForm(request.POST)
        if form.is_valid():
            try:
                # Cria o novo caixa
                initial_value = form.cleaned_data.get('initial_value')
                CashRegister.objects.create(
                    user=request.user,
                    initial_value=initial_value,
                    status="OPEN" 
                )
                messages.success(request, f"Caixa aberto com sucesso com R$ {initial_value}.")
                return redirect(reverse_lazy('sales:pdv')) # Redireciona para o Ponto de Venda
            
            except Exception as e:
                # Se falhar (ex: constraint do banco de dados), mostre o erro
                messages.error(request, f"Erro ao abrir o caixa: {e}")
                
        return render(request, self.template_name, {'form': form})