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
    # Identificar Cliente na Venda
    path("identify-customer/", views.identify_customer_view, name="identify-customer"),
    # Ações da Venda (POST only)
    path("complete/<int:sale_id>/", views.complete_sale_view, name="complete-sale"),
    # path('cancel/<int:sale_id>/', views.cancel_sale_view, name='cancel-sale'), # Futuro
]
