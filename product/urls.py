from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    # Product URLs
    path('list/', views.product_list_view, name='product-list'),
    path('create/', views.ProductCreateView.as_view(), name='product-create'),
    # Category URLs
    path('category/create', views.category_create_view, name='category-create'),
    # Supplier URLs
    path('supplier/create', views.supplier_create_view, name='supplier-create'),
]
