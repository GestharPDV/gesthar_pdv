import json
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView, View

from . import services


# ---------------------------------------------------------------------------
# Helper compartilhado para montar o contexto do relatório
# ---------------------------------------------------------------------------

def _build_report_context(request) -> dict:
    """
    Extrai os filtros do request e devolve o contexto completo do relatório.
    Centralizado aqui para ser reutilizado pela view HTML e pela view PDF.
    """
    today = date.today()

    def parse_date(param: str, fallback: date) -> date:
        try:
            return date.fromisoformat(request.GET.get(param, ""))
        except (ValueError, TypeError):
            return fallback

    def parse_int(param: str):
        try:
            return int(request.GET[param])
        except (KeyError, ValueError, TypeError):
            return None

    start_date = parse_date("start_date", today - timedelta(days=30))
    end_date = parse_date("end_date", today)
    category_id = parse_int("category_id")

    category_data = services.get_quantity_by_category()
    color_data = services.get_quantity_by_color()

    return {
        "total_pieces": services.get_total_pieces(),
        "inventory_valuation": services.get_inventory_valuation(),
        "category_chart_json": json.dumps({
            "labels": list(category_data.keys()),
            "data": list(category_data.values()),
        }),
        "color_chart_json": json.dumps({
            "labels": list(color_data.keys()),
            "data": list(color_data.values()),
        }),
        "movements": services.get_inventory_movements(start_date, end_date),
        "low_stock_variations": services.get_low_stock_variations(),
        "categories": services.get_all_categories(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "selected_category_id": category_id,
    }


# ---------------------------------------------------------------------------
# View principal — renderiza o dashboard HTML
# ---------------------------------------------------------------------------

class StockReportView(LoginRequiredMixin, TemplateView):
    """Dashboard de Relatório de Estoque (RF016) — renderização HTML."""

    template_name = "stock/report_stock.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_build_report_context(self.request))
        return context


# ---------------------------------------------------------------------------
# View de exportação — gera e devolve o PDF pelo servidor (WeasyPrint)
# ---------------------------------------------------------------------------

class StockReportPDFView(LoginRequiredMixin, View):
    """
    Gera o relatório de estoque em PDF no servidor via WeasyPrint
    e devolve como resposta HTTP inline (abre em nova guia) ou attachment (download).

    Parâmetro GET opcional:
        download=1  → força download; omitido → abre no browser.
    """

    def get(self, request, *args, **kwargs):
        context = _build_report_context(request)
        html_string = render_to_string("stock/report_stock_pdf.html", context, request=request)
        force_download = request.GET.get("download") == "1"

        try:
            from weasyprint import HTML
            pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
            disposition = "attachment" if force_download else "inline"
            response = HttpResponse(pdf_file, content_type="application/pdf")
            response["Content-Disposition"] = f'{ disposition}; filename="relatorio_estoque.pdf"'
            return response
        except (ImportError, OSError):
            if force_download:
                html_string = html_string.replace(
                    "</body>",
                    "<script>window.addEventListener('load',function(){window.print();});</script></body>",
                )
            return HttpResponse(html_string, content_type="text/html; charset=utf-8")
