"""Relatórios de vendas e exportações em CSV.

Os CSV saem com ponto e vírgula e UTF-8 com BOM, que é o que o Excel do
escritório abre sem bagunçar os acentos.
"""
import csv
import logging
from datetime import datetime

from . import config, db
from .util import converter_data, formatar_cpf, formatar_data

log = logging.getLogger(__name__)


def _intervalo(inicio, fim):
    inicio = converter_data(inicio)
    fim = converter_data(fim)
    if fim < inicio:
        raise ValueError("Data final anterior à inicial")
    return inicio, fim


def vendas_por_periodo(conn, inicio, fim):
    """Quantidade de pedidos e total vendido entre duas datas (inclusive).

    Pedidos cancelados não entram. Datas em 'dd/mm/aaaa' ou 'aaaa-mm-dd'.
    """
    inicio, fim = _intervalo(inicio, fim)
    linha = conn.execute(
        "SELECT COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS total,"
        " COALESCE(SUM(desconto), 0) AS descontos"
        " FROM pedidos WHERE status != ? AND date(criado_em) BETWEEN ? AND ?",
        (config.STATUS_CANCELADO, inicio, fim),
    ).fetchone()
    return {
        "inicio": inicio,
        "fim": fim,
        "quantidade_pedidos": linha["quantidade"],
        "total": linha["total"],
        "descontos": linha["descontos"],
    }


def resumo_do_dia(conn, data=None):
    """Fechamento do dia: pedidos, total, cancelados, ticket médio e total por forma.

    data em 'dd/mm/aaaa' ou ISO; sem data, usa hoje.
    """
    if data is None:
        data = datetime.now().strftime(config.FORMATO_DATA)
    else:
        data = converter_data(data)
    validos = conn.execute(
        "SELECT COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS total FROM pedidos"
        " WHERE status != ? AND date(criado_em) = ?",
        (config.STATUS_CANCELADO, data),
    ).fetchone()
    cancelados = conn.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ? AND date(criado_em) = ?",
        (config.STATUS_CANCELADO, data),
    ).fetchone()[0]
    por_forma = {}
    for l in conn.execute(
        "SELECT forma_pagamento, SUM(total) AS total FROM pedidos"
        " WHERE status = ? AND date(pago_em) = ? GROUP BY forma_pagamento",
        (config.STATUS_PAGO, data),
    ).fetchall():
        por_forma[l["forma_pagamento"]] = l["total"]
    return {
        "data": data,
        "pedidos": validos["qtd"],
        "total": validos["total"],
        "cancelados": cancelados,
        "ticket_medio": validos["total"] // validos["qtd"] if validos["qtd"] else 0,
        "pagamentos": por_forma,
    }


def vendas_por_vendedor(conn, inicio, fim):
    """Total vendido por vendedor no período, do maior para o menor."""
    inicio, fim = _intervalo(inicio, fim)
    linhas = conn.execute(
        "SELECT u.id AS vendedor_id, u.login, COUNT(p.id) AS quantidade_pedidos,"
        " SUM(p.total) AS total"
        " FROM pedidos p JOIN usuarios u ON u.id = p.vendedor_id"
        " WHERE p.status != ? AND date(p.criado_em) BETWEEN ? AND ?"
        " GROUP BY u.id, u.login ORDER BY total DESC, u.login",
        (config.STATUS_CANCELADO, inicio, fim),
    ).fetchall()
    return db.linhas_para_dicts(linhas)


def produtos_mais_vendidos(conn, limite=5):
    """Produtos com mais unidades vendidas (pedidos não cancelados)."""
    linhas = conn.execute(
        "SELECT pr.id AS produto_id, pr.codigo, pr.nome,"
        " SUM(i.quantidade) AS quantidade, SUM(i.total) AS total"
        " FROM itens_pedido i"
        " JOIN pedidos p ON p.id = i.pedido_id"
        " JOIN produtos pr ON pr.id = i.produto_id"
        " WHERE p.status != ?"
        " GROUP BY pr.id, pr.codigo, pr.nome"
        " ORDER BY quantidade DESC, pr.nome"
        " LIMIT ?",
        (config.STATUS_CANCELADO, int(limite)),
    ).fetchall()
    return db.linhas_para_dicts(linhas)


