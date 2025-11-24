from django import forms
from django.core.exceptions import ValidationError
from product.models import ProductVariation


class AddItemForm(forms.Form):
    # O campo aceita texto para permitir leitura de código de barras ou digitação manual
    sku_or_barcode = forms.CharField(
        label="Código / SKU",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Bipe o código ou digite o SKU...",
                "autofocus": "autofocus",
            }
        ),
    )
    quantity = forms.IntegerField(
        label="Qtd",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-lg", "style": "width: 100px;"}
        ),
    )

    def clean_sku_or_barcode(self):
        code = self.cleaned_data["sku_or_barcode"]

        # Tenta buscar exato pelo SKU (case insensitive)
        # Futuramente: OR barcode__exact=code
        variation = ProductVariation.objects.filter(
            sku__iexact=code, is_active=True, product__is_active=True
        ).first()

        if not variation:
            raise ValidationError(f"Produto não encontrado com o código '{code}'.")

        # Feedback imediato de estoque (UX)
        if variation.stock <= 0:
            raise ValidationError(f"O produto '{variation}' está sem estoque físico.")

        return variation
