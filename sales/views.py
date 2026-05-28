from decimal import Decimal, InvalidOperation
import json
from datetime import date

from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from user.permissions import AdminRequiredMixin
from . import services

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


# ---------------------------------------------------------------------------
# Helpers de contexto — reutilizados pelas views HTML e PDF
# ---------------------------------------------------------------------------

def _build_sales_report_context(request) -> dict:
    today = date.today()
    start_str = request.GET.get("start_date", today.replace(day=1).isoformat())
    end_str = request.GET.get("end_date", today.isoformat())

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        start_date = today.replace(day=1)
        end_date = today

    if end_date < start_date:
        return {
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

    return {
        "total_revenue": total_revenue,
        "total_discounts": total_discounts,
        "completed_sales_count": completed_sales_count,
        "top_items": services.get_top_selling_items(start_date, end_date),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "payment_chart_json": json.dumps(payment_chart),
        "user_chart_json": json.dumps(user_chart),
    }


def _build_financial_context(request) -> dict:
    today = date.today()
    start_str = request.GET.get("start_date", today.replace(day=1).isoformat())
    end_str = request.GET.get("end_date", today.isoformat())

    capital_imobilizado = services.get_capital_imobilizado()
    stockout_alerts = services.get_stockout_risk_list()

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        start_date = today.replace(day=1)
        end_date = today

    if end_date < start_date:
        return {
            "date_error": "A data final não pode ser anterior à data inicial.",
            "start_date": start_str,
            "end_date": end_str,
            "gross_revenue": 0,
            "net_revenue": 0,
            "total_discounts": 0,
            "cmv": 0,
            "gross_profit": 0,
            "profit_margin": 0,
            "average_ticket": 0,
            "gmroi": 0,
            "capital_imobilizado": capital_imobilizado,
            "stockout_alerts": stockout_alerts,
            "abc_curve": [],
            "payment_methods_json": "{}",
            "sales_evolution_json": "{}",
        }

    indicators = services.get_financial_indicators(start_date, end_date)
    average_ticket = services.get_average_ticket(start_date, end_date)
    gmroi = services.get_gmroi(start_date, end_date)

    payment_qs = services.get_revenue_by_payment_method(start_date, end_date)
    payment_chart = {
        "labels": [METHOD_DISPLAY.get(p["method"], p["method"]) for p in payment_qs],
        "values": [float(p["total"]) for p in payment_qs],
    }

    evolution_qs = services.get_sales_evolution(start_date, end_date)
    sales_evolution = {
        "labels": [str(d["sale_date"]) for d in evolution_qs],
        "values": [float(d["daily_revenue"]) for d in evolution_qs],
    }

    abc_data = []
    for item in services.get_abc_curve(start_date, end_date):
        avg_cost = item["avg_unit_cost"] or 0
        total_cost = avg_cost * item["total_quantity"]
        total_revenue = item["total_revenue"] or 0
        profit = total_revenue - total_cost
        margin_pct = (profit / total_revenue * 100) if total_revenue > 0 else 0
        abc_data.append({
            "product_id": item["variation__product"],
            "name": item["variation__product__name"],
            "total_quantity": item["total_quantity"],
            "total_revenue": total_revenue,
            "profit_margin": margin_pct,
        })

    if abc_data:
        product_ids = [it["product_id"] for it in abc_data]
        coverage_map = services.get_bulk_stock_coverage(product_ids)
        for it in abc_data:
            cov = coverage_map.get(it["product_id"], {})
            it["days_coverage"] = cov.get("days_coverage")
            it["current_stock"] = cov.get("current_stock", 0)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "gross_revenue": indicators["gross_revenue"],
        "net_revenue": indicators["net_revenue"],
        "total_discounts": indicators["total_discounts"],
        "cmv": indicators["cmv"],
        "gross_profit": indicators["gross_profit"],
        "profit_margin": indicators["profit_margin"],
        "average_ticket": average_ticket,
        "gmroi": gmroi,
        "capital_imobilizado": capital_imobilizado,
        "stockout_alerts": stockout_alerts,
        "abc_curve": abc_data,
        "payment_methods_json": json.dumps(payment_chart),
        "sales_evolution_json": json.dumps(sales_evolution),
    }


# ---------------------------------------------------------------------------
# Views HTML
# ---------------------------------------------------------------------------

class FinancialDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = "sales/report_financial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_build_financial_context(self.request))
        return context


class SalesReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = "sales/report_sales.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_build_sales_report_context(self.request))
        return context


# ---------------------------------------------------------------------------
# Views PDF — geram o arquivo no servidor via WeasyPrint
# ---------------------------------------------------------------------------

def _weasyprint_response(html_string, request, filename, force_download):
    try:
        from weasyprint import HTML
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
        disposition = "attachment" if force_download else "inline"
        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        return response
    except (ImportError, OSError):
        # Fallback: entrega o HTML para impressão nativa do browser.
        # Com ?download=1 dispara window.print() automaticamente — o browser
        # oferece "Salvar como PDF" sem nenhuma dependência de sistema.
        if force_download:
            html_string = html_string.replace(
                "</body>",
                "<script>window.addEventListener('load',function(){window.print();});</script></body>",
            )
        return HttpResponse(html_string, content_type="text/html; charset=utf-8")


class SalesReportPDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = _build_sales_report_context(request)
        html_string = render_to_string("sales/report_sales_pdf.html", context, request=request)
        return _weasyprint_response(
            html_string, request,
            filename="relatorio_vendas.pdf",
            force_download=request.GET.get("download") == "1",
        )


class FinancialDashboardPDFView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = _build_financial_context(request)
        html_string = render_to_string("sales/report_financial_pdf.html", context, request=request)
        return _weasyprint_response(
            html_string, request,
            filename="relatorio_financeiro.pdf",
            force_download=request.GET.get("download") == "1",
        )
