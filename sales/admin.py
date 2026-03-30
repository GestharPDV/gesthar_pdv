from django.contrib import admin

from .models import SaleGateway


@admin.register(SaleGateway)
class SaleGatewayAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"sale",
		"metodo",
		"charge_id",
		"provider_payment_id",
		"data_vencimento",
		"gerado_em",
	)
	search_fields = ("charge_id", "provider_payment_id", "sale__id")
	list_filter = ("metodo", "gerado_em")
