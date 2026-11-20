'use strict';

// Cadastro de clientes.

const { agora, linha, linhas, transacao } = require('./db');
const { formatarCPF, ufPorCEP } = require('./util/documentos');
const { hoje, somarDias } = require('./util/datas');

function soDigitos(v) {
  return String(v || '').replace(/[^0-9]/g, '');
}

// validacao de CPF do cadastro
function cpfValido(cpf) {
  const n = soDigitos(cpf);
  if (n.length != 11) return false;
  let soma = 0;
  for (let i = 0; i < 9; i++) soma += Number(n.charAt(i)) * (10 - i);
  let resto = 11 - (soma % 11);
  let dv1 = resto >= 10 ? 0 : resto;
  if (dv1 != Number(n.charAt(9))) return false;
  soma = 0;
  for (let i = 0; i < 10; i++) soma += Number(n.charAt(i)) * (11 - i);
  resto = 11 - (soma % 11);
  let dv2 = resto >= 10 ? 0 : resto;
  return dv2 == Number(n.charAt(10));
}

function emailValido(email) {
  return /^\S+@\S+$/.test(String(email).trim());
}

/**
 * Formata telefone brasileiro.
 * 11987654321 -> (11) 98765-4321
 * 1134567890  -> (11) 3456-7890
 * Qualquer outra coisa volta como veio.
 */
function formatarTelefone(telefone) {
  let n = soDigitos(telefone);
  if (n.length === 13 && n.startsWith('55')) n = n.slice(2);
  if (n.length === 12 && n.startsWith('55')) n = n.slice(2);
  if (n.length === 11) {
    return '(' + n.slice(0, 2) + ') ' + n.slice(2, 7) + '-' + n.slice(7);
  }
  if (n.length === 10) {
    return '(' + n.slice(0, 2) + ') ' + n.slice(2, 6) + '-' + n.slice(6);
  }
  return telefone == null ? '' : String(telefone);
}

function validarDadosCliente(dados, parcial) {
  if (!parcial || dados.nome !== undefined) {
    const nome = String(dados.nome || '').trim();
    if (nome.length < 3) {
      throw new Error('Nome do cliente deve ter pelo menos 3 letras');
    }
  }
  if (!parcial || dados.cpf !== undefined) {
    if (!cpfValido(dados.cpf)) {
      throw new Error('CPF invalido');
    }
  }
  if (dados.email) {
    if (!emailValido(dados.email)) {
      throw new Error('E-mail invalido');
    }
  }
  if (dados.telefone) {
    const t = soDigitos(dados.telefone);
    if (t.length < 10 || t.length > 13) {
      throw new Error('Telefone invalido');
    }
  }
  if (dados.cep) {
    if (soDigitos(dados.cep).length !== 8) {
      throw new Error('CEP invalido');
    }
  }
}

/**
 * Cadastra um cliente.
 * @param {DatabaseSync} db
 * @param {{nome:string, cpf:string, email?:string, telefone?:string, cep?:string, observacao?:string}} dados
 * @returns {object} cliente gravado
 */
function criarCliente(db, dados) {
  if (!dados) throw new Error('Dados do cliente nao informados');
  validarDadosCliente(dados, false);
  const cpf = formatarCPF(dados.cpf);
  const existente = db.prepare('SELECT id FROM clientes WHERE cpf = ?').get(cpf);
  if (existente) {
    throw new Error('CPF ja cadastrado');
  }
  const r = db.prepare(
    'INSERT INTO clientes (nome, cpf, email, telefone, cep, observacao, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).run(
    String(dados.nome).trim(),
    cpf,
    dados.email ? String(dados.email).trim().toLowerCase() : null,
    dados.telefone ? soDigitos(dados.telefone) : null,
    dados.cep ? soDigitos(dados.cep) : null,
    dados.observacao || null,
    agora()
  );
  return buscarCliente(db, Number(r.lastInsertRowid));
}

function buscarCliente(db, id) {
  return linha(db.prepare('SELECT * FROM clientes WHERE id = ?').get(Number(id)));
}

function buscarClientePorCPF(db, cpf) {
  return linha(db.prepare('SELECT * FROM clientes WHERE cpf = ?').get(formatarCPF(cpf)));
}

/**
 * Lista clientes em ordem alfabetica.
 */
function listarClientes(db) {
  return linhas(db.prepare('SELECT * FROM clientes ORDER BY nome, id').all());
}

/**
 * Busca clientes pelo nome (parte do nome, sem diferenciar maiusculas).
 */
function buscarClientesPorNome(db, nome) {
  const termo = String(nome || '').trim();
  if (!termo) return listarClientes(db);
  const sql = "SELECT * FROM clientes WHERE nome LIKE '%" + termo + "%' ORDER BY nome, id";
  return linhas(db.prepare(sql).all());
}

