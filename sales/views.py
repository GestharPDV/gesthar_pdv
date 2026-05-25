from decimal import Decimal, InvalidOperation
import json
import os
import uuid
from datetime import date

import requests
from django.conf import settings
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from user.permissions import AdminRequiredMixin
from . import services

from product.models import ProductVariation
from .models import Sale, SaleItem, CashRegister, SalePayment, GatewayPayment
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
                return redirect("base:home")
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
        return redirect("sales:open-register")

    # Busca a última venda em aberto (RASCUNHO)
    # Em produção, filtraria por request.user ou caixa_id
    sale, created = Sale.objects.get_or_create(
        status=Sale.Status.DRAFT,
        user=request.user,
        cash_register_session=cash_register_session,  # <--- ADICIONE ESTA LINHA NO FILTRO
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

    items = sale.items.select_related("variation__product").all().order_by("-id")

    # busca pagamentos relacionados
    payments = sale.payments.all().order_by("created_at")
    # Cria o formulário de pagamento com o valor restante
    payment_form = PaymentForm(initial={"amount": round(sale.remaining_balance, 2)})
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
@login_required
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
        return JsonResponse({'error': 'Venda não encontrada ou já finalizada.'}, status=404)

    form = PaymentForm(request.POST)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.sale = sale

        if payment.method != SalePayment.Method.DINHEIRO and payment.amount > sale.remaining_balance:
            return JsonResponse({
                'error': f"Pagamentos em {payment.get_method_display()} não podem exceder o saldo de R$ {sale.remaining_balance:.2f}"
            }, status=400)

        payment.save()
        sale.calculate_totals()

        return JsonResponse({
            'success': True,
            'remaining': float(sale.remaining_balance),
            'change': float(sale.change_preview),
            'total_paid': float(sale.total_paid),
            'method': payment.get_method_display()
        })
    
    return JsonResponse({'error': "Valor ou método inválido."}, status=400)


@require_POST
@login_required
def create_mp_order_view(request):
    """Cria uma order no Mercado Pago Point para a venda atual.

    Espera receber via POST:
    - sale_id (opcional): id da venda; se ausente, usa a venda em rascunho do usuário
    - terminal_id (opcional): id completo do terminal (ex: NEWLAND_N950__...); se ausente, tenta usar env TERMINAL_ID
    - expiration_time (opcional): string ISO-8601 period (ex: PT16M)
    - installments (opcional): número de parcelas (1-6); padrão: 1
    """
    sale_id = request.POST.get('sale_id')
    terminal_id = request.POST.get('terminal_id') or os.environ.get('TERMINAL_ID')
    expiration_time = request.POST.get('expiration_time') or 'PT16M'
    installments = int(request.POST.get('installments', 1))

    if sale_id:
        sale = get_object_or_404(Sale, pk=sale_id, user=request.user)
    else:
        sale = Sale.objects.filter(status=Sale.Status.DRAFT, user=request.user).first()

    if not sale:
        return JsonResponse({'error': 'Venda não encontrada.'}, status=404)

    sale.calculate_totals()

    amount_raw = request.POST.get('amount')
    amount_decimal = sale.remaining_balance if sale.remaining_balance > 0 else sale.net_amount

    if amount_raw:
        try:
            amount_decimal = Decimal(str(amount_raw).replace(',', '.'))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({'error': 'Valor de amount inválido.'}, status=400)

    if amount_decimal <= 0:
        return JsonResponse({'error': 'Valor da venda inválido.'}, status=400)

    if not sale.items.exists():
        return JsonResponse({'error': 'Venda sem itens não pode gerar order.'}, status=400)

    amount = float(amount_decimal)

    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        return JsonResponse({'error': 'ACCESS_TOKEN não configurado no ambiente.'}, status=500)

    if not terminal_id:
        return JsonResponse({'error': 'terminal_id não informado (ou TERMINAL_ID não está em env).'}, status=400)

    # Validar expiration_time
    valid_expiration_times = ['PT30S', 'PT1M', 'PT5M', 'PT10M', 'PT16M', 'PT30M', 'PT1H', 'PT2H', 'PT3H']
    if expiration_time not in valid_expiration_times:
        return JsonResponse({
            'error': f'expiration_time inválido. Valores válidos: {", ".join(valid_expiration_times)}'
        }, status=400)

    # Validar installments (1 a 6)
    if not (1 <= installments <= 6):
        return JsonResponse({
            'error': f'installments deve estar entre 1 e 6. Recebido: {installments}'
        }, status=400)

    # Validar external_reference (máx 64 caracteres, apenas letras, números, -, _)
    external_ref = f'sale_{sale.pk}'
    if len(external_ref) > 64:
        return JsonResponse({
            'error': f'external_reference excede 64 caracteres: {len(external_ref)}'
        }, status=400)

    url = 'https://api.mercadopago.com/v1/orders'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Idempotency-Key': str(uuid.uuid4())
    }

    payload = {
        'type': 'point',
        'external_reference': external_ref,
        'expiration_time': expiration_time,
        'transactions': {
            'payments': [ { 'amount': f"{amount:.2f}" } ]
        },
        'config': {
            'point': {
                'terminal_id': terminal_id,
                'print_on_terminal': 'seller_ticket'
            },
            'payment_method': {
                'default_type': 'credit_card',
                'default_installments': installments,
                'installments_cost': 'seller'
            }
        },
        'description': f'Venda PDV #{sale.pk}'
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
    except Exception as e:
        return JsonResponse({'error': 'Erro ao conectar Mercado Pago: ' + str(e)}, status=500)

    try:
        data = resp.json()
    except Exception:
        return JsonResponse({'error': 'Resposta inválida do Mercado Pago', 'raw': resp.text}, status=502)

    if resp.status_code not in (200, 201):
        mp_message = data.get('message') or data.get('error') or str(data)
        return JsonResponse(
            {'error': f'MP API ({resp.status_code}): {mp_message}', 'details': data},
            status=resp.status_code,
        )

    mp_payment = (data.get('transactions', {}).get('payments') or [{}])[0]
    point_config = data.get('config', {}).get('point', {})

    GatewayPayment.objects.update_or_create(
        order_id=data.get('id', ''),
        defaults={
            'sale': sale,
            'provider': GatewayPayment.Provider.MERCADO_PAGO,
            'payment_id': mp_payment.get('id', ''),
            'external_reference': data.get('external_reference', ''),
            'terminal_id': point_config.get('terminal_id', ''),
            'amount': Decimal(str(mp_payment.get('amount', amount))).quantize(Decimal('0.01')),
            'status': data.get('status', ''),
            'status_detail': data.get('status_detail', ''),
            'raw_payload': data,
        },
    )

    # Retorna a resposta da API para uso no frontend e logs
    return JsonResponse({'success': True, 'order': data})


@require_POST
@login_required
def cancel_mp_order_view(request):
    """Cancela uma order do Mercado Pago via API. Recebe `order_id` em POST."""
    order_id = request.POST.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id é obrigatório'}, status=400)

    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        return JsonResponse({'error': 'ACCESS_TOKEN não configurado no ambiente.'}, status=500)

    url = f'https://api.mercadopago.com/v1/orders/{order_id}/cancel'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Idempotency-Key': str(uuid.uuid4())
    }

    try:
        resp = requests.post(url, headers=headers, timeout=10)
    except Exception as e:
        return JsonResponse({'error': 'Erro ao conectar Mercado Pago: ' + str(e)}, status=500)

    try:
        data = resp.json()
    except Exception:
        return JsonResponse({'error': 'Resposta inválida do Mercado Pago', 'raw': resp.text}, status=502)

    if resp.status_code not in (200, 201):
        mp_message = data.get('message') or data.get('error') or str(data)
        return JsonResponse(
            {'error': f'MP API ({resp.status_code}): {mp_message}', 'details': data},
            status=resp.status_code,
        )

    GatewayPayment.objects.filter(order_id=order_id).update(
        status=data.get('status', ''),
        status_detail=data.get('status_detail', ''),
        raw_payload=data,
        canceled_at=timezone.now(),
    )

    return JsonResponse({'success': True, 'order': data})


