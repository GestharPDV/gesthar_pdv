from decimal import Decimal, InvalidOperation
import hashlib
import hmac
import json
import os
import re
import time
import uuid
import logging

logger = logging.getLogger(__name__)
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
from django.http import JsonResponse, StreamingHttpResponse
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
    buyer_pays_fee = request.POST.get('buyer_pays_fee') == 'true'
    payment_method_type = request.POST.get('payment_method_type', 'CREDITO').upper()

    mp_type_map = {
        'CREDITO': 'credit_card',
        'DEBITO': 'debit_card',
        'PIX': 'qr',
    }
    mp_default_type = mp_type_map.get(payment_method_type, 'credit_card')

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

    if amount_decimal > sale.remaining_balance:
        return JsonResponse({
            'error': f'O valor não pode exceder o saldo restante de R$ {sale.remaining_balance:.2f}'
        }, status=400)

    if not sale.items.exists():
        return JsonResponse({'error': 'Venda sem itens não pode gerar order.'}, status=400)

    # Impede duplo clique: rejeita se já existe uma order ativa para esta venda
    active_statuses = ('pending', 'at_terminal', 'open')
    existing = GatewayPayment.objects.filter(sale=sale, status__in=active_statuses).first()
    if existing:
        logger.warning('Tentativa de criar order duplicada para venda %s (order ativa: %s, status: %s)',
                       sale.pk, existing.order_id, existing.status)
        return JsonResponse(
            {'error': 'Já existe uma cobrança ativa para esta venda. Cancele-a antes de criar uma nova.',
             'order_id': existing.order_id, 'status': existing.status},
            status=409,
        )

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
    idempotency_key = str(uuid.uuid4())

    payment_method_config = {'default_type': mp_default_type}
    if payment_method_type == 'CREDITO':
        payment_method_config['default_installments'] = installments
        payment_method_config['installments_cost'] = 'buyer' if buyer_pays_fee else 'seller'

    payload = {
        'type': 'point',
        'external_reference': external_ref,
        'expiration_time': expiration_time,
        'transactions': {
            'payments': [{'amount': f"{amount:.2f}"}]
        },
        'config': {
            'point': {
                'terminal_id': terminal_id,
                'print_on_terminal': 'seller_ticket'
            },
            'payment_method': payment_method_config,
        },
        'description': f'Venda PDV #{sale.pk}'
    }

    if sale.customer:
        c = sale.customer
        name_parts = c.name.strip().split(' ', 1)
        payer = {
            'email': c.email,
            'first_name': name_parts[0],
            'last_name': name_parts[1] if len(name_parts) > 1 else '',
        }
        doc = re.sub(r'\D', '', c.cpf_cnpj or '')
        if len(doc) == 11:
            payer['identification'] = {'type': 'CPF', 'number': doc}
        elif len(doc) == 14:
            payer['identification'] = {'type': 'CNPJ', 'number': doc}
        phone_digits = re.sub(r'\D', '', c.phone or '')
        if len(phone_digits) >= 10:
            payer['phone'] = {'area_code': phone_digits[:2], 'number': phone_digits[2:]}
        payload['payer'] = payer

    resp, err = _mp_request('POST', url, access_token=access_token,
                            headers={'Content-Type': 'application/json', 'X-Idempotency-Key': idempotency_key},
                            data=json.dumps(payload))
    if err:
        return JsonResponse({'error': 'Erro ao conectar Mercado Pago: ' + err}, status=500)

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
            'buyer_pays_fee': buyer_pays_fee,
            'installments': installments if installments > 1 else None,
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

    resp, err = _mp_request('POST', url, access_token=access_token,
                            headers={'Content-Type': 'application/json', 'X-Idempotency-Key': str(uuid.uuid4())})
    if err:
        return JsonResponse({'error': 'Erro ao conectar Mercado Pago: ' + err}, status=500)

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
    """Retorna o status atual da order lendo do banco local (atualizado pelo webhook)."""
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id é obrigatório'}, status=400)

    gp = GatewayPayment.objects.filter(order_id=order_id).values('status', 'status_detail').first()
    if not gp:
        return JsonResponse({'error': 'Order não encontrada.'}, status=404)

    return JsonResponse({
        'status': gp['status'],
        'status_detail': gp['status_detail'],
    })


