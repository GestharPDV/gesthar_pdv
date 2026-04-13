from django.urls import path
from . import views

app_name = "stock"

urlpatterns = [
    path("relatorios/estoque/", views.StockReportView.as_view(), name="report-stock"),
    path("relatorios/estoque/pdf/", views.StockReportPDFView.as_view(), name="report-stock-pdf"),
]
