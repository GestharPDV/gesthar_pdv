# sales/urls.py
from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path(
        "cash-register-open/",
        views.CashRegisterOpenView.as_view(),
        name="cash-register-open",
    ),
    path("pdv/", views.PDVView.as_view(), name="pdv"),
]
