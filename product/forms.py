from django import forms
from django.forms import (
    ModelForm,
    Textarea,
    inlineformset_factory,
    BaseInlineFormSet,
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

# Classes do Tailwind CSS para estilização dos campos do formulário
TAILWIND_CLASSES = "w-full border border-gray-300 rounded-lg py-2 px-4 bg-white focus:outline-none focus:ring-2 focus:ring-rose-400"

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
            "description": Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.filter(is_active=True)

        for field_name, field in self.fields.items():
            # Pulamos checkboxes, pois eles são estilizados de forma diferente no HTML
            if field.widget.__class__.__name__ == "CheckboxInput":
                continue

            # Aplicamos as classes do Tailwind a todos os outros
            field.widget.attrs["class"] = TAILWIND_CLASSES


class ProductSupplierForm(ModelForm):
    class Meta:
        model = ProductSupplier
        fields = ["supplier", "cost_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lógica de Negócio
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True)

        # Lógica de Estilização
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == "CheckboxInput":
                continue
            field.widget.attrs["class"] = TAILWIND_CLASSES


class ProductVariationForm(ModelForm):
    class Meta:
        model = ProductVariation
        fields = ["color", "size", "minimum_stock", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lógica de Negócio
        self.fields["color"].queryset = Color.objects.all()
        self.fields["size"].queryset = Size.objects.filter(is_active=True)

        # Lógica de Estilização
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == "CheckboxInput":
                continue
            field.widget.attrs["class"] = TAILWIND_CLASSES


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
                    form.add_error(
                        None,
                        "Variações duplicadas (mesma cor e tamanho) não são permitidas.",
                    )
                variations_exist.add(variation_tuple)


# Formsets para gerenciar múltiplos fornecedores e variações de produtos
ProductSupplierFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductSupplier,
    form=ProductSupplierForm,
    extra=0,
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
