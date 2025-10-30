from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    # Product URLs
    path('list/', views.product_list_view, name='product-list'),
    path('detail/<int:pk>/', views.product_detail_view, name='product-detail'),
    path('create/', views.ProductCreateView.as_view(), name='product-create'),
    path('update/<int:pk>/', views.ProductUpdateView.as_view(), name='product-update'),
    # Category URLs
    path('category/create', views.category_create_view, name='category-create'),
    # Supplier URLs
    path('supplier/create', views.supplier_create_view, name='supplier-create'),
    # Color URLs
    path('color/create', views.color_create_view, name='color-create'),
    # Size URLs
    path('size/create', views.size_create_view, name='size-create'),
]
