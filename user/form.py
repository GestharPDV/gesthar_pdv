from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from .models import UserGesthar
import re
from datetime import date, timedelta

def validar_cpf(cpf):
    """
    Função auxiliar para validar CPF (algoritmo padrão de 11 dígitos).
    """
    cpf = re.sub(r'[^0-9]', '', cpf)

    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * len(cpf):
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[9]):
        return False

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[10]):
        return False

    return True


class UserGestharChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = UserGesthar
        fields = [
            "first_name",
            "last_name",
            "email",
            "cpf",
            "phone_number",
            "hire_date",
            "birth_date",
            "role",
            "notes",
            "exit_date",
            "is_active",
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'exit_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00', 'maxlength': '14', 'pattern': r'\d{3}\.\d{3}\.\d{3}-\d{2}'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000', 'maxlength': '15', 'pattern': r'\(\d{2}\) \d{4,5}-\d{4}'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

        # Adicionar validações frontend
        today = date.today()
        min_birth_date = today.replace(year=today.year - 110)
        self.fields['birth_date'].widget.attrs.update({
            'min': min_birth_date.strftime('%Y-%m-%d'),
            'max': today.strftime('%Y-%m-%d'),
            'required': 'required'
        })
        self.fields['hire_date'].widget.attrs['required'] = 'required'
        self.fields['email'].widget.attrs['required'] = 'required'
        self.fields['cpf'].widget.attrs['required'] = 'required'
        self.fields['role'].widget.attrs['required'] = 'required'

        if self.instance and self.instance.pk:

            if self.initial.get('cpf'):
                raw_cpf = str(self.initial['cpf'])
                if len(raw_cpf) == 11:
                    self.initial['cpf'] = f"{raw_cpf[:3]}.{raw_cpf[3:6]}.{raw_cpf[6:9]}-{raw_cpf[9:]}"

            if self.initial.get('phone_number'):
                raw_phone = str(self.initial['phone_number'])
                if len(raw_phone) == 11:
                    self.initial['phone_number'] = f"({raw_phone[:2]}) {raw_phone[2:7]}-{raw_phone[7:]}"
                elif len(raw_phone) == 10:
                    self.initial['phone_number'] = f"({raw_phone[:2]}) {raw_phone[2:6]}-{raw_phone[6:]}"

            for date_field in ['birth_date', 'hire_date', 'exit_date']:
                val = self.initial.get(date_field)
                if val:
                    self.initial[date_field] = val.strftime('%Y-%m-%d')

    def clean(self):
        """Validação cruzada entre campos"""
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hire_date')
        exit_date = cleaned_data.get('exit_date')
        birth_date = cleaned_data.get('birth_date')

        # 1. Validação: Data de Saída não pode ser anterior à Data de Admissão
        if hire_date and exit_date:
            if exit_date < hire_date:
                self.add_error('exit_date', "A data de saída não pode ser anterior à data de admissão.")

        # 2. Validações relacionadas a Nascimento e Admissão
        if birth_date and hire_date:
            # Verifica cronologia básica primeiro
            if hire_date < birth_date:
                self.add_error('hire_date', "A data de admissão não pode ser anterior à data de nascimento.")
            
            # Só verifica a idade mínima se a cronologia estiver correta (else)
            else:
                # 3. Validação de Idade Mínima para contratação
                # Calcula a idade na data da contratação
                age_at_hire = hire_date.year - birth_date.year - ((hire_date.month, hire_date.day) < (birth_date.month, birth_date.day))
                
                if age_at_hire < 14:
                    self.add_error('hire_date', f"Idade inválida para contratação. A idade mínima é 14 anos completos.")
        
        return cleaned_data

    def clean_cpf(self):
        """Valida e limpa o campo CPF"""
        cpf = self.cleaned_data.get('cpf', '')
        cpf_limpo = re.sub(r'[^0-9]', '', cpf)

        if not cpf_limpo:
            raise ValidationError("O campo CPF é obrigatório.")

        if len(cpf_limpo) != 11:
            raise ValidationError("O CPF deve conter exatamente 11 dígitos.")

        if not validar_cpf(cpf_limpo):
            raise ValidationError("Número de CPF inválido.")

        return cpf_limpo

    def clean_birth_date(self):
        """Valida a data de nascimento para não ser anterior a 110 anos"""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            min_birth_date = date.today().replace(year=date.today().year - 110)
            if birth_date < min_birth_date:
                raise ValidationError("A data de nascimento não pode ser anterior a 110 anos da data atual.")
        return birth_date

    def clean_phone_number(self):
        """Valida e limpa o telefone"""
        phone = self.cleaned_data.get('phone_number', '')
        if phone:
            phone_limpo = re.sub(r'[^0-9]', '', phone)

            if len(phone_limpo) < 10 or len(phone_limpo) > 11:
                 raise ValidationError("O telefone deve ter 10 ou 11 dígitos (com DDD).")

            return phone_limpo

        return phone
