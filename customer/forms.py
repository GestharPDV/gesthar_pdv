from django import forms
from django.forms import inlineformset_factory
from .models import Customer, Address


class CustomerForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de clientes.
    """
    
    class Meta:
        model = Customer
        fields = [
            'name',
            'cpf_cnpj',
            'birth_date',
            'email',
            'phone',
            'baby_due_date',
            'size_preferences',
            'note'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do cliente'
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00 ou 00.000.000/0000-00'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'baby_due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'size_preferences': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: P, M, G'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais sobre o cliente'
            })
        }

    def clean_cpf_cnpj(self):
        """
        Remove caracteres não numéricos do CPF/CNPJ antes de validar.
        """
        import re
        cpf_cnpj = self.cleaned_data.get('cpf_cnpj', '')
        # Remove pontos, traços e barras
        cpf_cnpj_limpo = re.sub(r'[^0-9]', '', cpf_cnpj)
        return cpf_cnpj_limpo

    def clean_phone(self):
        """
        Remove caracteres especiais do telefone.
        """
        import re
        phone = self.cleaned_data.get('phone', '')
        if phone:
            # Remove tudo exceto números
            phone_limpo = re.sub(r'[^0-9]', '', phone)
            return phone_limpo
        return phone


class AddressForm(forms.ModelForm):
    """
    Formulário para endereços.
    """
    
    class Meta:
        model = Address
        fields = ['cep', 'state', 'city', 'neighborhood', 'street', 'number', 'complement']
        widgets = {
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00000-000'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: PI'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da cidade'
            }),
            'neighborhood': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do bairro'
            }),
            'street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da rua'
            }),
            'number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'complement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apto, bloco, etc (opcional)'
            })
        }

    def clean_cep(self):
        """
        Remove caracteres não numéricos do CEP.
        """
        import re
        cep = self.cleaned_data.get('cep', '')
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        return cep_limpo


# Formset para gerenciar múltiplos endereços inline
AddressFormSet = inlineformset_factory(
    Customer,
    Address,
    form=AddressForm,
    extra=1,  # Número de formulários vazios extras
    can_delete=True,  # Permite deletar endereços
    min_num=1,  # Pelo menos um endereço é obrigatório
    validate_min=True
)