def clientes_que_mais_compram(conn, limite=10):
    """Clientes com maior valor comprado (pedidos não cancelados)."""
    linhas = conn.execute(
        "SELECT c.id AS cliente_id, c.nome, COUNT(p.id) AS quantidade_pedidos,"
        " SUM(p.total) AS total, MAX(p.criado_em) AS ultima_compra"
        " FROM pedidos p JOIN clientes c ON c.id = p.cliente_id"
        " WHERE p.status != ?"
        " GROUP BY c.id, c.nome"
        " ORDER BY total DESC, c.nome"
        " LIMIT ?",
        (config.STATUS_CANCELADO, int(limite)),
    ).fetchall()
    return db.linhas_para_dicts(linhas)


def relatorio_pedidos(conn, ordenar_por="criado_em", decrescente=False):
    """Lista de pedidos para conferência, ordenada pela coluna pedida.

    Colunas: id, cliente, vendedor, total, status, criado_em.
    """
    sql = (
        "SELECT p.id AS id, c.nome AS cliente, u.login AS vendedor, p.total AS total,"
        " p.status AS status, p.criado_em AS criado_em"
        " FROM pedidos p"
        " JOIN clientes c ON c.id = p.cliente_id"
        " JOIN usuarios u ON u.id = p.vendedor_id"
    )
    sql += " ORDER BY " + ordenar_por
    if decrescente:
        sql += " DESC"
    return db.linhas_para_dicts(conn.execute(sql).fetchall())


def ticket_medio_por_vendedor(conn):
    """Valor médio dos pedidos de cada vendedor, em centavos."""
    linhas = conn.execute(
        "SELECT u.login, COUNT(p.id) AS pedidos, COALESCE(SUM(p.total), 0) AS total"
        " FROM usuarios u LEFT JOIN pedidos p"
        " ON p.vendedor_id = u.id AND p.status != ?"
        " GROUP BY u.login ORDER BY u.login",
        (config.STATUS_CANCELADO,),
    ).fetchall()
    resultado = {}
    for l in linhas:
        resultado[l["login"]] = l["total"] // l["pedidos"] if l["pedidos"] else 0
    return resultado


def exportar_clientes_csv(conn, caminho):
    """Grava os clientes em CSV. Devolve quantas linhas de dados foram escritas."""
    linhas = conn.execute(
        "SELECT id, nome, cpf, email, telefone, cep, criado_em FROM clientes ORDER BY id"
    ).fetchall()
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arq:
        w = csv.writer(arq, delimiter=config.SEPARADOR_CSV)
        w.writerow(["id", "nome", "cpf", "email", "telefone", "cep", "cadastro"])
        for l in linhas:
            w.writerow([
                l["id"],
                l["nome"],
                formatar_cpf(l["cpf"]),
                l["email"],
                l["telefone"],
                l["cep"],
                formatar_data(l["criado_em"]),
            ])
    log.info("%d clientes exportados para %s", len(linhas), caminho)
    return len(linhas)


def exportar_pedidos_csv(conn, caminho):
    """Grava os pedidos em CSV (valores em reais com vírgula)."""
    linhas = conn.execute(
        "SELECT p.id, c.nome AS cliente, u.login AS vendedor, p.subtotal, p.desconto,"
        " p.total, p.status, p.criado_em"
        " FROM pedidos p JOIN clientes c ON c.id = p.cliente_id"
        " JOIN usuarios u ON u.id = p.vendedor_id ORDER BY p.id"
    ).fetchall()
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arq:
        w = csv.writer(arq, delimiter=config.SEPARADOR_CSV)
        w.writerow(["pedido", "cliente", "vendedor", "subtotal", "desconto", "total",
                    "status", "data"])
        for l in linhas:
            w.writerow([
                l["id"],
                l["cliente"],
                l["vendedor"],
                _reais(l["subtotal"]),
                _reais(l["desconto"]),
                _reais(l["total"]),
                l["status"],
                formatar_data(l["criado_em"]),
            ])
    return len(linhas)


def exportar_estoque_csv(conn, caminho):
    """Posição de estoque dos produtos ativos, para conferência do inventário."""
    linhas = conn.execute(
        "SELECT codigo, nome, preco, estoque, estoque_minimo FROM produtos"
        " WHERE ativo = 1 ORDER BY codigo"
    ).fetchall()
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arq:
        w = csv.writer(arq, delimiter=config.SEPARADOR_CSV)
        w.writerow(["codigo", "produto", "preco", "estoque", "minimo", "valor_em_estoque"])
        for l in linhas:
            w.writerow([
                l["codigo"],
                l["nome"],
                _reais(l["preco"]),
                l["estoque"],
                l["estoque_minimo"],
                _reais(l["preco"] * l["estoque"]),
            ])
    return len(linhas)


def _reais(centavos):
    # 123456 -> '1234,56' (sem R$ e sem milhar, para a planilha somar)
    return "%d,%02d" % divmod(centavos, 100)
