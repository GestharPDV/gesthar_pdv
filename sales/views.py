from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from product.models import ProductVariation
from .models import Sale, SaleItem, CashRegister, SalePayment
from .forms import (
    AddItemForm,
    CloseRegisterForm,
    OpenRegisterForm,
    IdentifyCustomerForm,
    PaymentForm,
)


@login_required
def open_register_view(request):
    """
    Tela para informar o fundo de troco e abrir o caixa.
    Bloqueia abertura se já existir um caixa aberto para este usuário.
    """
    if CashRegister.objects.filter(
        user=request.user, status=CashRegister.Status.OPEN
    ).exists():
        messages.info(request, "Você já possui um caixa aberto.")
        return redirect("sales:pdv")

    form = OpenRegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.status = CashRegister.Status.OPEN
            session.save()

            messages.success(
                request,
                f"Caixa aberto com sucesso! Fundo de Troco: R$ {session.opening_balance}",
            )
            return redirect("sales:pdv")

    return render(request, "sales/open_register.html", {"form": form})


@login_required
def close_register_view(request):
    """Tela para conferir valores e fechar o caixa."""
    # Tenta buscar a sessão de forma segura
    session = CashRegister.objects.filter(
        user=request.user, status=CashRegister.Status.OPEN
    ).first()

    # Se não tiver caixa aberto, redireciona com aviso ao invés de dar erro 404
    if not session:
        messages.error(request, "Você não tem nenhum caixa aberto para fechar.")
        return redirect("sales:pdv")  # Ou redireciona para o Dashboard

    form = CloseRegisterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            final_value = form.cleaned_data["closing_balance"]
            try:
                session.close_session(final_value)
                messages.success(
                    request, f"Caixa fechado. Valor final: R$ {final_value}"
                )
                return redirect("product:product-list")
            except ValidationError as e:
                messages.error(request, e.message)

    return render(
        request, "sales/close_register.html", {"form": form, "session": session}
    )


@login_required
def pdv_view(request):
    """
    Tela Principal do PDV.
    Busca ou Cria um Rascunho vinculado ao usuário logado.
    """
    cash_register_session = CashRegister.objects.filter(
        user=request.user, status=CashRegister.Status.OPEN
    ).first()

    if not cash_register_session:
        messages.warning(
            request, "O caixa está fechado. Abra o caixa para começar a vender."
        )
        return redirect("sales:open-register")

    # Busca a última venda em aberto (RASCUNHO)
    # Em produção, filtraria por request.user ou caixa_id
    sale, created = Sale.objects.get_or_create(
        status=Sale.Status.DRAFT,
        user=request.user,
        defaults={
            "status": Sale.Status.DRAFT,
            "user": request.user,
            "cash_register_session": cash_register_session,
        },
    )

    if not sale.cash_register_session:
        sale.cash_register_session = cash_register_session
        sale.save(update_fields=["cash_register_session"])

    sale.calculate_totals()

    if created:
        messages.info(request, "Nova venda iniciada.")

    items = sale.items.select_related("variation__product").all().order_by("-id")

    # busca pagamentos relacionados
    payments = sale.payments.all().order_by("created_at")
    # Cria o formulário de pagamento com o valor restante
    payment_form = PaymentForm(initial={"amount": sale.remaining_balance})
    available_products = ProductVariation.active.select_related('product', 'color', 'size').order_by('product__name')

    context = {
        "sale": sale,
        "items": items,
        "payments": payments,
        "form": AddItemForm(),
        "payment_form": payment_form,
        "available_products": available_products, 
        "customer_form": IdentifyCustomerForm(),
    }
    return render(request, "sales/pdv.html", context)


