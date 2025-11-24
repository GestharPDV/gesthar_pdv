from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import Sale, SaleItem
from .forms import AddItemForm


@login_required
def pdv_view(request):
    """
    Tela Principal do PDV.
    Busca ou Cria um Rascunho vinculado ao usuário logado.
    """
    # Busca a última venda em aberto (RASCUNHO)
    # Em produção, filtraria por request.user ou caixa_id
    sale, created = Sale.objects.get_or_create(
        status=Sale.Status.DRAFT,
        user=request.user,  
        defaults={
            "status": Sale.Status.DRAFT,
            "user": request.user,  
        },
    )

    if created:
        messages.info(request, "Nova venda iniciada.")

    items = sale.items.select_related("variation__product").all().order_by("-id")

    context = {
        "sale": sale,
        "items": items,
        "form": AddItemForm(),  # O formulário de bipar produto
    }
    return render(request, "sales/pos.html", context)


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
        sale__user=request.user # <--- SEGURANÇA EXTRA
    )
    item.delete()
    messages.warning(request, "Item removido.")
    return redirect("sales:pdv")


@require_POST
@login_required
def complete_sale_view(request, sale_id):
    """Finaliza a venda (Baixa estoque e fecha caixa)"""
    sale = get_object_or_404(
        Sale, 
        pk=sale_id, 
        status=Sale.Status.DRAFT,
        user=request.user 
    )
    try:
        sale.complete_sale()
        messages.success(request, f"Venda #{sale.pk} finalizada com sucesso!")

        # Redirecionar para uma nota fiscal ou recibo seria o ideal aqui
        # return redirect('sales:invoice', sale_id=sale.pk)

    except ValidationError as e:
        messages.error(request, f"Erro ao finalizar: {e.message}")
    except Exception as e:
        messages.error(request, "Erro inesperado ao processar venda.")

    return redirect("sales:pdv")
