from django.contrib import admin
from .models import (
    Category,
    Color,
    Size,
    Supplier,
    Product,
    ProductImage,
    ProductSupplier,
    ProductVariation,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 3


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "selling_price", "is_active", "created_at"]
    list_filter = ["is_active", "category"]
    search_fields = ["name"]
    inlines = [ProductImageInline, ProductVariationInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


admin.site.register(ProductSupplier)
admin.site.register(ProductImage)
