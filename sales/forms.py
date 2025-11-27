from django import forms
from django.core.exceptions import ValidationError
from product.models import ProductVariation
from customer.models import Customer
from .models import CashRegister, SalePayment


class AddItemForm(forms.Form):
    """
    Formulário para o PDV: Bipar produto e definir quantidade.
    """

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
        # Futuramente pode adicionar: OR barcode__exact=code
        variation = ProductVariation.objects.filter(
            sku__iexact=code, is_active=True, product__is_active=True
        ).first()

        if not variation:
            raise ValidationError(f"Produto não encontrado com o código '{code}'.")

        # Feedback imediato de estoque (UX)
        if variation.stock <= 0:
            raise ValidationError(f"O produto '{variation}' está sem estoque físico.")

        return variation


class IdentifyCustomerForm(forms.Form):
    """
    Formulário para vincular um cliente à venda via CPF/CNPJ.
    """

    cpf_cnpj = forms.CharField(
        label="CPF ou CNPJ do Cliente",
        max_length=18,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "CPF/CNPJ (somente números)",
                "id": "customer-search-input",
            }
        ),
    )

    def clean_cpf_cnpj(self):
        raw_value = self.cleaned_data["cpf_cnpj"]
        if not raw_value:
            return None

        # Remove caracteres não numéricos para busca flexível
        clean_value = "".join(filter(str.isdigit, raw_value))

        # Tenta buscar o cliente pelo CPF ou CNPJ limpo (contém)
        # Isso ajuda caso o usuário não digite a pontuação exata
        customer = Customer.objects.filter(cpf_cnpj__icontains=clean_value).first()

        if not customer:
            raise ValidationError("Cliente não encontrado com este CPF/CNPJ.")

        return customer


class OpenRegisterForm(forms.ModelForm):
    """
    Formulário para Abertura de Caixa.
    Captura apenas o fundo de troco inicial.
    """

    class Meta:
        model = CashRegister
        fields = ["opening_balance"]
        widgets = {
            "opening_balance": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            )
        }
        labels = {"opening_balance": "Fundo de Troco (R$)"}


class CloseRegisterForm(forms.ModelForm):
    """
    Formulário para Fechamento de Caixa.
    Captura o valor conferido na gaveta para auditoria.
    """

    class Meta:
        model = CashRegister
        fields = ["closing_balance"]
        widgets = {
            "closing_balance": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            )
        }
        labels = {"closing_balance": "Valor Conferido na Gaveta (R$)"}


class PaymentForm(forms.ModelForm):
    class Meta:
        model = SalePayment
        fields = ["method", "amount"]
        widgets = {
            "method": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "R$ 0,00",
                }
            ),
        }
        labels = {"method": "Forma de Pagamento", "amount": "Valor"}