@login_required
def mp_order_status_view(request):
    """Consulta o status de uma order no MP e atualiza o registro local."""
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id é obrigatório'}, status=400)

    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        return JsonResponse({'error': 'ACCESS_TOKEN não configurado.'}, status=500)

    try:
        resp = requests.get(
            f'https://api.mercadopago.com/v1/orders/{order_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    GatewayPayment.objects.filter(order_id=order_id).update(
        status=data.get('status', ''),
        status_detail=data.get('status_detail', ''),
        raw_payload=data,
    )

    return JsonResponse({
        'status': data.get('status', ''),
        'status_detail': data.get('status_detail', ''),
    })


@require_POST
@login_required
def mp_simulate_view(request):
    """Simula o status de uma order no MP (apenas em modo DEBUG/teste)."""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Disponível apenas em ambiente de desenvolvimento.'}, status=403)

    order_id = request.POST.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id é obrigatório'}, status=400)

    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        return JsonResponse({'error': 'ACCESS_TOKEN não configurado.'}, status=500)

    status = request.POST.get('status', 'processed')
    payment_method_type = request.POST.get('payment_method_type', 'credit_card')

    payload = {'status': status}

    try:
        resp = requests.post(
            f'https://api.mercadopago.com/v1/orders/{order_id}/events',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Test-Scope': 'sandbox',
            },
            json=payload,
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if resp.status_code not in (200, 201):
        mp_message = data.get('message') or data.get('error') or str(data)
        return JsonResponse(
            {'error': f'MP API ({resp.status_code}): {mp_message}', 'details': data},
            status=resp.status_code,
        )

    return JsonResponse({'success': True, 'result': data})


