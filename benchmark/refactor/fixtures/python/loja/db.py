"""Acesso ao banco SQLite da loja."""
import logging
import sqlite3
from datetime import datetime

from . import config

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    telefone TEXT NOT NULL DEFAULT '',
    cep TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    preco INTEGER NOT NULL CHECK (preco >= 0),
    estoque INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    estoque_minimo INTEGER NOT NULL DEFAULT 5,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movimentos_estoque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    tipo TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    motivo TEXT NOT NULL DEFAULT '',
    pedido_id INTEGER,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    senha_hash TEXT NOT NULL,
    papel TEXT NOT NULL DEFAULT 'vendedor',
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessoes (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    criado_em TEXT NOT NULL,
    expira_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    vendedor_id INTEGER NOT NULL REFERENCES usuarios(id),
    subtotal INTEGER NOT NULL,
    desconto INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL,
    cupom TEXT,
    status TEXT NOT NULL DEFAULT 'aberto',
    forma_pagamento TEXT,
    pago_em TEXT,
    cancelado_em TEXT,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade INTEGER NOT NULL,
    preco_unitario INTEGER NOT NULL,
    total INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL DEFAULT '',
    telefone TEXT NOT NULL DEFAULT '',
    prazo_entrega_dias INTEGER NOT NULL DEFAULT 7,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id),
    total INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberta',
    criado_em TEXT NOT NULL,
    recebida_em TEXT
);

CREATE TABLE IF NOT EXISTS itens_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id INTEGER NOT NULL REFERENCES compras(id),
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade INTEGER NOT NULL,
    custo_unitario INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS caixas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    valor_inicial INTEGER NOT NULL,
    aberto_em TEXT NOT NULL,
    fechado_em TEXT,
    valor_contado INTEGER
);

CREATE TABLE IF NOT EXISTS movimentos_caixa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caixa_id INTEGER NOT NULL REFERENCES caixas(id),
    tipo TEXT NOT NULL,
    valor INTEGER NOT NULL,
    motivo TEXT NOT NULL DEFAULT '',
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entregas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL UNIQUE REFERENCES pedidos(id),
    cep TEXT NOT NULL,
    endereco TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL,
    taxa INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'agendada',
    criado_em TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_vendedor ON pedidos(vendedor_id);
CREATE INDEX IF NOT EXISTS idx_itens_pedido ON itens_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_mov_produto ON movimentos_estoque(produto_id);
"""

# colunas que entraram depois da primeira versão do banco
_COLUNAS_NOVAS = [
    ("pedidos", "observacao", "TEXT NOT NULL DEFAULT ''"),
    ("clientes", "atualizado_em", "TEXT"),
]


def conectar(caminho=None):
    """Abre (ou cria) o banco e devolve a conexão já com as tabelas criadas.

    As linhas voltam como sqlite3.Row, que aceita acesso por nome de coluna.
    """
    if caminho is None:
        caminho = config.BANCO_PADRAO
    conn = sqlite3.connect(str(caminho))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    inicializar_banco(conn)
    return conn


def inicializar_banco(conn):
    """Cria as tabelas que faltam e aplica as colunas novas em bancos antigos."""
    conn.executescript(SCHEMA)
    _aplicar_colunas_novas(conn)
    conn.commit()


def _aplicar_colunas_novas(conn):
    for tabela, coluna, definicao in _COLUNAS_NOVAS:
        pragma = "PRAGMA table_info(%s)" % tabela
        existentes = [r[1] for r in conn.execute(pragma)]
        if coluna not in existentes:
            log.info("adicionando coluna %s.%s", tabela, coluna)
            alter = "ALTER TABLE %s ADD COLUMN %s %s" % (tabela, coluna, definicao)
            conn.execute(alter)


def agora():
    """Data e hora atual no formato gravado no banco."""
    return datetime.now().strftime(config.FORMATO_DATA_HORA)


def linha_para_dict(linha):
    if linha is None:
        return None
    return {k: linha[k] for k in linha.keys()}


def linhas_para_dicts(linhas):
    return [linha_para_dict(l) for l in linhas]

