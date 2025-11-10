# sales/forms.py
from django import forms
from decimal import Decimal

# Classes do Tailwind CSS para estilização
# (Copiadas do seu 'product/forms.py' para manter a consistência)
TAILWIND_CLASSES = "w-full border border-gray-300 rounded-lg py-2 px-4 bg-white focus:outline-none focus:ring-2 focus:ring-rose-400"


class CashRegisterOpenForm(forms.Form):
    """
    Formulário para capturar o valor inicial de abertura do caixa.
    """

    initial_value = forms.DecimalField(
        label="Valor de Abertura (Troco)",
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        # Valor inicial padrão de 0.00
        initial=Decimal("0.00"),
        widget=forms.NumberInput(
            attrs={"step": "0.01", "placeholder": "R$ 0,00"}  # Permite centavos
        ),
        help_text="Informe o valor de troco inicial na gaveta.",
    )

    def __init__(self, *args, **kwargs):
        """
        Adiciona as classes Tailwind ao widget do campo.
        """
        super().__init__(*args, **kwargs)

        # Aplica a classe de estilização
        self.fields["initial_value"].widget.attrs["class"] = TAILWIND_CLASSES