@login_required
def mp_terminals_view(request):
    """Lista os terminais Point vinculados à conta."""
    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        return JsonResponse({'error': 'ACCESS_TOKEN não configurado.'}, status=500)

    try:
        resp = requests.get(
            'https://api.mercadopago.com/terminals/v1/list',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse(data, safe=False)


@csrf_exempt
def mp_webhook_view(request):
    """Recebe notificações do Mercado Pago e atualiza o GatewayPayment."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    topic = payload.get('type') or request.GET.get('topic', '')

    if topic == 'orders_v2':
        resource_id = payload.get('data', {}).get('id')
        access_token = os.environ.get('ACCESS_TOKEN')
        if resource_id and access_token:
            try:
                resp = requests.get(
                    f'https://api.mercadopago.com/v1/orders/{resource_id}',
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=10,
                )
                order_data = resp.json()
                GatewayPayment.objects.filter(order_id=resource_id).update(
                    status=order_data.get('status', ''),
                    status_detail=order_data.get('status_detail', ''),
                    raw_payload=order_data,
                )
            except Exception:
                pass

    return JsonResponse({'received': True})


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

class SaleListView(LoginRequiredMixin, ListView):
    """Lista o histórico de vendas concluídas."""
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        # Filtra apenas vendas concluídas (exclui rascunhos e canceladas se desejar)
        queryset = super().get_queryset().filter(status=Sale.Status.COMPLETED)
        
        query = self.request.GET.get('query')
        if query:
            # Permite buscar por ID da venda ou Nome do Cliente
            queryset = queryset.filter(
                Q(id__icontains=query) |
                Q(customer__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        return context


class SaleDetailView(LoginRequiredMixin, DetailView):
    """Exibe os detalhes completos de uma venda específica."""
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'


@login_required
def search_products_api(request):
    """Retorna lista de produtos para o autocomplete do PDV em JSON"""
    query = request.GET.get('term', '')
    results = []

    if len(query) > 2:
        # Adicionamos 'color' e 'size' no select_related para otimizar
        variations = ProductVariation.active.select_related('product', 'color', 'size').filter(
            Q(product__name__icontains=query) |
            Q(sku__icontains=query)
        )[:10]

        for v in variations:
            full_name = v.product.name
            
            # Monta os detalhes da variação (Cor e Tamanho)
            details = []
            
            # Verifica se a cor é relevante (diferente de N/A)
            if v.color and v.color.name.upper() != "N/A":
                details.append(v.color.name)
                
            # Verifica se o tamanho é relevante
            if v.size and v.size.name.upper() != "N/A":
                details.append(v.size.name)
            
            # Se tiver detalhes, adiciona ao nome (Ex: "Sutiã - Vermelho M")
            if details:
                full_name += f" - {' '.join(details)}"
            
            results.append({
                'label': full_name,
                'value': v.sku,
                'price': float(v.product.selling_price)
            })

    return JsonResponse(results, safe=False)


@require_POST
@login_required
def apply_discount_view(request):
    """Aplica desconto no total da venda"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    sale = Sale.objects.filter(status=Sale.Status.DRAFT, user=request.user).first()
    if not sale:
        if is_ajax:
            return JsonResponse({'error': 'Nenhuma venda em andamento.'}, status=404)
        messages.error(request, "Nenhuma venda em andamento.")
        return redirect("sales:pdv")

    discount_str = request.POST.get('discount_amount', '0').replace(',', '.').strip()

    try:
        discount = Decimal(discount_str) if discount_str else Decimal('0')

        if discount < Decimal('0'):
            msg = "O desconto não pode ser negativo."
            if is_ajax:
                return JsonResponse({'error': msg}, status=400)
            messages.error(request, msg)
            return redirect("sales:pdv")

        if discount > sale.gross_amount:
            msg = "O desconto não pode ser maior que o valor total da venda."
            if is_ajax:
                return JsonResponse({'error': msg}, status=400)
            messages.error(request, msg)
            return redirect("sales:pdv")

        sale.discount_amount = discount
        sale.save(update_fields=['discount_amount'])
        sale.calculate_totals()
        sale.refresh_from_db()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'gross_amount': float(sale.gross_amount),
                'discount_amount': float(sale.discount_amount),
                'net_amount': float(sale.net_amount),
                'remaining_balance': float(sale.remaining_balance),
            })

        messages.success(request, f"Desconto de R$ {discount:.2f} aplicado com sucesso!")
        
    except (ValueError, TypeError):
        messages.error(request, "Valor de desconto inválido.")

    return redirect("sales:pdv")


