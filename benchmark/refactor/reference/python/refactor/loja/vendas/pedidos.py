"""Pedidos de venda.

Fluxo normal: o vendedor cria o pedido (o estoque baixa na hora), o
cliente paga e o pedido fica 'pago'. Um pedido pode ser cancelado; nesse
caso os itens voltam para o estoque.

Vendedor só enxerga e cancela os próprios pedidos; admin, qualquer um.
"""
import logging

from ..cadastro.estoque import devolver_itens_ao_estoque, registrar_movimento
from ..infra import banco, config
from . import precos

log = logging.getLogger(__name__)

TAMANHO_MAXIMO_OBSERVACAO = 500


# ------------------------------------------------------------ criação

def criar_pedido(conn, cliente_id, itens, vendedor_id, cupom=None, observacao=""):
    """Cria um pedido e baixa o estoque dos produtos.

    itens: lista de dicts {"produto_id": int, "quantidade": int}.
    Devolve o id do pedido. ValueError se algo estiver errado; nesse caso
    nada é gravado.
    """
    observacao = _validar_cabecalho(itens, observacao)
    cliente = _carregar_cliente(conn, cliente_id)
    vendedor = _carregar_vendedor(conn, vendedor_id)
    linhas = _carregar_linhas(conn, _consolidar_itens(itens))
    valores = _calcular_valores(conn, cliente_id, linhas, cupom)
    pedido_id = _gravar(conn, cliente_id, vendedor_id, linhas, valores, cupom, observacao)
    log.info("pedido %s criado por %s para o cliente %s: total %s",
             pedido_id, vendedor["login"], cliente["nome"], valores["total"])
    return pedido_id


def _validar_cabecalho(itens, observacao):
    if not itens:
        raise ValueError("Pedido sem itens")
    if len(itens) > config.MAX_ITENS_POR_PEDIDO:
        raise ValueError("Pedido com itens demais (máximo %d)" % config.MAX_ITENS_POR_PEDIDO)
    observacao = (observacao or "").strip()
    if len(observacao) > TAMANHO_MAXIMO_OBSERVACAO:
        raise ValueError("Observação muito longa")
    return observacao


def _carregar_cliente(conn, cliente_id):
    cliente = conn.execute("SELECT id, nome FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if cliente is None:
        raise ValueError("Cliente %s não encontrado" % cliente_id)
    return cliente


def _carregar_vendedor(conn, vendedor_id):
    vendedor = conn.execute(
        "SELECT id, login, ativo FROM usuarios WHERE id = ?", (vendedor_id,)
    ).fetchone()
    if vendedor is None:
        raise ValueError("Vendedor %s não encontrado" % vendedor_id)
    if not vendedor["ativo"]:
        raise ValueError("Vendedor inativo não pode vender")
    return vendedor


def _consolidar_itens(itens):
    """Soma itens repetidos do mesmo produto, mantendo a ordem de chegada."""
    quantidades = {}
    for item in itens:
        try:
            produto_id = int(item["produto_id"])
            quantidade = int(item["quantidade"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Item inválido: %r" % (item,))
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        if quantidade > config.MAX_QUANTIDADE_ITEM:
            raise ValueError("Quantidade acima do permitido para um item")
        quantidades[produto_id] = quantidades.get(produto_id, 0) + quantidade
    return quantidades


def _carregar_linhas(conn, quantidades):
    """Confere produto e estoque e devolve as linhas com preço."""
    linhas = []
    for produto_id, qtd in quantidades.items():
        produto = conn.execute(
            "SELECT id, codigo, nome, preco, estoque, ativo FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()
        if produto is None:
            raise ValueError("Produto %s não encontrado" % produto_id)
        if not produto["ativo"]:
            raise ValueError("Produto %s está fora de venda" % produto["codigo"])
        if produto["estoque"] < qtd:
            raise ValueError("Estoque insuficiente para %s (disponível: %d, pedido: %d)"
                             % (produto["nome"], produto["estoque"], qtd))
        linhas.append({
            "produto_id": produto_id,
            "quantidade": qtd,
            "preco_unitario": produto["preco"],
            "total": produto["preco"] * qtd,
        })
    return linhas


def _calcular_valores(conn, cliente_id, linhas, cupom):
    precos.conferir_cupom_do_cliente(conn, cliente_id, cupom)
    subtotal = sum(l["total"] for l in linhas)
    desconto = precos.calcular_desconto(subtotal, cupom)
    return {"subtotal": subtotal, "desconto": desconto, "total": subtotal - desconto}


def _gravar(conn, cliente_id, vendedor_id, linhas, valores, cupom, observacao):
    try:
        cur = conn.execute(
            "INSERT INTO pedidos (cliente_id, vendedor_id, subtotal, desconto, total, cupom,"
            " status, observacao, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cliente_id, vendedor_id, valores["subtotal"], valores["desconto"],
             valores["total"], precos.normalizar_cupom(cupom), config.STATUS_ABERTO,
             observacao, banco.agora()),
        )
        pedido_id = cur.lastrowid
        for linha in linhas:
            _gravar_item(conn, pedido_id, linha)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return pedido_id


def _gravar_item(conn, pedido_id, linha):
    conn.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, total)"
        " VALUES (?, ?, ?, ?, ?)",
        (pedido_id, linha["produto_id"], linha["quantidade"], linha["preco_unitario"],
         linha["total"]),
    )
    baixa = conn.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (linha["quantidade"], linha["produto_id"], linha["quantidade"]),
    )
    if baixa.rowcount == 0:
        raise ValueError("Estoque mudou durante o pedido, tente de novo")
    registrar_movimento(conn, linha["produto_id"], "saida", linha["quantidade"], "venda",
                        pedido_id)


