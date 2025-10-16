# from django import forms
from django.forms import (
    ModelForm,
    Widget,
    inlineformset_factory,
    BaseInlineFormSet,
    add_error,
)
from .models import (
    Product,
    ProductSupplier,
    ProductVariation,
    Category,
    Supplier,
    Color,
    Size,
)


# Formulário para o modelo Product
class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "selling_price",
            "category",
            "is_active",
            "has_variation",
        ]
        widgets = {
            "description": Widget(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.filter(is_active=True)

        # Adiciona classe CSS para estilização a todfos os campos
        for _field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class ProductSupplierForm(ModelForm):
    class Meta:
        model = ProductSupplier
        fields = ["supplier", "cost_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True)

        for _field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class ProductVariationForm(ModelForm):
    class Meta:
        model = ProductVariation
        fields = ["color", "size", "minimum_stock", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["color"].queryset = Color.objects.all()
        self.fields["size"].queryset = Size.objects.filter(is_active=True)

        for _field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class BaseProductVariationInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        variations_exist = set()

        for form in self.forms:

            if not form.is_valid() or form.cleaned_data.get("DELETE", False):
                continue

            color = form.cleaned_data.get("color")
            size = form.cleaned_data.get("size")
            if color and size:
                variation_tuple = (color, size)

                if variation_tuple in variations_exist:
                    add_error(None, "Variações duplicadas não são permitidas.")

                variations_exist.add(variation_tuple)


# Formsets para gerenciar múltiplos fornecedores e variações de produtos
ProductSupplierFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductSupplier,
    form=ProductSupplierForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

ProductVariationFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductVariation,
    form=ProductVariationForm,
    formset=BaseProductVariationInlineFormSet,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
