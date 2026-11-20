"""Validação de dados de entrada, num lugar só.

Cadastro de clientes, importação de planilha e usuários usam estas
funções; nenhuma outra parte do sistema deve ter sua própria cópia.
"""
import re

_RE_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
TAMANHO_MAXIMO_EMAIL = 254


def somente_digitos(valor):
    """Remove tudo que não for dígito. None vira string vazia."""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


def _digito_cpf(numeros, posicao):
    soma = sum(int(numeros[i]) * (posicao + 1 - i) for i in range(posicao))
    digito = (soma * 10) % 11
    return 0 if digito == 10 else digito


def validar_cpf(cpf):
    """Confere os dígitos verificadores do CPF. Aceita com ou sem pontuação."""
    numeros = somente_digitos(cpf)
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        return False
    return all(_digito_cpf(numeros, p) == int(numeros[p]) for p in (9, 10))


def validar_cnpj(cnpj):
    numeros = somente_digitos(cnpj)
    if len(numeros) != 14 or numeros == numeros[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, posicao in ((pesos1, 12), (pesos2, 13)):
        resto = sum(int(numeros[i]) * pesos[i] for i in range(posicao)) % 11
        if (0 if resto < 2 else 11 - resto) != int(numeros[posicao]):
            return False
    return True


def validar_email(email):
    if not email:
        return False
    email = email.strip()
    return len(email) <= TAMANHO_MAXIMO_EMAIL and bool(_RE_EMAIL.match(email))


def normalizar_email(email, obrigatorio=True):
    """E-mail em minúsculas e sem espaços nas pontas; ValueError se inválido."""
    email = (email or "").strip().lower()
    if not email and not obrigatorio:
        return ""
    if not validar_email(email):
        raise ValueError("E-mail inválido")
    return email


def exigir_cpf(cpf):
    """CPF só com dígitos; ValueError se inválido."""
    if not validar_cpf(cpf):
        raise ValueError("CPF inválido")
    return somente_digitos(cpf)


def exigir_cnpj(cnpj):
    if not validar_cnpj(cnpj):
        raise ValueError("CNPJ inválido")
    return somente_digitos(cnpj)


def normalizar_nome(nome, rotulo="Nome", maximo=None):
    """Junta espaços repetidos; ValueError se vazio ou longo demais."""
    nome = " ".join((nome or "").split())
    if not nome:
        raise ValueError("%s é obrigatório" % rotulo)
    if maximo is not None and len(nome) > maximo:
        raise ValueError("%s muito longo" % rotulo)
    return nome


def exigir_centavos(valor, rotulo="Valor"):
    """Valor monetário inteiro e não negativo (centavos)."""
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ValueError("%s deve ser inteiro em centavos" % rotulo)
    if valor < 0:
        raise ValueError("%s não pode ser negativo" % rotulo)
    return valor


def exigir_positivo(quantidade, rotulo="Quantidade"):
    if quantidade <= 0:
        raise ValueError("%s deve ser positiva" % rotulo)
    return quantidade