# ------------------------------------------------------------ consulta

def _itens(conn, pedido_id):
    linhas = conn.execute(
        "SELECT i.produto_id, p.codigo, p.nome, i.quantidade, i.preco_unitario, i.total"
        " FROM itens_pedido i JOIN produtos p ON p.id = i.produto_id"
        " WHERE i.pedido_id = ? ORDER BY i.id",
        (pedido_id,),
    ).fetchall()
    return banco.linhas_para_dicts(linhas)


_CAMPOS_PEDIDO = ("id", "cliente_id", "vendedor_id", "subtotal", "desconto", "total", "cupom",
                  "status", "forma_pagamento", "criado_em")


def _pedido(conn, linha):
    if linha is None:
        return None
    pedido = {campo: linha[campo] for campo in _CAMPOS_PEDIDO}
    pedido["itens"] = _itens(conn, linha["id"])
    return pedido


def _pode_ver(usuario, linha):
    return usuario is None or usuario["papel"] == "admin" or linha["vendedor_id"] == usuario["id"]


def buscar_pedido(conn, pedido_id, usuario=None):
    """Devolve o pedido com seus itens, ou None (também se o vendedor não for o dono)."""
    linha = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if linha is None or not _pode_ver(usuario, linha):
        return None
    return _pedido(conn, linha)


def listar_pedidos(conn, usuario, status=None):
    """Pedidos do mais novo para o mais antigo; vendedor vê só os próprios."""
    sql = "SELECT * FROM pedidos WHERE 1 = 1"
    params = []
    if usuario["papel"] != "admin":
        sql += " AND vendedor_id = ?"
        params.append(usuario["id"])
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC"
    return [_pedido(conn, l) for l in conn.execute(sql, params).fetchall()]


# ------------------------------------------------------------ mudanças de status

def cancelar_pedido(conn, pedido_id, usuario):
    """Cancela o pedido e devolve os itens ao estoque."""
    linha = conn.execute(
        "SELECT id, status, vendedor_id FROM pedidos WHERE id = ?", (pedido_id,)
    ).fetchone()
    if linha is None:
        raise ValueError("Pedido %s não encontrado" % pedido_id)
    if not _pode_ver(usuario, linha):
        raise PermissionError("Vendedor só cancela os próprios pedidos")
    if linha["status"] == config.STATUS_CANCELADO:
        raise ValueError("Pedido já está cancelado")
    try:
        devolver_itens_ao_estoque(conn, pedido_id)
        conn.execute(
            "UPDATE pedidos SET status = ?, cancelado_em = ? WHERE id = ?",
            (config.STATUS_CANCELADO, banco.agora(), pedido_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    log.info("pedido %s cancelado por %s", pedido_id, usuario["login"])
    return True


def registrar_pagamento(conn, pedido_id, forma):
    """Marca o pedido como pago na forma informada (dinheiro, pix, cartao, boleto)."""
    forma = (forma or "").strip().lower()
    if forma not in config.FORMAS_PAGAMENTO:
        raise ValueError("Forma de pagamento inválida: %s" % forma)
    linha = conn.execute("SELECT status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if linha is None:
        raise ValueError("Pedido %s não encontrado" % pedido_id)
    if linha["status"] == config.STATUS_CANCELADO:
        raise ValueError("Pedido cancelado não pode ser pago")
    if linha["status"] == config.STATUS_PAGO:
        raise ValueError("Pedido já está pago")
    conn.execute(
        "UPDATE pedidos SET status = ?, forma_pagamento = ?, pago_em = ? WHERE id = ?",
        (config.STATUS_PAGO, forma, banco.agora(), pedido_id),
    )
    conn.commit()
    return True


def previa_pedido(conn, itens, cupom=None):
    """Calcula subtotal, desconto e total sem gravar nada (orçamento de balcão)."""
    subtotal = 0
    for item in itens:
        linha = conn.execute(
            "SELECT preco FROM produtos WHERE id = ? AND ativo = 1", (item["produto_id"],)
        ).fetchone()
        if linha is None:
            raise ValueError("Produto %s não encontrado" % item["produto_id"])
        subtotal += linha["preco"] * int(item["quantidade"])
    desconto = precos.calcular_desconto(subtotal, cupom)
    return {"subtotal": subtotal, "desconto": desconto, "total": subtotal - desconto}