METHOD_DISPLAY = {
    "DINHEIRO": "Dinheiro",
    "CREDITO": "Cartão de Crédito",
    "DEBITO": "Cartão de Débito",
    "PIX": "PIX",
    "OUTROS": "Outros",
}


class SalesReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = "sales/report_sales.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = date.today()
        start_str = self.request.GET.get("start_date", today.replace(day=1).isoformat())
        end_str = self.request.GET.get("end_date", today.isoformat())

        try:
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
        except ValueError:
            start_date = today.replace(day=1)
            end_date = today

        if end_date < start_date:
            context.update(
                {
                    "date_error": "A data final não pode ser anterior à data inicial.",
                    "start_date": start_str,
                    "end_date": end_str,
                    "total_revenue": 0,
                    "total_discounts": 0,
                    "completed_sales_count": 0,
                    "top_items": [],
                    "payment_chart_json": "{}",
                    "user_chart_json": "{}",
                }
            )
            return context

        total_revenue = services.get_total_revenue(start_date, end_date)
        total_discounts = services.get_total_discounts(start_date, end_date)
        completed_sales_count = Sale.objects.filter(
            status=Sale.Status.COMPLETED,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        ).count()

        payment_qs = services.get_revenue_by_payment_method(start_date, end_date)
        payment_chart = {
            "labels": [METHOD_DISPLAY.get(p["method"], p["method"]) for p in payment_qs],
            "values": [float(p["total"]) for p in payment_qs],
        }

        user_qs = services.get_sales_by_user(start_date, end_date)
        user_chart = {"labels": [], "values": []}
        for u in user_qs:
            name = (
                f"{u['user__first_name']} {u['user__last_name']}".strip()
                or u["user__email"]
            )
            user_chart["labels"].append(name)
            user_chart["values"].append(float(u["total_revenue"]))

        context.update(
            {
                "total_revenue": total_revenue,
                "total_discounts": total_discounts,
                "completed_sales_count": completed_sales_count,
                "top_items": services.get_top_selling_items(start_date, end_date),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "payment_chart_json": json.dumps(payment_chart),
                "user_chart_json": json.dumps(user_chart),
            }
        )
        return context
