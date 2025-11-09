from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('global.urls')),
    path('', include('user.urls')),
    path('products/', include('product.urls')),
    path('user/', include('user.urls')),
]
