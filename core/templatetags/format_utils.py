"""
Template tags para formatação de documentos (CPF, CNPJ, Telefone).
Uso nos templates:
    {% load format_utils %}
    {{ cliente.cpf|format_cpf }}
    {{ cliente.cnpj|format_cnpj }}
    {{ cliente.telefone|format_telefone }}
"""
from django import template

register = template.Library()


@register.filter(name='format_cpf')
def format_cpf(value):
    """
    Formata um CPF de 11 dígitos para o padrão 000.000.000-00
    Entrada: 12345678900
    Saída: 123.456.789-00
    """
    if not value:
        return ''
    
    # Remove qualquer caractere não numérico
    cpf = ''.join(filter(str.isdigit, str(value)))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return value  # Retorna original se não tiver tamanho correto
    
    # Formata: 000.000.000-00
    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'


@register.filter(name='format_cnpj')
def format_cnpj(value):
    """
    Formata um CNPJ de 14 dígitos para o padrão 00.000.000/0000-00
    Entrada: 12345678000199
    Saída: 12.345.678/0001-99
    """
    if not value:
        return ''
    
    # Remove qualquer caractere não numérico
    cnpj = ''.join(filter(str.isdigit, str(value)))
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return value  # Retorna original se não tiver tamanho correto
    
    # Formata: 00.000.000/0000-00
    return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'


@register.filter(name='format_telefone')
def format_telefone(value):
    """
    Formata telefone para os padrões:
    - 10 dígitos: (00) 0000-0000
    - 11 dígitos: (00) 00000-0000
    """
    if not value:
        return ''
    
    # Remove qualquer caractere não numérico
    tel = ''.join(filter(str.isdigit, str(value)))
    
    if len(tel) == 10:
        # Telefone fixo: (00) 0000-0000
        return f'({tel[:2]}) {tel[2:6]}-{tel[6:]}'
    elif len(tel) == 11:
        # Celular: (00) 00000-0000
        return f'({tel[:2]}) {tel[2:7]}-{tel[7:]}'
    else:
        return value  # Retorna original se não reconhecer o formato


@register.filter(name='format_documento')
def format_documento(value, tipo):
    """
    Formata documento baseado no tipo (CPF ou CNPJ).
    Uso: {{ cliente.cpf|format_documento:"cpf" }}
    """
    if tipo == 'cpf':
        return format_cpf(value)
    elif tipo == 'cnpj':
        return format_cnpj(value)
    return value

