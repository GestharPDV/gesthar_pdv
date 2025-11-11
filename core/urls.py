from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("global.urls")),
    path("products/", include("product.urls")),
    path("user/", include("user.urls")),
    path("accounts/", include("accounts.urls")),
    path('clientes/', include('customer.urls')),
]
