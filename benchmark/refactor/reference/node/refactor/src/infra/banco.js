'use strict';

// Acesso ao banco SQLite da loja.
// Usa o modulo node:sqlite que ja vem com o Node (22.5+), sem dependencia externa.

const { DatabaseSync } = require('node:sqlite');
const fs = require('node:fs');
const path = require('node:path');

const VERSAO_SCHEMA = 3;

const SCHEMA = `
CREATE TABLE IF NOT EXISTS clientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  cpf TEXT NOT NULL UNIQUE,
  email TEXT,
  telefone TEXT,
  cep TEXT,
  observacao TEXT,
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT NOT NULL UNIQUE,
  nome TEXT NOT NULL,
  preco INTEGER NOT NULL,
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
  motivo TEXT,
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  login TEXT NOT NULL UNIQUE,
  nome TEXT NOT NULL,
  email TEXT,
  senha_hash TEXT NOT NULL,
  papel TEXT NOT NULL CHECK (papel IN ('admin', 'vendedor')),
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessoes (
  token TEXT PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  criada_em TEXT NOT NULL,
  expira_em INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pedidos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cliente_id INTEGER NOT NULL REFERENCES clientes(id),
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  subtotal INTEGER NOT NULL,
  desconto INTEGER NOT NULL DEFAULT 0,
  total INTEGER NOT NULL,
  cupom TEXT,
  cpf_nota TEXT,
  email_recibo TEXT,
  status TEXT NOT NULL DEFAULT 'aberto',
  forma_pagamento TEXT,
  pago_em TEXT,
  criado_em TEXT NOT NULL,
  cancelado_em TEXT,
  cancelado_por INTEGER
);

CREATE TABLE IF NOT EXISTS itens_pedido (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
  produto_id INTEGER NOT NULL REFERENCES produtos(id),
  quantidade INTEGER NOT NULL,
  preco_unitario INTEGER NOT NULL,
  total INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_itens_pedido ON itens_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_movimentos_produto ON movimentos_estoque(produto_id);

CREATE TABLE IF NOT EXISTS meta (
  chave TEXT PRIMARY KEY,
  valor TEXT
);
`;

/**
 * Abre (ou cria) o banco no caminho informado e garante que as tabelas existem.
 * Use ':memory:' para um banco temporario.
 * @param {string} caminho
 * @returns {DatabaseSync}
 */
function abrirBanco(caminho) {
  if (!caminho) {
    throw new Error('Caminho do banco nao informado');
  }
  if (caminho !== ':memory:') {
    const pasta = path.dirname(path.resolve(caminho));
    if (!fs.existsSync(pasta)) {
      fs.mkdirSync(pasta, { recursive: true });
    }
  }
  const db = new DatabaseSync(caminho);
  db.exec('PRAGMA foreign_keys = ON');
  db.exec(SCHEMA);
  const versao = db.prepare("SELECT valor FROM meta WHERE chave = 'versao'").get();
  if (!versao) {
    db.prepare("INSERT INTO meta (chave, valor) VALUES ('versao', ?)").run(String(VERSAO_SCHEMA));
  }
  return db;
}

function fecharBanco(db) {
  if (db && db.isOpen) {
    db.close();
  }
}

/**
 * Roda a funcao dentro de uma transacao. Se der erro, desfaz e repassa o erro.
 */
function transacao(db, fn) {
  db.exec('BEGIN');
  try {
    const resultado = fn();
    db.exec('COMMIT');
    return resultado;
  } catch (e) {
    db.exec('ROLLBACK');
    throw e;
  }
}

// Data e hora local no formato que gravamos no banco: AAAA-MM-DD HH:MM:SS
function agora() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
    ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
}

// O node:sqlite devolve objetos sem prototype; aqui viram objetos comuns.
function linha(row) {
  return row ? Object.assign({}, row) : null;
}

function linhas(rows) {
  return rows.map((r) => Object.assign({}, r));
}

module.exports = {
  abrirBanco,
  fecharBanco,
  transacao,
  agora,
  linha,
  linhas,
  VERSAO_SCHEMA,
};
