"""Cadastro de clientes."""
import logging

from ..comum.formatacao import formatar_cep, formatar_telefone
from ..comum.validacao import exigir_cpf, normalizar_email, normalizar_nome, somente_digitos
from ..infra import banco

log = logging.getLogger(__name__)

TAMANHO_MAXIMO_NOME = 120
_CAMPOS = ("id", "nome", "cpf", "email", "telefone", "cep", "criado_em")


def _cliente(linha):
    if linha is None:
        return None
    return {campo: linha[campo] for campo in _CAMPOS}


def _nome(nome):
    return normalizar_nome(nome, "Nome do cliente", TAMANHO_MAXIMO_NOME)


def cadastrar_cliente(conn, nome, cpf, email, telefone="", cep=""):
    """Cadastra um cliente e devolve o id.

    O CPF é gravado só com dígitos; telefone e CEP já formatados.
    ValueError para dados inválidos ou CPF repetido.
    """
    nome = _nome(nome)
    cpf = exigir_cpf(cpf)
    email = normalizar_email(email)
    telefone = formatar_telefone(telefone) if telefone else ""
    cep = formatar_cep(cep) if cep else ""
    if conn.execute("SELECT 1 FROM clientes WHERE cpf = ?", (cpf,)).fetchone():
        raise ValueError("Já existe cliente com este CPF")
    cur = conn.execute(
        "INSERT INTO clientes (nome, cpf, email, telefone, cep, criado_em) VALUES (?, ?, ?, ?, ?, ?)",
        (nome, cpf, email, telefone, cep, banco.agora()),
    )
    conn.commit()
    log.info("cliente %s cadastrado", cur.lastrowid)
    return cur.lastrowid


def cpf_ja_cadastrado(conn, cpf):
    return conn.execute("SELECT 1 FROM clientes WHERE cpf = ?", (cpf,)).fetchone() is not None


def buscar_cliente(conn, cliente_id):
    return _cliente(conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone())


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
    linhas = conn.execute(
        "SELECT * FROM clientes WHERE nome LIKE ? ORDER BY nome COLLATE NOCASE",
        ("%" + termo + "%",),
    ).fetchall()
    return [_cliente(l) for l in linhas]


def historico_cliente(conn, cliente_id):
    """Pedidos do cliente, do mais novo para o mais antigo (sem os itens)."""
    linhas = conn.execute(
        "SELECT id, total, status, criado_em FROM pedidos WHERE cliente_id = ? ORDER BY id DESC",
        (cliente_id,),
    ).fetchall()
    return [{"pedido_id": l["id"], "total": l["total"], "status": l["status"],
             "criado_em": l["criado_em"]} for l in linhas]


def atualizar_cliente(conn, cliente_id, nome=None, email=None, telefone=None, cep=None):
    """Atualiza os campos informados. Devolve True se o cliente existia."""
    atual = buscar_cliente(conn, cliente_id)
    if atual is None:
        return False
    novo = dict(atual)
    if nome is not None:
        novo["nome"] = _nome(nome)
    if email is not None:
        novo["email"] = normalizar_email(email)
    if telefone is not None:
        novo["telefone"] = formatar_telefone(telefone) if telefone else ""
    if cep is not None:
        novo["cep"] = formatar_cep(cep) if cep else ""
    if novo == atual:
        return True
    conn.execute(
        "UPDATE clientes SET nome = ?, email = ?, telefone = ?, cep = ?, atualizado_em = ?"
        " WHERE id = ?",
        (novo["nome"], novo["email"], novo["telefone"], novo["cep"], banco.agora(), cliente_id),
    )
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
