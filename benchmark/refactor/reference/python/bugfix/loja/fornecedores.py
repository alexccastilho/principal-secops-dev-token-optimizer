"""Fornecedores e pedidos de compra.

A compra nasce 'aberta'. Quando a mercadoria chega, receber_compra dá
entrada no estoque de cada item e marca a compra como 'recebida'.
"""
import logging

from . import db
from .util import formatar_cnpj, somente_digitos, validar_cnpj, validar_email

log = logging.getLogger(__name__)

STATUS_COMPRA_ABERTA = "aberta"
STATUS_COMPRA_RECEBIDA = "recebida"
STATUS_COMPRA_CANCELADA = "cancelada"


def _fornecedor(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "cnpj": linha["cnpj"],
        "email": linha["email"],
        "telefone": linha["telefone"],
        "prazo_entrega_dias": linha["prazo_entrega_dias"],
        "ativo": bool(linha["ativo"]),
    }


def cadastrar_fornecedor(conn, nome, cnpj, email="", telefone="", prazo_entrega_dias=7):
    """Cadastra fornecedor e devolve o id. O CNPJ é gravado só com dígitos."""
    nome = " ".join((nome or "").split())
    if not nome:
        raise ValueError("Nome do fornecedor é obrigatório")
    if not validar_cnpj(cnpj):
        raise ValueError("CNPJ inválido")
    cnpj = somente_digitos(cnpj)
    email = (email or "").strip().lower()
    if email and not validar_email(email):
        raise ValueError("E-mail inválido")
    if prazo_entrega_dias < 0:
        raise ValueError("Prazo de entrega inválido")
    if conn.execute("SELECT 1 FROM fornecedores WHERE cnpj = ?", (cnpj,)).fetchone():
        raise ValueError("Fornecedor %s já cadastrado" % formatar_cnpj(cnpj))
    cur = conn.execute(
        "INSERT INTO fornecedores (nome, cnpj, email, telefone, prazo_entrega_dias, ativo,"
        " criado_em) VALUES (?, ?, ?, ?, ?, 1, ?)",
        (nome, cnpj, email, somente_digitos(telefone), prazo_entrega_dias, db.agora()),
    )
    conn.commit()
    return cur.lastrowid


def buscar_fornecedor(conn, fornecedor_id):
    linha = conn.execute(
        "SELECT * FROM fornecedores WHERE id = ?", (fornecedor_id,)
    ).fetchone()
    return _fornecedor(linha)


def listar_fornecedores(conn, apenas_ativos=True):
    sql = "SELECT * FROM fornecedores"
    if apenas_ativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome COLLATE NOCASE"
    return [_fornecedor(l) for l in conn.execute(sql).fetchall()]


def registrar_compra(conn, fornecedor_id, itens):
    """Registra um pedido de compra ao fornecedor.

    itens: lista de {"produto_id", "quantidade", "custo_unitario"} (custo em centavos).
    Devolve o id da compra.
    """
    fornecedor = buscar_fornecedor(conn, fornecedor_id)
    if fornecedor is None or not fornecedor["ativo"]:
        raise ValueError("Fornecedor não encontrado ou inativo")
    if not itens:
        raise ValueError("Compra sem itens")
    total = 0
    for item in itens:
        if item["quantidade"] <= 0 or item["custo_unitario"] < 0:
            raise ValueError("Item de compra inválido")
        existe = conn.execute(
            "SELECT 1 FROM produtos WHERE id = ?", (item["produto_id"],)
        ).fetchone()
        if not existe:
            raise ValueError("Produto %s não encontrado" % item["produto_id"])
        total += item["quantidade"] * item["custo_unitario"]
    try:
        cur = conn.execute(
            "INSERT INTO compras (fornecedor_id, total, status, criado_em) VALUES (?, ?, ?, ?)",
            (fornecedor_id, total, STATUS_COMPRA_ABERTA, db.agora()),
        )
        compra_id = cur.lastrowid
        for item in itens:
            conn.execute(
                "INSERT INTO itens_compra (compra_id, produto_id, quantidade, custo_unitario)"
                " VALUES (?, ?, ?, ?)",
                (compra_id, item["produto_id"], item["quantidade"], item["custo_unitario"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return compra_id


def receber_compra(conn, compra_id):
    """Dá entrada no estoque dos itens da compra. Devolve a quantidade de itens."""
    compra = conn.execute("SELECT * FROM compras WHERE id = ?", (compra_id,)).fetchone()
    if compra is None:
        raise ValueError("Compra %s não encontrada" % compra_id)
    if compra["status"] != STATUS_COMPRA_ABERTA:
        raise ValueError("Compra %s já está %s" % (compra_id, compra["status"]))
    itens = conn.execute(
        "SELECT produto_id, quantidade FROM itens_compra WHERE compra_id = ?", (compra_id,)
    ).fetchall()
    agora = db.agora()
    try:
        for item in itens:
            conn.execute(
                "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
            conn.execute(
                "INSERT INTO movimentos_estoque (produto_id, tipo, quantidade, motivo, criado_em)"
                " VALUES (?, 'entrada', ?, ?, ?)",
                (item["produto_id"], item["quantidade"], "compra %d" % compra_id, agora),
            )
        conn.execute(
            "UPDATE compras SET status = ?, recebida_em = ? WHERE id = ?",
            (STATUS_COMPRA_RECEBIDA, agora, compra_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    log.info("compra %s recebida com %d itens", compra_id, len(itens))
    return len(itens)


def cancelar_compra(conn, compra_id):
    cur = conn.execute(
        "UPDATE compras SET status = ? WHERE id = ? AND status = ?",
        (STATUS_COMPRA_CANCELADA, compra_id, STATUS_COMPRA_ABERTA),
    )
    conn.commit()
    return cur.rowcount > 0


def compras_do_fornecedor(conn, fornecedor_id):
    """Compras do fornecedor, da mais nova para a mais antiga, com os itens."""
    compras = []
    for linha in conn.execute(
        "SELECT * FROM compras WHERE fornecedor_id = ? ORDER BY id DESC", (fornecedor_id,)
    ).fetchall():
        compra = db.linha_para_dict(linha)
        compra["itens"] = db.linhas_para_dicts(conn.execute(
            "SELECT produto_id, quantidade, custo_unitario FROM itens_compra"
            " WHERE compra_id = ? ORDER BY id",
            (linha["id"],),
        ).fetchall())
        compras.append(compra)
    return compras


def custo_medio(conn, produto_id):
    """Custo médio ponderado das compras recebidas do produto (centavos), ou None."""
    linha = conn.execute(
        "SELECT SUM(i.quantidade * i.custo_unitario) AS valor, SUM(i.quantidade) AS qtd"
        " FROM itens_compra i JOIN compras c ON c.id = i.compra_id"
        " WHERE i.produto_id = ? AND c.status = ?",
        (produto_id, STATUS_COMPRA_RECEBIDA),
    ).fetchone()
    if not linha["qtd"]:
        return None
    return linha["valor"] // linha["qtd"]
