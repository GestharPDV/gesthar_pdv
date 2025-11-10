# sales/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from decimal import Decimal

from product.models import Category
from product.services import get_filtered_products
from sales.mixins import CashRegisterRequiredMixin

# Importe os models e serviços que JÁ CRIAMOS
from .models import CashRegister, Sale
from .services import complete_sale, SaleCompletionError

# (Vamos precisar de um formulário simples para o valor de abertura)
from .forms import CashRegisterOpenForm  # (Criaremos este form no próximo passo)


class CashRegisterOpenView(LoginRequiredMixin, View):
    """
    View para o usuário abrir um novo caixa.
    """

    template_name = "sales/cash_register_open.html"

    def get(self, request, *args, **kwargs):
        # Primeiro, o usuário já tem um caixa aberto?
        if CashRegister.objects.filter(user=request.user, status="OPEN").exists():
            messages.info(
                request, "Você já possui um caixa aberto. Redirecionando para o PDV."
            )
            return redirect(reverse_lazy("sales:pdv"))  # Vamos criar o 'pdv' em breve

        # Se não, mostre o formulário para abrir um
        form = CashRegisterOpenForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        # Se ele já tem um caixa aberto, não permita abrir outro
        if CashRegister.objects.filter(user=request.user, status="OPEN").exists():
            messages.error(request, "Ação inválida. Você já possui um caixa aberto.")
            return redirect(reverse_lazy("sales:pdv"))

        form = CashRegisterOpenForm(request.POST)
        if form.is_valid():
            try:
                # Cria o novo caixa
                initial_value = form.cleaned_data.get("initial_value")
                CashRegister.objects.create(
                    user=request.user, initial_value=initial_value, status="OPEN"
                )
                messages.success(
                    request, f"Caixa aberto com sucesso com R$ {initial_value}."
                )
                return redirect(
                    reverse_lazy("sales:pdv")
                )  # Redireciona para o Ponto de Venda

            except Exception as e:
                # Se falhar (ex: constraint do banco de dados), mostre o erro
                messages.error(request, f"Erro ao abrir o caixa: {e}")

        return render(request, self.template_name, {"form": form})


class PDVView(LoginRequiredMixin, CashRegisterRequiredMixin, View):
    """
    View principal do Ponto de Venda (PDV).
    Protegida pelo CashRegisterRequiredMixin.
    """

    template_name = "sales/pdv.html"  # O template que criaremos a seguir

    def get(self, request, *args, **kwargs):
        # 1. Busca os produtos para exibir na grade
        #    Usamos o service que você já tem em product/services.py
        #    Buscamos todos (query="") na página 1, com um limite alto (ex: 50)
        product_service_data = get_filtered_products(
            query="",
            page_number=1,
            per_page=50,  # Ajuste este número conforme necessário
        )

        # 2. Busca as categorias para os botões de filtro
        categories = Category.objects.filter(is_active=True)

        # 3. Busca o caixa aberto do usuário (o Mixin já garantiu que ele existe)
        try:
            current_cash_register = CashRegister.objects.get(
                user=request.user, status=CashRegister.CashRegisterStatus.OPEN
            )
        except CashRegister.DoesNotExist:
            # Isso "não deveria" acontecer por causa do Mixin,
            # mas é uma boa prática de defesa.
            messages.error(
                request, "Erro crítico: Caixa não encontrado. Abrindo novamente."
            )
            return redirect(reverse_lazy("sales:cash-register-open"))

        context = {
            "products": product_service_data.get("products"),
            "categories": categories,
            "cash_register": current_cash_register,
            # (O 'product_service_data' também contém 'paginator' e 'page_obj'
            #  se você quiser implementar paginação no PDV no futuro)
        }

        return render(request, self.template_name, context)
