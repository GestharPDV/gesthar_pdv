from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.CatalogListView.as_view(), name="catalog-list"),
    path("api/product/<int:product_id>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("api/search/", views.SearchProductsView.as_view(), name="search-products"),
    path("api/filter/", views.FilterProductsView.as_view(), name="filter-products"),
    path("api/whatsapp-redirect/", views.WhatsAppRedirectView.as_view(), name="whatsapp-redirect"),
]
