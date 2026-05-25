from django.contrib import admin
from .models import GatewayPayment


@admin.register(GatewayPayment)
class GatewayPaymentAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"provider",
		"order_id",
		"payment_id",
		"sale",
		"amount",
		"fee_amount",
		"payment_method_id",
		"installments",
		"buyer_pays_fee",
		"status",
		"updated_at",
	)
	search_fields = ("order_id", "payment_id", "external_reference", "terminal_id")
	list_filter = ("provider", "status", "buyer_pays_fee", "created_at")
