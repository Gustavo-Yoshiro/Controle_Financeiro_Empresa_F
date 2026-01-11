import re

def validar_cpf(cpf: str) -> bool:
    """
    Verifica se um CPF é válido seguindo o algoritmo oficial.
    Aceita com ou sem pontuação (pontos e traço).
    """
    if not cpf:
        return False

    # 1. Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)

    # 2. Verifica tamanho e se todos os dígitos são iguais (ex: 111.111.111-11 é inválido)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # 3. Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito_1 = 0 if resto == 10 else resto

    if digito_1 != int(cpf[9]):
        return False

    # 4. Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito_2 = 0 if resto == 10 else resto

    if digito_2 != int(cpf[10]):
        return False

    return True

def validar_telefone(telefone: str) -> bool:
    """Validação simples: verifica se tem entre 10 e 11 dígitos numéricos"""
    if not telefone: return False
    numeros = re.sub(r'[^0-9]', '', telefone)
    return 10 <= len(numeros) <= 11

def validar_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ verificando dígitos verificadores.
    Aceita formatado ou apenas números.
    """
    if not cnpj:
        return False

    # 1. Limpa
    cnpj = re.sub(r'[^0-9]', '', cnpj)

    # 2. Tamanho e invalidos conhecidos
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    # 3. Validação matemática
    def calcular_digito(cnpj_parcial, pesos):
        soma = 0
        for i, num in enumerate(cnpj_parcial):
            soma += int(num) * pesos[i]
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    # Pesos para o primeiro dígito
    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digito_1 = calcular_digito(cnpj[:12], pesos_1)

    if digito_1 != int(cnpj[12]):
        return False

    # Pesos para o segundo dígito
    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digito_2 = calcular_digito(cnpj[:13], pesos_2)

    if digito_2 != int(cnpj[13]):
        return False

    return True

import re

# ... (Mantenha validar_cpf, validar_telefone e validar_cnpj aqui) ...

def validar_email(email: str) -> bool:
    """
    Verifica se o formato do e-mail é válido (ex: nome@dominio.com).
    """
    if not email:
        return False
        
    # Regex padrão para validação de e-mail
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return re.match(padrao, email) is not None