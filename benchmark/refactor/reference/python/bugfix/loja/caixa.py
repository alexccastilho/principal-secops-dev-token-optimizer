"""Controle do caixa do balcão.

Um caixa por vez. O operador abre com um fundo de troco, faz sangrias e
suprimentos durante o dia e fecha informando o dinheiro contado. O valor
esperado considera só os pedidos pagos em dinheiro desde a abertura.
"""
import logging

from . import config, db

log = logging.getLogger(__name__)


def _caixa(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "usuario_id": linha["usuario_id"],
        "valor_inicial": linha["valor_inicial"],
        "aberto_em": linha["aberto_em"],
        "fechado_em": linha["fechado_em"],
        "valor_contado": linha["valor_contado"],
    }


def caixa_aberto(conn):
    """O caixa aberto no momento, ou None."""
    linha = conn.execute(
        "SELECT * FROM caixas WHERE fechado_em IS NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return _caixa(linha)


def abrir_caixa(conn, usuario_id, valor_inicial):
    """Abre o caixa com o fundo de troco (centavos). Devolve o id."""
    if valor_inicial < 0:
        raise ValueError("Fundo de troco não pode ser negativo")
    if caixa_aberto(conn) is not None:
        raise ValueError("Já existe um caixa aberto")
    cur = conn.execute(
        "INSERT INTO caixas (usuario_id, valor_inicial, aberto_em) VALUES (?, ?, ?)",
        (usuario_id, valor_inicial, db.agora()),
    )
    conn.commit()
    log.info("caixa %s aberto pelo usuario %s", cur.lastrowid, usuario_id)
    return cur.lastrowid


def _movimentar(conn, tipo, valor, motivo):
    caixa = caixa_aberto(conn)
    if caixa is None:
        raise ValueError("Nenhum caixa aberto")
    if valor <= 0:
        raise ValueError("Valor deve ser positivo")
    conn.execute(
        "INSERT INTO movimentos_caixa (caixa_id, tipo, valor, motivo, criado_em)"
        " VALUES (?, ?, ?, ?, ?)",
        (caixa["id"], tipo, valor, motivo or "", db.agora()),
    )
    conn.commit()
    return caixa["id"]


def registrar_sangria(conn, valor, motivo=""):
    """Retirada de dinheiro do caixa (ex.: depósito no banco)."""
    return _movimentar(conn, "sangria", valor, motivo)


def registrar_suprimento(conn, valor, motivo=""):
    """Entrada de dinheiro no caixa que não é venda (ex.: mais troco)."""
    return _movimentar(conn, "suprimento", valor, motivo)


def _vendas_desde(conn, inicio):
    """Total pago por forma de pagamento desde 'inicio'."""
    linhas = conn.execute(
        "SELECT forma_pagamento, SUM(total) AS total FROM pedidos"
        " WHERE status = ? AND pago_em >= ? GROUP BY forma_pagamento",
        (config.STATUS_PAGO, inicio),
    ).fetchall()
    por_forma = {forma: 0 for forma in config.FORMAS_PAGAMENTO}
    for l in linhas:
        por_forma[l["forma_pagamento"]] = l["total"]
    return por_forma


def resumo_caixa(conn):
    """Situação do caixa aberto: fundo, vendas por forma, sangrias e esperado em dinheiro."""
    caixa = caixa_aberto(conn)
    if caixa is None:
        raise ValueError("Nenhum caixa aberto")
    movimentos = conn.execute(
        "SELECT tipo, COALESCE(SUM(valor), 0) AS total FROM movimentos_caixa"
        " WHERE caixa_id = ? GROUP BY tipo",
        (caixa["id"],),
    ).fetchall()
    sangrias = 0
    suprimentos = 0
    for m in movimentos:
        if m["tipo"] == "sangria":
            sangrias = m["total"]
        elif m["tipo"] == "suprimento":
            suprimentos = m["total"]
    por_forma = _vendas_desde(conn, caixa["aberto_em"])
    esperado = caixa["valor_inicial"] + por_forma["dinheiro"] + suprimentos - sangrias
    return {
        "caixa_id": caixa["id"],
        "valor_inicial": caixa["valor_inicial"],
        "vendas_por_forma": por_forma,
        "sangrias": sangrias,
        "suprimentos": suprimentos,
        "esperado_em_dinheiro": esperado,
    }


def fechar_caixa(conn, valor_contado):
    """Fecha o caixa com o dinheiro contado. Devolve o resumo com a diferença."""
    resumo = resumo_caixa(conn)
    conn.execute(
        "UPDATE caixas SET fechado_em = ?, valor_contado = ? WHERE id = ?",
        (db.agora(), valor_contado, resumo["caixa_id"]),
    )
    conn.commit()
    resumo["valor_contado"] = valor_contado
    resumo["diferenca"] = valor_contado - resumo["esperado_em_dinheiro"]
    if resumo["diferenca"]:
        log.warning("caixa %s fechado com diferença de %s centavos",
                    resumo["caixa_id"], resumo["diferenca"])
    return resumo
