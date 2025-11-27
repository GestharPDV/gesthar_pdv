from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='customer_list'),
    path('novo/', views.CustomerCreateView.as_view(), name='customer-create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('<int:pk>/editar/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('<int:pk>/deletar/', views.CustomerDeleteView.as_view(), name='customer_delete'),
]

