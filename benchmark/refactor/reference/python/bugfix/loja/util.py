"""Funções de apoio: dinheiro, datas e documentos brasileiros.

Dinheiro anda sempre em centavos (int) dentro do sistema. A conversão
para texto só acontece na hora de mostrar para alguém.
"""
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from . import config

_RE_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def somente_digitos(valor):
    """Remove tudo que não for dígito. None vira string vazia."""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


# ---------------------------------------------------------------- dinheiro

def formatar_moeda(centavos):
    """Formata centavos como moeda: 123456 -> 'R$ 1.234,56'."""
    centavos = int(centavos)
    negativo = centavos < 0
    reais, resto = divmod(abs(centavos), 100)
    texto_reais = "{:,}".format(reais).replace(",", ".")
    texto = "R$ %s,%02d" % (texto_reais, resto)
    if negativo:
        return "-" + texto
    return texto


def converter_moeda(texto):
    """Converte texto digitado pelo usuário em centavos.

    Aceita 'R$ 1.234,56', '1234,56', '12.50' e '12'. Levanta ValueError
    quando não consegue entender o valor.
    """
    if isinstance(texto, int):
        return texto * 100
    if texto is None:
        raise ValueError("Valor vazio")
    limpo = str(texto).strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ValueError("Valor vazio")
    if "," in limpo:
        # formato brasileiro: ponto separa milhar, vírgula separa centavos
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        raise ValueError("Valor inválido: %s" % texto)
    if valor != valor.quantize(Decimal("0.01")):
        raise ValueError("Valor com mais de duas casas decimais: %s" % texto)
    return int(valor * 100)


# ------------------------------------------------------------------- datas

def formatar_data(valor):
    """'2024-03-05' ou '2024-03-05 10:00:00' -> '05/03/2024'."""
    if valor is None or valor == "":
        return ""
    if isinstance(valor, datetime):
        return valor.strftime(config.FORMATO_DATA_BR)
    if isinstance(valor, date):
        return valor.strftime(config.FORMATO_DATA_BR)
    texto = str(valor)[:10]
    try:
        d = datetime.strptime(texto, config.FORMATO_DATA)
    except ValueError:
        raise ValueError("Data inválida: %s" % valor)
    return d.strftime(config.FORMATO_DATA_BR)


def formatar_data_hora(valor):
    """'2024-03-05 14:30:00' -> '05/03/2024 14:30'."""
    if not valor:
        return ""
    d = datetime.strptime(str(valor)[:19], config.FORMATO_DATA_HORA)
    return d.strftime("%d/%m/%Y %H:%M")


def converter_data(texto):
    """'05/03/2024' -> '2024-03-05'. Também aceita a data já em ISO."""
    if texto is None:
        raise ValueError("Data vazia")
    texto = str(texto).strip()
    for formato in (config.FORMATO_DATA_BR, config.FORMATO_DATA):
        try:
            return datetime.strptime(texto, formato).strftime(config.FORMATO_DATA)
        except ValueError:
            continue
    raise ValueError("Data inválida: %s" % texto)


def dias_uteis_entre(inicio, fim):
    """Quantidade de dias úteis (seg a sex) entre duas datas ISO, inclusive.

    Não considera feriados.
    """
    d1 = datetime.strptime(converter_data(inicio), config.FORMATO_DATA).date()
    d2 = datetime.strptime(converter_data(fim), config.FORMATO_DATA).date()
    if d2 < d1:
        d1, d2 = d2, d1
    dias = 0
    atual = d1
    while atual <= d2:
        if atual.weekday() < 5:
            dias += 1
        atual += timedelta(days=1)
    return dias


# -------------------------------------------------------------- documentos

def formatar_cep(cep):
    """'01310100' -> '01310-100'."""
    numeros = somente_digitos(cep)
    if len(numeros) != 8:
        raise ValueError("CEP deve ter 8 dígitos")
    return numeros[:5] + "-" + numeros[5:]


def formatar_cpf(cpf):
    """'52998224725' -> '529.982.247-25'. Devolve como veio se não tiver 11 dígitos."""
    n = somente_digitos(cpf)
    if len(n) != 11:
        return str(cpf or "")
    return "%s.%s.%s-%s" % (n[:3], n[3:6], n[6:9], n[9:])


def validar_cpf(cpf):
    """Confere os dígitos verificadores do CPF. Aceita com ou sem pontuação."""
    numeros = somente_digitos(cpf)
    if len(numeros) != 11:
        return False
    if numeros == numeros[0] * 11:
        return False
    for posicao in (9, 10):
        soma = 0
        for i in range(posicao):
            soma += int(numeros[i]) * (posicao + 1 - i)
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(numeros[posicao]):
            return False
    return True


def formatar_cnpj(cnpj):
    """'11222333000181' -> '11.222.333/0001-81'."""
    n = somente_digitos(cnpj)
    if len(n) != 14:
        return str(cnpj or "")
    return "%s.%s.%s/%s-%s" % (n[:2], n[2:5], n[5:8], n[8:12], n[12:])


def validar_cnpj(cnpj):
    numeros = somente_digitos(cnpj)
    if len(numeros) != 14 or numeros == numeros[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, posicao in ((pesos1, 12), (pesos2, 13)):
        soma = sum(int(numeros[i]) * pesos[i] for i in range(posicao))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(numeros[posicao]):
            return False
    return True


def validar_email(email):
    if not email:
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    return bool(_RE_EMAIL.match(email))
