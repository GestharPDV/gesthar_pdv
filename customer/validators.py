from django.core.exceptions import ValidationError
import re


def validate_cpf_cnpj(value):
    """
    Valida CPF ou CNPJ.
    Aceita formatos com ou sem máscara.
    """
    # Remove caracteres não numéricos
    value = re.sub(r'[^0-9]', '', value)
    
    # Verifica se é CPF (11 dígitos) ou CNPJ (14 dígitos)
    if len(value) == 11:
        return validate_cpf(value)
    elif len(value) == 14:
        return validate_cnpj(value)
    else:
        raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')


def validate_cpf(cpf):
    """
    Valida um CPF.
    """
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')
    
    # Verifica se todos os dígitos são iguais (CPF inválido)
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    # Calcula o primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        raise ValidationError('CPF inválido.')
    
    # Calcula o segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[10]) != digito2:
        raise ValidationError('CPF inválido.')
    
    return cpf


def validate_cnpj(cnpj):
    """
    Valida um CNPJ.
    """
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        raise ValidationError('CNPJ deve ter 14 dígitos.')
    
    # Verifica se todos os dígitos são iguais (CNPJ inválido)
    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')
    
    # Calcula o primeiro dígito verificador
    multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        raise ValidationError('CNPJ inválido.')
    
    # Calcula o segundo dígito verificador
    multiplicadores2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[13]) != digito2:
        raise ValidationError('CNPJ inválido.')
    
    return cnpj