@login_required
def mp_payment_stream_view(request):
    """SSE: mantém conexão aberta e envia evento quando o status da order mudar no banco."""
    order_id = request.GET.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id é obrigatório'}, status=400)

    def event_stream():
        access_token = os.environ.get('ACCESS_TOKEN')
        last_status = None
        elapsed = 0
        last_api_check = 0
        last_heartbeat = 0
        max_wait = 2700        # 45 minutos
        api_check_interval = 30  # consulta MP a cada 30s se banco não mudar
        heartbeat_interval = 15  # keepalive a cada 15s

        terminal_statuses = ('processed', 'paid', 'canceled', 'expired', 'failed')

        while elapsed < max_wait:
            try:
                gp = GatewayPayment.objects.filter(order_id=order_id).values('status', 'status_detail').first()
                if gp:
                    status = gp['status']

                    if status != last_status:
                        last_status = status
                        payload = json.dumps({'status': status, 'status_detail': gp['status_detail']})
                        yield f'data: {payload}\n\n'
                        last_heartbeat = elapsed

                    if status in terminal_statuses:
                        break

                    # Fallback: se o webhook não atualizou o banco, consulta o MP diretamente
                    if access_token and (elapsed - last_api_check) >= api_check_interval:
                        last_api_check = elapsed
                        try:
                            resp, err = _mp_request('GET', f'https://api.mercadopago.com/v1/orders/{order_id}',
                                                    access_token=access_token)
                            if not err and resp.status_code == 200:
                                api_data = resp.json()
                                api_status = api_data.get('status', '')
                                api_detail = api_data.get('status_detail', '')
                                if api_status and api_status != status:
                                    updates = {'status': api_status, 'status_detail': api_detail, 'raw_payload': api_data}
                                    if api_status in ('processed', 'paid'):
                                        mp_pmt = (api_data.get('transactions', {}).get('payments') or [{}])[0]
                                        pm = mp_pmt.get('payment_method', {})
                                        fee_list = mp_pmt.get('fee_details') or []
                                        total_fee = sum(float(f.get('amount', 0)) for f in fee_list)
                                        if pm.get('id'):
                                            updates['payment_method_id'] = pm['id']
                                        if pm.get('installments'):
                                            updates['installments'] = int(pm['installments'])
                                        if total_fee:
                                            updates['fee_amount'] = Decimal(str(total_fee)).quantize(Decimal('0.01'))
                                    GatewayPayment.objects.filter(order_id=order_id).update(**updates)
                                    logger.info('SSE fallback: order %s atualizada via API (%s → %s)', order_id, status, api_status)
                                    last_status = api_status
                                    yield f'data: {json.dumps({"status": api_status, "status_detail": api_detail})}\n\n'
                                    if api_status in terminal_statuses:
                                        return
                        except Exception:
                            pass

            except Exception:
                pass

            # Heartbeat para manter a conexão viva em proxies com idle timeout
            if (elapsed - last_heartbeat) >= heartbeat_interval:
                yield ': heartbeat\n\n'
                last_heartbeat = elapsed

            time.sleep(2)
            elapsed += 2

        logger.warning('SSE timeout: order %s sem resolução após %ds', order_id, max_wait)
        yield 'data: {"status": "timeout"}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


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
        data = resp.json() if resp.content else {}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if resp.status_code not in (200, 201, 204):
        mp_message = data.get('message') or data.get('error') or str(data)
        return JsonResponse(
            {'error': f'MP API ({resp.status_code}): {mp_message}', 'details': data},
            status=resp.status_code,
        )

    # Em desenvolvimento local o webhook não é chamado pelo MP.
    # Aguarda o MP processar e atualiza o banco diretamente para o SSE detectar.
    time.sleep(2)
    try:
        status_resp = requests.get(
            f'https://api.mercadopago.com/v1/orders/{order_id}',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        if status_resp.status_code == 200:
            sdata = status_resp.json()
            updates = {
                'status': sdata.get('status', ''),
                'status_detail': sdata.get('status_detail', ''),
                'raw_payload': sdata,
            }
            if sdata.get('status') in ('processed', 'paid'):
                mp_payment = (sdata.get('transactions', {}).get('payments') or [{}])[0]
                pm = mp_payment.get('payment_method', {})
                fee_list = mp_payment.get('fee_details') or []
                total_fee = sum(float(f.get('amount', 0)) for f in fee_list)
                if pm.get('id'):
                    updates['payment_method_id'] = pm['id']
                if pm.get('installments'):
                    updates['installments'] = int(pm['installments'])
                if total_fee:
                    updates['fee_amount'] = Decimal(str(total_fee)).quantize(Decimal('0.01'))
            GatewayPayment.objects.filter(order_id=order_id).update(**updates)
    except Exception:
        pass

    return JsonResponse({'success': True, 'result': data})


@login_required
def mp_installments_view(request):
    """Consulta opções de parcelamento com juros reais via MP API."""
    amount = request.GET.get('amount')
    if not amount:
        return JsonResponse({'error': 'amount é obrigatório'}, status=400)

    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        return JsonResponse({'error': 'ACCESS_TOKEN não configurado.'}, status=500)

    try:
        resp = requests.get(
            'https://api.mercadopago.com/v1/payment_methods/installments',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'amount': amount, 'payment_method_id': 'visa'},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if resp.status_code != 200:
        mp_message = data.get('message') or data.get('error') or str(data)
        return JsonResponse({'error': f'MP API ({resp.status_code}): {mp_message}'}, status=resp.status_code)

    payer_costs = []
    if data and isinstance(data, list) and data[0].get('payer_costs'):
        payer_costs = [
            {
                'installments': pc['installments'],
                'installment_rate': pc['installment_rate'],
                'installment_amount': float(pc['installment_amount']),
                'total_amount': float(pc['total_amount']),
            }
            for pc in data[0]['payer_costs']
            if pc['installments'] <= 6
        ]

    return JsonResponse({'payer_costs': payer_costs})


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


def _mp_request(method, url, *, access_token, max_retries=3, **kwargs):
    """Executa uma requisição à API do MP com retry automático em falhas de rede/timeout.

    Retorna (response, error_str). Se todas as tentativas falharem, error_str descreve o problema.
    """
    headers = kwargs.pop('headers', {})
    headers['Authorization'] = f'Bearer {access_token}'
    last_error = ''
    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, headers=headers, timeout=10, **kwargs)
            return resp, None
        except requests.Timeout:
            last_error = 'Timeout ao conectar Mercado Pago'
        except requests.ConnectionError:
            last_error = 'Erro de conexão com Mercado Pago'
        except Exception as e:
            last_error = str(e)
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # 1s, 2s
    logger.error('MP API falhou após %d tentativas: %s %s — %s', max_retries, method, url, last_error)
    return None, last_error


