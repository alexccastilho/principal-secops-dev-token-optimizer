"""Conversão entre valores internos e texto brasileiro.

Dinheiro anda sempre em centavos (int) dentro do sistema. A conversão
para texto só acontece na hora de mostrar para alguém.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ..infra import config
from .validacao import somente_digitos


# ---------------------------------------------------------------- dinheiro

def formatar_moeda(centavos):
    """Formata centavos como moeda: 123456 -> 'R$ 1.234,56'."""
    centavos = int(centavos)
    reais, resto = divmod(abs(centavos), 100)
    texto = "R$ %s,%02d" % ("{:,}".format(reais).replace(",", "."), resto)
    return "-" + texto if centavos < 0 else texto


def converter_moeda(texto):
    """Converte texto digitado pelo usuário em centavos.

    Aceita 'R$ 1.234,56', '1234,56', '12.50' e '12'. ValueError quando não
    consegue entender o valor.
    """
    if isinstance(texto, int):
        return texto * 100
    limpo = str(texto or "").strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ValueError("Valor vazio")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        raise ValueError("Valor inválido: %s" % texto)
    if valor != valor.quantize(Decimal("0.01")):
        raise ValueError("Valor com mais de duas casas decimais: %s" % texto)
    return int(valor * 100)


def reais_planilha(centavos):
    """123456 -> '1234,56' (sem R$ e sem milhar, para a planilha somar)."""
    return "%d,%02d" % divmod(centavos, 100)


# ------------------------------------------------------------------- datas

def formatar_data(valor):
    """'2024-03-05' ou '2024-03-05 10:00:00' -> '05/03/2024'."""
    if valor is None or valor == "":
        return ""
    if isinstance(valor, (datetime, date)):
        return valor.strftime(config.FORMATO_DATA_BR)
    try:
        d = datetime.strptime(str(valor)[:10], config.FORMATO_DATA)
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


def hoje_iso():
    return datetime.now().strftime(config.FORMATO_DATA)


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


def formatar_cnpj(cnpj):
    """'11222333000181' -> '11.222.333/0001-81'."""
    n = somente_digitos(cnpj)
    if len(n) != 14:
        return str(cnpj or "")
    return "%s.%s.%s/%s-%s" % (n[:2], n[2:5], n[5:8], n[8:12], n[12:])


def formatar_telefone(numero):
    """'11987654321' -> '(11) 98765-4321'; '1134567890' -> '(11) 3456-7890'.

    Outros tamanhos voltam só com os dígitos.
    """
    d = somente_digitos(numero)
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) == 11:
        return "(%s) %s-%s" % (d[:2], d[2:7], d[7:])
    if len(d) == 10:
        return "(%s) %s-%s" % (d[:2], d[2:6], d[6:])
    return d
