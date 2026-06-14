from django import forms
from django.forms import (
    ModelForm,
    Textarea,
    inlineformset_factory,
    BaseInlineFormSet,
)
from .models import (
    Product,
    ProductImage,
    ProductSupplier,
    ProductVariation,
    Category,
    Supplier,
    Color,
    Size,
)

def _apply_bootstrap_classes(fields):
    for field in fields.values():
        widget = field.widget.__class__.__name__
        if widget == "CheckboxInput":
            continue
        if "Select" in widget:
            field.widget.attrs["class"] = "form-select"
        else:
            field.widget.attrs["class"] = "form-control"


# Formulário para o modelo Product
class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "selling_price",
            "category",
            "cover_image",
            "is_active",
        ]
        widgets = {
            "description": Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        _apply_bootstrap_classes(self.fields)
        self.fields["cover_image"].required = False
        self.fields["cover_image"].widget.attrs.update({
            "accept": "image/*",
            "class": "form-control",
        })

        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ("CheckboxInput", "ClearableFileInput"):
                continue
            field.widget.attrs["class"] = TAILWIND_CLASSES
        _apply_bootstrap_classes(self.fields)


class ProductImageForm(ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = False
        self.fields["image"].widget.attrs.update({
            "accept": "image/*",
            "class": "form-control form-control-sm",
        })


class ProductSupplierForm(ModelForm):
    class Meta:
        model = ProductSupplier
        fields = ["supplier", "cost_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True)
        _apply_bootstrap_classes(self.fields)


class ProductVariationForm(ModelForm):
    class Meta:
        model = ProductVariation
        fields = ["color", "size", "stock","minimum_stock", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["color"].queryset = Color.objects.all()
        self.fields["size"].queryset = Size.objects.filter(is_active=True)
        _apply_bootstrap_classes(self.fields)


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
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

ProductImageFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductImage,
    form=ProductImageForm,
    extra=3,
    max_num=3,
    can_delete=True,
)