/**
 * Atualiza os campos informados. Campos ausentes ficam como estao.
 */
function atualizarCliente(db, id, dados) {
  const atual = buscarCliente(db, id);
  if (!atual) throw new Error('Cliente nao encontrado');
  dados = dados || {};
  validarDadosCliente(dados, true);

  const novo = {
    nome: dados.nome !== undefined ? String(dados.nome).trim() : atual.nome,
    cpf: dados.cpf !== undefined ? formatarCPF(dados.cpf) : atual.cpf,
    email: dados.email !== undefined ? (dados.email ? String(dados.email).trim().toLowerCase() : null) : atual.email,
    telefone: dados.telefone !== undefined ? (dados.telefone ? soDigitos(dados.telefone) : null) : atual.telefone,
    cep: dados.cep !== undefined ? (dados.cep ? soDigitos(dados.cep) : null) : atual.cep,
    observacao: dados.observacao !== undefined ? dados.observacao : atual.observacao,
  };

  if (novo.cpf !== atual.cpf) {
    const outro = db.prepare('SELECT id FROM clientes WHERE cpf = ? AND id <> ?').get(novo.cpf, atual.id);
    if (outro) throw new Error('CPF ja cadastrado');
  }

  db.prepare(
    'UPDATE clientes SET nome = ?, cpf = ?, email = ?, telefone = ?, cep = ?, observacao = ? WHERE id = ?'
  ).run(novo.nome, novo.cpf, novo.email, novo.telefone, novo.cep, novo.observacao, atual.id);
  return buscarCliente(db, atual.id);
}

/**
 * Remove o cliente. Cliente com pedido nao pode ser removido.
 */
function removerCliente(db, id) {
  const cli = buscarCliente(db, id);
  if (!cli) throw new Error('Cliente nao encontrado');
  const ped = db.prepare('SELECT COUNT(*) AS n FROM pedidos WHERE cliente_id = ?').get(cli.id);
  if (ped.n > 0) {
    throw new Error('Cliente possui pedidos e nao pode ser removido');
  }
  db.prepare('DELETE FROM clientes WHERE id = ?').run(cli.id);
  return true;
}

/**
 * Junta dois cadastros do mesmo cliente: os pedidos do segundo passam para o primeiro.
 */
function mesclarClientes(db, idManter, idRemover) {
  const manter = buscarCliente(db, idManter);
  const remover = buscarCliente(db, idRemover);
  if (!manter || !remover) throw new Error('Cliente nao encontrado');
  return transacao(db, () => {
    db.prepare('UPDATE pedidos SET cliente_id = ? WHERE cliente_id = ?').run(manter.id, remover.id);
    if (!manter.email && remover.email) {
      db.prepare('UPDATE clientes SET email = ? WHERE id = ?').run(remover.email, manter.id);
    }
    if (!manter.telefone && remover.telefone) {
      db.prepare('UPDATE clientes SET telefone = ? WHERE id = ?').run(remover.telefone, manter.id);
    }
    db.prepare('DELETE FROM clientes WHERE id = ?').run(remover.id);
    return buscarCliente(db, manter.id);
  });
}

/**
 * Dados do cliente prontos para exibir (documentos e telefone formatados).
 */
function clienteParaExibicao(cli) {
  if (!cli) return null;
  return {
    id: cli.id,
    nome: cli.nome,
    cpf: cli.cpf,
    email: cli.email || '',
    telefone: cli.telefone ? formatarTelefone(cli.telefone) : '',
    cep: cli.cep ? cli.cep.slice(0, 5) + '-' + cli.cep.slice(5) : '',
    uf: cli.cep ? ufPorCEP(cli.cep) || '' : '',
    observacao: cli.observacao || '',
  };
}

/**
 * Clientes que nao compram ha mais de N dias (ou nunca compraram), para a campanha do WhatsApp.
 */
function clientesSemCompra(db, dias, hojeIso) {
  const limite = somarDias(hojeIso || hoje(), -(dias || 90)) + ' 00:00:00';
  return linhas(db.prepare(
    'SELECT c.*, MAX(p.criado_em) AS ultima_compra FROM clientes c ' +
    "LEFT JOIN pedidos p ON p.cliente_id = c.id AND p.status <> 'cancelado' " +
    'GROUP BY c.id HAVING ultima_compra IS NULL OR ultima_compra < ? ORDER BY c.nome'
  ).all(limite));
}

module.exports = {
  clientesSemCompra,
  criarCliente,
  buscarCliente,
  buscarClientePorCPF,
  listarClientes,
  buscarClientesPorNome,
  atualizarCliente,
  removerCliente,
  mesclarClientes,
  formatarTelefone,
  clienteParaExibicao,
};
