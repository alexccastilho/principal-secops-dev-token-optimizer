"""Cadastro de produtos.

Preço sempre em centavos. O estoque inicial informado no cadastro já
entra como movimento de entrada, para o histórico bater com o saldo.
"""
import logging
import re

from ..comum.validacao import exigir_centavos, normalizar_nome
from ..infra import banco, config
from .estoque import registrar_movimento

log = logging.getLogger(__name__)

_RE_CODIGO = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,19}$")


def _normalizar_codigo(codigo):
    codigo = (codigo or "").strip().upper()
    if not _RE_CODIGO.match(codigo):
        raise ValueError("Código de produto inválido: use letras, números e hífen (2 a 20)")
    return codigo


def _produto(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "codigo": linha["codigo"],
        "nome": linha["nome"],
        "preco": linha["preco"],
        "estoque": linha["estoque"],
        "estoque_minimo": linha["estoque_minimo"],
        "ativo": bool(linha["ativo"]),
    }


def cadastrar_produto(conn, codigo, nome, preco, estoque=0, estoque_minimo=None):
    """Cadastra um produto e devolve o id.

    preco: inteiro em centavos.
    """
    codigo = _normalizar_codigo(codigo)
    nome = normalizar_nome(nome, "Nome do produto")
    exigir_centavos(preco, "Preço")
    if estoque < 0:
        raise ValueError("Estoque inicial não pode ser negativo")
    if estoque_minimo is None:
        estoque_minimo = config.ESTOQUE_MINIMO_PADRAO

    if conn.execute("SELECT 1 FROM produtos WHERE codigo = ?", (codigo,)).fetchone():
        raise ValueError("Já existe produto com o código %s" % codigo)

    agora = banco.agora()
    cur = conn.execute(
        "INSERT INTO produtos (codigo, nome, preco, estoque, estoque_minimo, ativo, criado_em)"
        " VALUES (?, ?, ?, ?, ?, 1, ?)",
        (codigo, nome, preco, estoque, estoque_minimo, agora),
    )
    produto_id = cur.lastrowid
    if estoque:
        registrar_movimento(conn, produto_id, "entrada", estoque, "estoque inicial")
    conn.commit()
    log.info("produto %s (%s) cadastrado", produto_id, codigo)
    return produto_id


def buscar_produto(conn, produto_id):
    linha = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _produto(linha)


def buscar_produto_por_codigo(conn, codigo):
    codigo = (codigo or "").strip().upper()
    linha = conn.execute("SELECT * FROM produtos WHERE codigo = ?", (codigo,)).fetchone()
    return _produto(linha)


def buscar_produtos(conn, termo):
    """Produtos ativos cujo nome ou código contém o termo."""
    termo = (termo or "").strip()
    padrao = "%" + termo + "%"
    linhas = conn.execute(
        "SELECT * FROM produtos WHERE ativo = 1 AND (nome LIKE ? OR codigo LIKE ?)"
        " ORDER BY nome COLLATE NOCASE",
        (padrao, padrao),
    ).fetchall()
    return [_produto(l) for l in linhas]


def listar_produtos(conn, apenas_ativos=True):
    sql = "SELECT * FROM produtos"
    if apenas_ativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome COLLATE NOCASE"
    return [_produto(l) for l in conn.execute(sql)]


def atualizar_produto(conn, produto_id, nome=None, preco=None, estoque_minimo=None):
    """Altera nome, preço ou estoque mínimo. Estoque muda só por movimento."""
    produto = buscar_produto(conn, produto_id)
    if produto is None:
        return False
    novo_nome = produto["nome"]
    novo_preco = produto["preco"]
    novo_minimo = produto["estoque_minimo"]
    if nome is not None:
        novo_nome = normalizar_nome(nome, "Nome do produto")
    if preco is not None:
        novo_preco = exigir_centavos(preco, "Preço")
    if estoque_minimo is not None:
        if estoque_minimo < 0:
            raise ValueError("Estoque mínimo inválido")
        novo_minimo = estoque_minimo
    conn.execute(
        "UPDATE produtos SET nome = ?, preco = ?, estoque_minimo = ? WHERE id = ?",
        (novo_nome, novo_preco, novo_minimo, produto_id),
    )
    conn.commit()
    if novo_preco != produto["preco"]:
        log.info("preço do produto %s: %s -> %s", produto_id, produto["preco"], novo_preco)
    return True


def desativar_produto(conn, produto_id):
    """Tira o produto da venda sem apagar o histórico."""
    cur = conn.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,))
    conn.commit()
    return cur.rowcount > 0


def reativar_produto(conn, produto_id):
    cur = conn.execute("UPDATE produtos SET ativo = 1 WHERE id = ?", (produto_id,))
    conn.commit()
    return cur.rowcount > 0


def reajustar_precos(conn, percentual_reajuste):
    """Aplica reajuste percentual nos produtos ativos.

    Usado na virada do ano. Arredonda para o centavo mais próximo.
    Devolve a quantidade de produtos alterados.
    """
    if percentual_reajuste <= -100:
        raise ValueError("Reajuste inválido")
    alterados = 0
    for linha in conn.execute("SELECT id, preco FROM produtos WHERE ativo = 1").fetchall():
        novo = (linha["preco"] * (100 + percentual_reajuste) + 50) // 100
        conn.execute("UPDATE produtos SET preco = ? WHERE id = ?", (novo, linha["id"]))
        alterados += 1
    conn.commit()
    return alterados
