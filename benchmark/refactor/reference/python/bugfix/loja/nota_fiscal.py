"""Geração dos dados da nota fiscal eletrônica (NF-e) de um pedido.

Monta a estrutura que o emissor espera receber: emitente, destinatário,
itens com impostos e totais. A transmissão para a SEFAZ é feita pelo
emissor contratado, fora deste sistema.
"""
from datetime import datetime
from xml.sax.saxutils import escape

from . import config
from .util import formatar_cnpj, formatar_cpf, somente_digitos

# alíquotas simplificadas do Simples Nacional, faixa 1
ALIQUOTA_ICMS = 0.0125
ALIQUOTA_PIS = 0.0
ALIQUOTA_COFINS = 0.0

CODIGO_UF = {"SP": "35", "RJ": "33", "MG": "31", "PR": "41", "RS": "43", "SC": "42"}
CFOP_VENDA = "5102"
MODELO_NFE = "55"
SERIE = "1"


def _digito_chave(chave43):
    """Dígito verificador da chave de acesso (módulo 11, pesos 2 a 9)."""
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    for i, c in enumerate(reversed(chave43)):
        soma += int(c) * pesos[i % 8]
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def gerar_chave_acesso(numero_nota, emissao=None):
    """Chave de 44 dígitos: UF, AAMM, CNPJ, modelo, série, número, tipo, código, DV."""
    emissao = emissao or datetime.now()
    uf = CODIGO_UF.get(config.UF_LOJA, "35")
    aamm = emissao.strftime("%y%m")
    cnpj = somente_digitos(config.CNPJ_LOJA).zfill(14)
    numero = str(numero_nota).zfill(9)
    # código numérico da nota: derivado do número para a chave ser reproduzível
    codigo = str(numero_nota * 7919 % 100000000).zfill(8)
    chave = uf + aamm + cnpj + MODELO_NFE + SERIE.zfill(3) + numero + "1" + codigo
    return chave + _digito_chave(chave)


def calcular_impostos(valor_centavos):
    """Impostos de um item, em centavos (arredondamento comercial)."""
    return {
        "icms": int(round(valor_centavos * ALIQUOTA_ICMS)),
        "pis": int(round(valor_centavos * ALIQUOTA_PIS)),
        "cofins": int(round(valor_centavos * ALIQUOTA_COFINS)),
    }


def _emitente():
    return {
        "cnpj": formatar_cnpj(config.CNPJ_LOJA),
        "razao_social": config.NOME_LOJA,
        "municipio": config.CIDADE_LOJA,
        "uf": config.UF_LOJA,
        "regime": "Simples Nacional",
    }


def montar_dados_nfe(conn, pedido_id, numero_nota):
    """Estrutura da NF-e para o pedido (dict pronto para virar XML ou JSON)."""
    pedido = conn.execute(
        "SELECT p.*, c.nome, c.cpf, c.email, c.cep FROM pedidos p"
        " JOIN clientes c ON c.id = p.cliente_id WHERE p.id = ?",
        (pedido_id,),
    ).fetchone()
    if pedido is None:
        raise ValueError("Pedido %s não encontrado" % pedido_id)
    if pedido["status"] != config.STATUS_PAGO:
        raise ValueError("Só é emitida nota de pedido pago")

    itens = conn.execute(
        "SELECT i.*, pr.codigo, pr.nome FROM itens_pedido i"
        " JOIN produtos pr ON pr.id = i.produto_id WHERE i.pedido_id = ?",
        (pedido_id,),
    ).fetchall()

    # desconto rateado proporcionalmente entre os itens
    restante = pedido["desconto"]
    dados_itens = []
    for n, item in enumerate(itens, start=1):
        if n == len(itens):
            desconto_item = restante
        else:
            desconto_item = pedido["desconto"] * item["total"] // max(pedido["subtotal"], 1)
            restante -= desconto_item
        base = item["total"] - desconto_item
        dados_itens.append({
            "numero": n,
            "codigo": item["codigo"],
            "descricao": item["nome"],
            "cfop": CFOP_VENDA,
            "quantidade": item["quantidade"],
            "valor_unitario": item["preco_unitario"],
            "valor_bruto": item["total"],
            "desconto": desconto_item,
            "impostos": calcular_impostos(base),
        })

    emissao = datetime.now()
    return {
        "chave": gerar_chave_acesso(numero_nota, emissao),
        "numero": numero_nota,
        "serie": SERIE,
        "emissao": emissao.strftime("%Y-%m-%dT%H:%M:%S"),
        "emitente": _emitente(),
        "destinatario": {
            "nome": pedido["nome"],
            "cpf": formatar_cpf(pedido["cpf"]),
            "email": pedido["email"],
            "cep": pedido["cep"],
        },
        "itens": dados_itens,
        "totais": {
            "produtos": pedido["subtotal"],
            "desconto": pedido["desconto"],
            "nota": pedido["total"],
            "icms": sum(i["impostos"]["icms"] for i in dados_itens),
        },
        "pagamento": pedido["forma_pagamento"],
    }


def dados_para_xml(dados):
    """XML simplificado no layout aceito pelo emissor."""
    partes = ['<?xml version="1.0" encoding="UTF-8"?>', "<NFe>"]
    partes.append('  <infNFe Id="NFe%s">' % dados["chave"])
    partes.append("    <ide><nNF>%s</nNF><serie>%s</serie><dhEmi>%s</dhEmi></ide>"
                  % (dados["numero"], dados["serie"], dados["emissao"]))
    em = dados["emitente"]
    partes.append("    <emit><CNPJ>%s</CNPJ><xNome>%s</xNome></emit>"
                  % (somente_digitos(em["cnpj"]), escape(em["razao_social"])))
    de = dados["destinatario"]
    partes.append("    <dest><CPF>%s</CPF><xNome>%s</xNome></dest>"
                  % (somente_digitos(de["cpf"]), escape(de["nome"])))
    for item in dados["itens"]:
        partes.append(
            '    <det nItem="%d"><prod><cProd>%s</cProd><xProd>%s</xProd>'
            "<CFOP>%s</CFOP><qCom>%d</qCom><vUnCom>%.2f</vUnCom><vDesc>%.2f</vDesc>"
            "</prod></det>"
            % (item["numero"], escape(item["codigo"]), escape(item["descricao"]),
               item["cfop"], item["quantidade"], item["valor_unitario"] / 100,
               item["desconto"] / 100)
        )
    t = dados["totais"]
    partes.append("    <total><vProd>%.2f</vProd><vDesc>%.2f</vDesc><vNF>%.2f</vNF></total>"
                  % (t["produtos"] / 100, t["desconto"] / 100, t["nota"] / 100))
    partes.append("  </infNFe>")
    partes.append("</NFe>")
    return "\n".join(partes)