def _verify_mp_signature(request) -> bool:
    """Valida a assinatura HMAC-SHA256 enviada pelo Mercado Pago no header x-signature.

    Docs: https://www.mercadopago.com.br/developers/en/docs/your-integrations/notifications/webhooks
    Template: id:[data.id];request-id:[x-request-id];ts:[ts];

    Em desenvolvimento com ngrok, o ngrok substitui o header x-request-id pelo próprio UUID,
    quebrando a assinatura. Use MP_SKIP_WEBHOOK_SIGNATURE=True no .env para pular a verificação.
    """
    if os.environ.get('MP_SKIP_WEBHOOK_SIGNATURE', '').lower() in ('1', 'true', 'yes'):
        logger.warning('Webhook MP: verificação de assinatura DESABILITADA (MP_SKIP_WEBHOOK_SIGNATURE=True)')
        return True

    secret = os.environ.get('MP_WEBHOOK_SECRET', '').strip()
    if not secret:
        return False

    x_signature = request.headers.get('x-signature', '')
    x_request_id = request.headers.get('x-request-id', '')

    # Extrai ts e v1 do header: "ts=1234,v1=abcd..."
    ts = ''
    v1 = ''
    for part in x_signature.split(','):
        key, _, value = part.partition('=')
        if key.strip() == 'ts':
            ts = value.strip()
        elif key.strip() == 'v1':
            v1 = value.strip()

    if not ts or not v1:
        logger.warning('Webhook MP: x-signature sem ts/v1: %s', x_signature)
        return False

    # data.id vem como query param (ex: ?data.id=123)
    data_id = request.GET.get('data.id', '')

    parts = []
    if data_id:
        parts.append(f'id:{data_id}')
    if x_request_id:
        parts.append(f'request-id:{x_request_id}')
    if ts:
        parts.append(f'ts:{ts}')
    signed_template = ';'.join(parts) + ';'

    import binascii

    def _hmac(key_bytes, tpl):
        return hmac.new(key_bytes, tpl.encode('utf-8'), hashlib.sha256).hexdigest()

    # Dois templates possíveis: com e sem request-id (ngrok injeta X-Request-Id próprio)
    parts_with_rid = []
    parts_no_rid = []
    if data_id:
        parts_with_rid.append(f'id:{data_id}')
        parts_no_rid.append(f'id:{data_id}')
    if x_request_id:
        parts_with_rid.append(f'request-id:{x_request_id}')
    if ts:
        parts_with_rid.append(f'ts:{ts}')
        parts_no_rid.append(f'ts:{ts}')
    tpl_with_rid = ';'.join(parts_with_rid) + ';'
    tpl_no_rid   = ';'.join(parts_no_rid)   + ';'

    key_str = secret.encode('utf-8')
    try:
        key_hex = binascii.unhexlify(secret)
    except Exception:
        key_hex = None

    combos = [
        ('str+rid',    key_str, tpl_with_rid),
        ('str+no_rid', key_str, tpl_no_rid),
    ]
    if key_hex:
        combos += [
            ('hex+rid',    key_hex, tpl_with_rid),
            ('hex+no_rid', key_hex, tpl_no_rid),
        ]

    for name, key, tpl in combos:
        if hmac.compare_digest(_hmac(key, tpl), v1):
            logger.info('Webhook MP: assinatura válida via %s (template=%r)', name, tpl)
            return True

    logger.warning(
        'Webhook MP: nenhuma combinação bateu. v1=%s tpl_rid=%r tpl_no_rid=%r',
        v1, tpl_with_rid, tpl_no_rid,
    )
    return False


