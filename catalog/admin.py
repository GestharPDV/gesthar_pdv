from django.contrib import admin
from .models import CatalogConfig


@admin.register(CatalogConfig)
class CatalogConfigAdmin(admin.ModelAdmin):
    list_display = ["company_name", "whatsapp_number", "instagram_url", "catalog_visible", "updated_at"]
    list_filter = ["catalog_visible"]