@require_POST
@login_required
def add_item_view(request):
    """Processa a adição de item via código de barras/SKU"""
    sale = Sale.objects.filter(status=Sale.Status.DRAFT, user=request.user).first()
    if not sale:
        return redirect("sales:pdv")

    form = AddItemForm(request.POST)

    if form.is_valid():
        variation = form.cleaned_data["sku_or_barcode"]
        quantity = form.cleaned_data["quantity"]

        item, created = SaleItem.objects.get_or_create(
            sale=sale,
            variation=variation,
            defaults={"quantity": 0, "unit_price": variation.product.selling_price},
        )

        item.quantity += quantity
        item.save()

        messages.success(request, f"Adicionado: {variation}")
    else:
        # Retorna erro do formulário (ex: Produto não encontrado)
        for error in form.errors.values():
            messages.error(request, error)

    return redirect("sales:pdv")


@require_POST
def remove_item_view(request, item_id):
    """Remove item do carrinho"""
    item = get_object_or_404(
        SaleItem,
        pk=item_id,
        sale__status=Sale.Status.DRAFT,
        sale__user=request.user,  # <--- SEGURANÇA EXTRA
    )
    item.delete()
    messages.warning(request, "Item removido.")
    return redirect("sales:pdv")


@require_POST
@login_required
def add_payment_view(request):
    sale = Sale.objects.filter(status=Sale.Status.DRAFT, user=request.user).first()
    if not sale:
        return redirect("sales:pdv")

    form = PaymentForm(request.POST)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.sale = sale

        # Validação Lógica: Só permite pagar a mais se for DINHEIRO (para gerar troco)
        # Se for cartão/pix, trava no valor restante
        if (
            payment.method != SalePayment.Method.DINHEIRO
            and payment.amount > sale.remaining_balance
        ):
            messages.error(
                request,
                f"Pagamento em {payment.get_method_display()} não pode exceder o saldo restante (R$ {sale.remaining_balance}).",
            )
            return redirect("sales:pdv")

        payment.save()
        messages.success(request, f"Pagamento de R$ {payment.amount} adicionado.")
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect("sales:pdv")


@require_POST
@login_required
def remove_payment_view(request, payment_id):
    payment = get_object_or_404(
        SalePayment,
        pk=payment_id,
        sale__user=request.user,
        sale__status=Sale.Status.DRAFT,
    )
    payment.delete()
    messages.warning(request, "Pagamento removido.")
    return redirect("sales:pdv")


@require_POST
@login_required
def complete_sale_view(request, sale_id):
    """Finaliza a venda (Baixa estoque e fecha caixa)"""
    sale = get_object_or_404(
        Sale, pk=sale_id, status=Sale.Status.DRAFT, user=request.user
    )

    cash_register_session = CashRegister.objects.filter(user=request.user, status=CashRegister.Status.OPEN).first()
    if not cash_register_session:
        messages.error(request, "Seu caixa está fechado. Não é possível finalizar.")
        return redirect('sales:open-register')

    if not sale.cash_register_session:
        sale.cash_register_session = cash_register_session
        sale.save()

    try:
        sale.complete_sale()
        
        msg = f"Venda #{sale.pk} finalizada com sucesso!"
        if sale.change_amount > 0:
            msg += f" TROCO: R$ {sale.change_amount:,.2f}"
            
        messages.success(request, msg)

    except ValidationError as e:
        messages.error(request, f"Erro ao finalizar: {e.message}")
    except Exception as e:
        messages.error(request, "Erro inesperado ao processar venda.")

    return redirect("sales:pdv")


# Identificar Cliente na Venda
@require_POST
@login_required
def identify_customer_view(request):
    """Vincula um cliente à venda atual (Rascunho)."""
    sale = Sale.objects.filter(status=Sale.Status.DRAFT, user=request.user).first()
    if not sale:
        return redirect("sales:pdv")

    form = IdentifyCustomerForm(request.POST)
    if form.is_valid():
        customer = form.cleaned_data["cpf_cnpj"]
        sale.customer = customer
        sale.save(update_fields=["customer"])
        messages.success(request, f"Cliente identificado: {customer.name}")
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect("sales:pdv")
