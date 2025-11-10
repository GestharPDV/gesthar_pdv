# sales/urls.py
from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path(
        "open-cash-register/",
        views.CashRegisterOpenView.as_view(),
        name="open_cash_register",
    ),
]
