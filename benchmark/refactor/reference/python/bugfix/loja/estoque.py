"""Movimentação de estoque.

Toda alteração de saldo deve passar por aqui (ou pelo pedido), para que
o histórico em movimentos_estoque explique o saldo atual.
"""
import logging
import sqlite3

from . import db

log = logging.getLogger(__name__)

TIPOS_MOVIMENTO = ("entrada", "saida", "ajuste")


def _registrar_movimento(conn, produto_id, tipo, quantidade, motivo="", pedido_id=None):
    if tipo not in TIPOS_MOVIMENTO:
        raise ValueError("Tipo de movimento inválido: %s" % tipo)
    conn.execute(
        "INSERT INTO movimentos_estoque (produto_id, tipo, quantidade, motivo, pedido_id, criado_em)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (produto_id, tipo, quantidade, motivo or "", pedido_id, db.agora()),
    )


def _saldo(conn, produto_id):
    linha = conn.execute("SELECT estoque FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    if linha is None:
        raise ValueError("Produto %s não encontrado" % produto_id)
    return linha["estoque"]


def registrar_entrada(conn, produto_id, quantidade, motivo="compra"):
    """Soma quantidade ao estoque. Devolve o novo saldo."""
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser positiva")
    saldo = _saldo(conn, produto_id)
    novo = saldo + quantidade
    conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (novo, produto_id))
    _registrar_movimento(conn, produto_id, "entrada", quantidade, motivo)
    conn.commit()
    return novo


def registrar_saida(conn, produto_id, quantidade, motivo="ajuste"):
    """Tira quantidade do estoque (perda, uso interno, troca). Devolve o novo saldo."""
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser positiva")
    saldo = _saldo(conn, produto_id)
    if quantidade > saldo:
        raise ValueError("Estoque insuficiente: saldo %d, saída %d" % (saldo, quantidade))
    novo = saldo - quantidade
    conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (novo, produto_id))
    _registrar_movimento(conn, produto_id, "saida", quantidade, motivo)
    conn.commit()
    return novo


def atualizar_estoque(conn, produto_id, nova_quantidade, motivo="inventario"):
    """Define o saldo do produto após contagem de inventário.

    A diferença para o saldo anterior fica registrada como ajuste.
    """
    try:
        saldo = _saldo(conn, produto_id)
        conn.execute(
            "UPDATE produtos SET estoque = ? WHERE id = ?", (nova_quantidade, produto_id)
        )
        diferenca = nova_quantidade - saldo
        if diferenca:
            _registrar_movimento(conn, produto_id, "ajuste", diferenca, motivo)
        conn.commit()
    except sqlite3.Error as erro:
        conn.rollback()
        log.warning("inventario do produto %s: %s", produto_id, erro)
    return True


def produtos_estoque_baixo(conn):
    """Produtos ativos com saldo igual ou abaixo do estoque mínimo."""
    linhas = conn.execute(
        "SELECT id, codigo, nome, estoque, estoque_minimo FROM produtos"
        " WHERE ativo = 1 AND estoque <= estoque_minimo"
        " ORDER BY estoque ASC, nome COLLATE NOCASE"
    ).fetchall()
    return db.linhas_para_dicts(linhas)


def historico_estoque(conn, produto_id, limite=50):
    """Últimos movimentos do produto, do mais novo para o mais antigo."""
    linhas = conn.execute(
        "SELECT tipo, quantidade, motivo, pedido_id, criado_em FROM movimentos_estoque"
        " WHERE produto_id = ? ORDER BY id DESC LIMIT ?",
        (produto_id, limite),
    ).fetchall()
    return db.linhas_para_dicts(linhas)


def valor_em_estoque(conn):
    """Soma de preço x saldo dos produtos ativos, em centavos."""
    linha = conn.execute(
        "SELECT COALESCE(SUM(preco * estoque), 0) FROM produtos WHERE ativo = 1"
    ).fetchone()
    return linha[0]


def devolver_itens_ao_estoque(conn, pedido_id):
    """Devolve ao estoque os itens de um pedido. Não faz commit."""
    itens = conn.execute(
        "SELECT produto_id, quantidade FROM itens_pedido WHERE pedido_id = ?", (pedido_id,)
    ).fetchall()
    for item in itens:
        conn.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )
        _registrar_movimento(
            conn, item["produto_id"], "entrada", item["quantidade"],
            "cancelamento do pedido %s" % pedido_id, pedido_id,
        )
    return len(itens)
