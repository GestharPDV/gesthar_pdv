from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    # Abertura e Fechamento de Caixa
    path("open-register/", views.open_register_view, name="open-register"),
    path("close-register/", views.close_register_view, name="close-register"),
    # Tela Principal do PDV
    path("pdv/", views.pdv_view, name="pdv"),
    # Ações do Carrinho (POST only)
    path("add-item/", views.add_item_view, name="add-item"),
    path("identify-customer/", views.identify_customer_view, name="identify-customer"),
    path("add-payment/", views.add_payment_view, name="add-payment"),
    path(
        "remove-payment/<int:payment_id>/",
        views.remove_payment_view,
        name="remove-payment",
    ),
    path("remove-item/<int:item_id>/", views.remove_item_view, name="remove-item"),
    path("apply-discount/", views.apply_discount_view, name="apply-discount"),
    # Ações da Venda (POST only)
    path("complete/<int:sale_id>/", views.complete_sale_view, name="complete-sale"),
    # path('cancel/<int:sale_id>/', views.cancel_sale_view, name='cancel-sale'), # Futuro
    path('list/', views.SaleListView.as_view(), name='sale-list'),
    path('detail/<int:pk>/', views.SaleDetailView.as_view(), name='sale-detail'),
    path('api/search-products/', views.search_products_api, name='api-search-products'),
    path('relatorios/vendas/', views.SalesReportView.as_view(), name='report-sales'),
    # Mercado Pago Point
    path('mp/create-order/', views.create_mp_order_view, name='mp-create-order'),
    path('mp/cancel-order/', views.cancel_mp_order_view, name='mp-cancel-order'),
    path('mp/order-status/', views.mp_order_status_view, name='mp-order-status'),
    path('mp/simulate/', views.mp_simulate_view, name='mp-simulate'),
    path('mp/terminals/', views.mp_terminals_view, name='mp-terminals'),
    path('mp/webhook/', views.mp_webhook_view, name='mp-webhook'),
    path('mp/installments/', views.mp_installments_view, name='mp-installments'),
]
