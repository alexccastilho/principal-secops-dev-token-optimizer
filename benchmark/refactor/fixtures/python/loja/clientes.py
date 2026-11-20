"""Cadastro de clientes."""
import logging
import re
import sqlite3

from . import db
from .util import formatar_cep, somente_digitos

log = logging.getLogger(__name__)

TAMANHO_MAXIMO_NOME = 120


def _cpf_valido(cpf):
    cpf = re.sub(r"[^0-9]", "", cpf or "")
    if len(cpf) != 11:
        return False
    # primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = 11 - (soma % 11)
    if d1 >= 10:
        d1 = 0
    if d1 != int(cpf[9]):
        return False
    # segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = 11 - (soma % 11)
    if d2 >= 10:
        d2 = 0
    return d2 == int(cpf[10])


def _email_valido(email):
    if not email or len(email) > 200:
        return False
    return re.match(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$", email) is not None


def formatar_telefone(numero):
    """Formata telefone brasileiro com DDD.

    '11987654321' -> '(11) 98765-4321'
    '1134567890'  -> '(11) 3456-7890'
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


def _cliente(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "cpf": linha["cpf"],
        "email": linha["email"],
        "telefone": linha["telefone"],
        "cep": linha["cep"],
        "criado_em": linha["criado_em"],
    }


def _normalizar_nome(nome):
    nome = " ".join((nome or "").split())
    if not nome:
        raise ValueError("Nome do cliente é obrigatório")
    if len(nome) > TAMANHO_MAXIMO_NOME:
        raise ValueError("Nome muito longo")
    return nome


def cadastrar_cliente(conn, nome, cpf, email, telefone="", cep=""):
    """Cadastra um cliente e devolve o id.

    O CPF é gravado só com dígitos; telefone e CEP já formatados.
    Levanta ValueError para dados inválidos ou CPF repetido.
    """
    nome = _normalizar_nome(nome)
    if not _cpf_valido(cpf):
        raise ValueError("CPF inválido")
    email = (email or "").strip().lower()
    if not _email_valido(email):
        raise ValueError("E-mail inválido")
    cpf = somente_digitos(cpf)
    if telefone:
        telefone = formatar_telefone(telefone)
    if cep:
        cep = formatar_cep(cep)

    existente = conn.execute("SELECT id FROM clientes WHERE cpf = ?", (cpf,)).fetchone()
    if existente:
        raise ValueError("Já existe cliente com este CPF")

    cur = conn.execute(
        "INSERT INTO clientes (nome, cpf, email, telefone, cep, criado_em) VALUES (?, ?, ?, ?, ?, ?)",
        (nome, cpf, email, telefone or "", cep or "", db.agora()),
    )
    conn.commit()
    log.info("cliente %s cadastrado", cur.lastrowid)
    return cur.lastrowid


def buscar_cliente(conn, cliente_id):
    linha = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    return _cliente(linha)


def buscar_cliente_por_cpf(conn, cpf):
    linha = conn.execute(
        "SELECT * FROM clientes WHERE cpf = ?", (somente_digitos(cpf),)
    ).fetchone()
    return _cliente(linha)


def listar_clientes(conn, limite=None):
    """Lista os clientes em ordem alfabética."""
    sql = "SELECT * FROM clientes ORDER BY nome COLLATE NOCASE"
    params = ()
    if limite:
        sql += " LIMIT ?"
        params = (int(limite),)
    return [_cliente(l) for l in conn.execute(sql, params)]


def buscar_clientes_por_nome(conn, termo):
    """Busca clientes cujo nome contém o termo (sem diferenciar maiúsculas)."""
    termo = (termo or "").strip()
    if not termo:
        return listar_clientes(conn)
    sql = "SELECT * FROM clientes WHERE nome LIKE '%" + termo + "%' ORDER BY nome COLLATE NOCASE"
    return [_cliente(l) for l in conn.execute(sql).fetchall()]


def historico_cliente(conn, cliente_id):
    """Pedidos do cliente, do mais novo para o mais antigo (sem os itens)."""
    linhas = conn.execute(
        "SELECT id, total, status, criado_em FROM pedidos WHERE cliente_id = ?"
        " ORDER BY id DESC",
        (cliente_id,),
    ).fetchall()
    return [
        {"pedido_id": l["id"], "total": l["total"], "status": l["status"],
         "criado_em": l["criado_em"]}
        for l in linhas
    ]


def atualizar_cliente(conn, cliente_id, nome=None, email=None, telefone=None, cep=None):
    """Atualiza os campos informados. Devolve True se o cliente existia."""
    atual = buscar_cliente(conn, cliente_id)
    if atual is None:
        return False
    campos = {}
    if nome is not None:
        campos["nome"] = _normalizar_nome(nome)
    if email is not None:
        email = email.strip().lower()
        if not _email_valido(email):
            raise ValueError("E-mail inválido")
        campos["email"] = email
    if telefone is not None:
        campos["telefone"] = formatar_telefone(telefone) if telefone else ""
    if cep is not None:
        campos["cep"] = formatar_cep(cep) if cep else ""
    if not campos:
        return True

    partes = ", ".join("%s = ?" % c for c in campos)
    valores = list(campos.values()) + [db.agora(), cliente_id]
    sql = "UPDATE clientes SET %s, atualizado_em = ? WHERE id = ?" % partes
    conn.execute(sql, valores)
    conn.commit()
    return True


def remover_cliente(conn, cliente_id):
    """Remove o cliente. Cliente com pedido não pode ser removido."""
    qtd = conn.execute(
        "SELECT COUNT(*) FROM pedidos WHERE cliente_id = ?", (cliente_id,)
    ).fetchone()[0]
    if qtd:
        raise ValueError("Cliente tem %d pedido(s) e não pode ser removido" % qtd)
    cur = conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    return cur.rowcount > 0


def mesclar_clientes(conn, id_principal, id_duplicado):
    """Junta dois cadastros do mesmo cliente.

    Os pedidos do duplicado passam para o principal e o duplicado é apagado.
    Campos vazios do principal são preenchidos com os do duplicado.
    """
    principal = buscar_cliente(conn, id_principal)
    duplicado = buscar_cliente(conn, id_duplicado)
    if principal is None or duplicado is None:
        raise ValueError("Cliente não encontrado")
    if id_principal == id_duplicado:
        return principal
    try:
        conn.execute(
            "UPDATE pedidos SET cliente_id = ? WHERE cliente_id = ?",
            (id_principal, id_duplicado),
        )
        telefone = principal["telefone"] or duplicado["telefone"]
        cep = principal["cep"] or duplicado["cep"]
        conn.execute(
            "UPDATE clientes SET telefone = ?, cep = ? WHERE id = ?",
            (telefone, cep, id_principal),
        )
        conn.execute("DELETE FROM clientes WHERE id = ?", (id_duplicado,))
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    return buscar_cliente(conn, id_principal)
