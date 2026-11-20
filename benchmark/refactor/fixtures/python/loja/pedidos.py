"""Pedidos de venda.

Fluxo normal: o vendedor cria o pedido (o estoque baixa na hora), o
cliente paga e o pedido fica 'pago'. Um pedido pode ser cancelado; nesse
caso os itens voltam para o estoque.
"""
import logging

from . import config, db, descontos
from .estoque import devolver_itens_ao_estoque

log = logging.getLogger(__name__)


def criar_pedido(conn, cliente_id, itens, vendedor_id, cupom=None, observacao=""):
    """Cria um pedido e baixa o estoque dos produtos.

    itens: lista de dicts {"produto_id": int, "quantidade": int}.
    vendedor_id: id do usuário que está vendendo.
    cupom: código promocional opcional.

    Devolve o id do pedido. Levanta ValueError se algo estiver errado;
    nesse caso nada é gravado.
    """
    # validação do cabeçalho
    if not itens:
        raise ValueError("Pedido sem itens")
    if len(itens) > config.MAX_ITENS_POR_PEDIDO:
        raise ValueError("Pedido com itens demais (máximo %d)" % config.MAX_ITENS_POR_PEDIDO)
    observacao = (observacao or "").strip()
    if len(observacao) > 500:
        raise ValueError("Observação muito longa")

    cliente = conn.execute(
        "SELECT id, nome FROM clientes WHERE id = ?", (cliente_id,)
    ).fetchone()
    if cliente is None:
        raise ValueError("Cliente %s não encontrado" % cliente_id)

    vendedor = conn.execute(
        "SELECT id, login, papel, ativo FROM usuarios WHERE id = ?", (vendedor_id,)
    ).fetchone()
    if vendedor is None:
        raise ValueError("Vendedor %s não encontrado" % vendedor_id)
    if not vendedor["ativo"]:
        raise ValueError("Vendedor inativo não pode vender")

    # junta itens repetidos (o balcão às vezes manda o mesmo produto duas vezes)
    quantidades = {}
    ordem = []
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
        if produto_id not in quantidades:
            quantidades[produto_id] = 0
            ordem.append(produto_id)
        quantidades[produto_id] += quantidade

    # carrega os produtos e confere o estoque
    linhas = []
    subtotal = 0
    for produto_id in ordem:
        produto = conn.execute(
            "SELECT id, codigo, nome, preco, estoque, ativo FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()
        if produto is None:
            raise ValueError("Produto %s não encontrado" % produto_id)
        if not produto["ativo"]:
            raise ValueError("Produto %s está fora de venda" % produto["codigo"])
        qtd = quantidades[produto_id]
        if produto["estoque"] < qtd:
            raise ValueError(
                "Estoque insuficiente para %s (disponível: %d, pedido: %d)"
                % (produto["nome"], produto["estoque"], qtd)
            )
        valor = produto["preco"] * qtd
        subtotal += valor
        linhas.append({
            "produto_id": produto_id,
            "quantidade": qtd,
            "preco_unitario": produto["preco"],
            "total": valor,
        })

    # preço final
    desconto = descontos.desconto_progressivo(subtotal)
    desconto_cupom = 0
    if cupom:
        if cupom == "BAIRRO10":
            desconto_cupom = subtotal * 10 // 100
        elif cupom == "PRIMEIRACOMPRA":
            # só vale se o cliente nunca comprou
            anteriores = conn.execute(
                "SELECT COUNT(*) FROM pedidos WHERE cliente_id = ? AND status != ?",
                (cliente_id, config.STATUS_CANCELADO),
            ).fetchone()[0]
            if anteriores:
                raise ValueError("Cupom PRIMEIRACOMPRA vale só na primeira compra")
            desconto_cupom = subtotal * 5 // 100
        elif cupom == "FRETEGRATIS":
            desconto_cupom = 1000
        else:
            raise ValueError("Cupom não reconhecido: %s" % cupom)
    desconto += desconto_cupom
    if desconto > subtotal:
        desconto = subtotal
    total = subtotal - desconto

    # gravação
    agora = db.agora()
    try:
        cur = conn.execute(
            "INSERT INTO pedidos (cliente_id, vendedor_id, subtotal, desconto, total, cupom,"
            " status, observacao, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cliente_id, vendedor_id, subtotal, desconto, total, cupom or None,
             config.STATUS_ABERTO, observacao, agora),
        )
        pedido_id = cur.lastrowid
        for linha in linhas:
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, total)"
                " VALUES (?, ?, ?, ?, ?)",
                (pedido_id, linha["produto_id"], linha["quantidade"],
                 linha["preco_unitario"], linha["total"]),
            )
            baixa = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (linha["quantidade"], linha["produto_id"], linha["quantidade"]),
            )
            if baixa.rowcount == 0:
                # outro caixa vendeu o mesmo produto no meio do caminho
                raise ValueError("Estoque mudou durante o pedido, tente de novo")
            conn.execute(
                "INSERT INTO movimentos_estoque (produto_id, tipo, quantidade, motivo, pedido_id,"
                " criado_em) VALUES (?, 'saida', ?, ?, ?, ?)",
                (linha["produto_id"], linha["quantidade"], "venda", pedido_id, agora),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    log.info(
        "pedido %s criado por %s para o cliente %s: total %s",
        pedido_id, vendedor["login"], cliente["nome"], total,
    )
    return pedido_id


def _itens(conn, pedido_id):
    linhas = conn.execute(
        "SELECT i.produto_id, p.codigo, p.nome, i.quantidade, i.preco_unitario, i.total"
        " FROM itens_pedido i JOIN produtos p ON p.id = i.produto_id"
        " WHERE i.pedido_id = ? ORDER BY i.id",
        (pedido_id,),
    ).fetchall()
    return db.linhas_para_dicts(linhas)


def _pedido(conn, linha):
    if linha is None:
        return None
    pedido = {
        "id": linha["id"],
        "cliente_id": linha["cliente_id"],
        "vendedor_id": linha["vendedor_id"],
        "subtotal": linha["subtotal"],
        "desconto": linha["desconto"],
        "total": linha["total"],
        "cupom": linha["cupom"],
        "status": linha["status"],
        "forma_pagamento": linha["forma_pagamento"],
        "criado_em": linha["criado_em"],
    }
    pedido["itens"] = _itens(conn, linha["id"])
    return pedido


def buscar_pedido(conn, pedido_id, usuario=None):
    """Devolve o pedido com seus itens, ou None.

    usuario: dict do usuário logado (veja autenticacao.usuario_da_sessao).
    """
    linha = conn.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return _pedido(conn, linha)


def listar_pedidos(conn, usuario, status=None):
    """Lista pedidos, do mais novo para o mais antigo.

    Vendedor vê só os pedidos que ele mesmo fez; admin vê a loja inteira.
    """
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


def cancelar_pedido(conn, pedido_id, usuario):
    """Cancela o pedido e devolve os itens ao estoque."""
    linha = conn.execute(
        "SELECT id, status FROM pedidos WHERE id = ?", (pedido_id,)
    ).fetchone()
    if linha is None:
        raise ValueError("Pedido %s não encontrado" % pedido_id)
    if linha["status"] == config.STATUS_CANCELADO:
        raise ValueError("Pedido já está cancelado")
    try:
        devolver_itens_ao_estoque(conn, pedido_id)
        conn.execute(
            "UPDATE pedidos SET status = ?, cancelado_em = ? WHERE id = ?",
            (config.STATUS_CANCELADO, db.agora(), pedido_id),
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
        (config.STATUS_PAGO, forma, db.agora(), pedido_id),
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
    desconto = descontos.calcular_desconto(subtotal, cupom)
    return {"subtotal": subtotal, "desconto": desconto, "total": subtotal - desconto}