@csrf_exempt
def mp_webhook_view(request):
    """Recebe notificações do Mercado Pago e atualiza o GatewayPayment."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not _verify_mp_signature(request):
        logger.warning('Webhook MP rejeitado: assinatura inválida (ip=%s)', request.META.get('REMOTE_ADDR'))
        return JsonResponse({'error': 'Assinatura inválida'}, status=401)

    try:
        payload = json.loads(request.body)
    except Exception:
        logger.warning('Webhook MP rejeitado: JSON inválido')
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    topic = payload.get('type') or request.GET.get('topic', '')

    if topic in ('order', 'orders_v2'):
        order_data = payload.get('data', {})
        resource_id = order_data.get('id')

        if resource_id:
            # orders_v2 payload só contém {"id": "..."} — o status real vem da API
            access_token = os.environ.get('ACCESS_TOKEN')
            full_data = None
            if access_token:
                try:
                    resp = requests.get(
                        f'https://api.mercadopago.com/v1/orders/{resource_id}',
                        headers={'Authorization': f'Bearer {access_token}'},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        full_data = resp.json()
                except Exception as e:
                    logger.error('Webhook MP: falha ao buscar order %s: %s', resource_id, e)

            data_source = full_data or order_data
            new_status = data_source.get('status', '')

            if not new_status:
                logger.warning('Webhook MP: order %s sem status — ignorando atualização', resource_id)
            else:
                updates = {
                    'status': new_status,
                    'status_detail': data_source.get('status_detail', ''),
                    'raw_payload': payload,
                }

                if full_data:
                    full_payment = (full_data.get('transactions', {}).get('payments') or [{}])[0]
                    pm = full_payment.get('payment_method', {})
                    fee_list = full_payment.get('fee_details') or []
                    total_fee = sum(float(f.get('amount', 0)) for f in fee_list)
                    if full_payment.get('id'):
                        updates['payment_id'] = full_payment['id']
                    if pm.get('id'):
                        updates['payment_method_id'] = pm['id']
                    if pm.get('installments'):
                        updates['installments'] = int(pm['installments'])
                    if total_fee:
                        updates['fee_amount'] = Decimal(str(total_fee)).quantize(Decimal('0.01'))
                else:
                    mp_payment = (order_data.get('transactions', {}).get('payments') or [{}])[0]
                    if mp_payment.get('id'):
                        updates['payment_id'] = mp_payment['id']

                updated = GatewayPayment.objects.filter(order_id=resource_id).update(**updates)
                if updated:
                    logger.info('Webhook MP: order %s → %s', resource_id, new_status)
                else:
                    logger.warning('Webhook MP: order %s não encontrada no banco (status: %s)', resource_id, new_status)
    else:
        logger.info('Webhook MP: topic ignorado (%s)', topic)

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
