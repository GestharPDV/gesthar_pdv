from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Tela Principal do PDV
    path('pdv/', views.pdv_view, name='pdv'),

    # Ações do Carrinho (POST only)
    path('add-item/', views.add_item_view, name='add-item'),
    path('remove-item/<int:item_id>/', views.remove_item_view, name='remove-item'),
    
    # Ações da Venda (POST only)
    path('complete/<int:sale_id>/', views.complete_sale_view, name='complete-sale'),
    # path('cancel/<int:sale_id>/', views.cancel_sale_view, name='cancel-sale'), # Futuro
]
