"""Recibo de venda para a impressora térmica (40 colunas).

Não é documento fiscal; serve de comprovante para o cliente.
"""
from ..comum.formatacao import formatar_cnpj, formatar_data_hora, formatar_moeda
from ..infra import config

LARGURA = 40

_NOMES_PAGAMENTO = {
    "dinheiro": "Dinheiro",
    "pix": "PIX",
    "cartao": "Cartão",
    "boleto": "Boleto",
}


def _centro(texto):
    return texto[:LARGURA].center(LARGURA).rstrip()


def _linha_valor(rotulo, valor):
    valor = formatar_moeda(valor)
    espaco = LARGURA - len(rotulo) - len(valor)
    if espaco < 1:
        rotulo = rotulo[: LARGURA - len(valor) - 1]
        espaco = 1
    return rotulo + " " * espaco + valor


def gerar_recibo(conn, pedido_id):
    """Texto do recibo do pedido, pronto para imprimir."""
    pedido = conn.execute(
        "SELECT p.*, c.nome AS cliente, u.login AS vendedor FROM pedidos p"
        " JOIN clientes c ON c.id = p.cliente_id"
        " JOIN usuarios u ON u.id = p.vendedor_id WHERE p.id = ?",
        (pedido_id,),
    ).fetchone()
    if pedido is None:
        raise ValueError("Pedido %s não encontrado" % pedido_id)
    itens = conn.execute(
        "SELECT pr.nome, i.quantidade, i.preco_unitario, i.total FROM itens_pedido i"
        " JOIN produtos pr ON pr.id = i.produto_id WHERE i.pedido_id = ? ORDER BY i.id",
        (pedido_id,),
    ).fetchall()

    linhas = [
        _centro(config.NOME_LOJA.upper()),
        _centro("CNPJ " + formatar_cnpj(config.CNPJ_LOJA)),
        _centro("%s - %s" % (config.CIDADE_LOJA, config.UF_LOJA)),
        "-" * LARGURA,
        "Pedido: %d" % pedido["id"],
        "Data: %s" % formatar_data_hora(pedido["criado_em"]),
        "Cliente: %s" % pedido["cliente"][: LARGURA - 9],
        "Vendedor: %s" % pedido["vendedor"],
        "-" * LARGURA,
    ]
    for item in itens:
        linhas.append(item["nome"][:LARGURA])
        linhas.append(_linha_valor(
            "  %d x %s" % (item["quantidade"], formatar_moeda(item["preco_unitario"])),
            item["total"],
        ))
    linhas.append("-" * LARGURA)
    linhas.append(_linha_valor("Subtotal", pedido["subtotal"]))
    if pedido["desconto"]:
        linhas.append(_linha_valor("Desconto", -pedido["desconto"]))
    linhas.append(_linha_valor("TOTAL", pedido["total"]))
    if pedido["status"] == config.STATUS_PAGO:
        forma = _NOMES_PAGAMENTO.get(pedido["forma_pagamento"], pedido["forma_pagamento"])
        linhas.append("Pago em: %s" % forma)
    elif pedido["status"] == config.STATUS_CANCELADO:
        linhas.append(_centro("*** PEDIDO CANCELADO ***"))
    else:
        linhas.append("Pagamento pendente")
    linhas.append("-" * LARGURA)
    linhas.append(_centro("Obrigado pela preferência!"))
    return "\n".join(linhas) + "\n"
