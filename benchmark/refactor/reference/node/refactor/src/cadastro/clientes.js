'use strict';

// Cadastro de clientes.

const { agora, linha, linhas } = require('../infra/banco');
const { formatarCPF, limparNumeros, ufPorCEP } = require('../comum/documentos');
const { validarCPF, validarEmail, telefoneValido, cepValido, exigir } = require('../comum/validacao');
const { hoje, somarDias } = require('../comum/datas');

/**
 * Formata telefone brasileiro.
 * 11987654321 -> (11) 98765-4321
 * 1134567890  -> (11) 3456-7890
 * Qualquer outra coisa volta como veio.
 */
function formatarTelefone(telefone) {
  let n = limparNumeros(telefone);
  if ((n.length === 13 || n.length === 12) && n.startsWith('55')) n = n.slice(2);
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
    exigir(String(dados.nome || '').trim().length >= 3, 'Nome do cliente deve ter pelo menos 3 letras');
  }
  if (!parcial || dados.cpf !== undefined) {
    exigir(validarCPF(dados.cpf), 'CPF invalido');
  }
  if (dados.email) exigir(validarEmail(dados.email), 'E-mail invalido');
  if (dados.telefone) exigir(telefoneValido(dados.telefone), 'Telefone invalido');
  if (dados.cep) exigir(cepValido(dados.cep), 'CEP invalido');
}

function emailNormalizado(email) {
  return email ? String(email).trim().toLowerCase() : null;
}

function digitosOuNulo(valor) {
  return valor ? limparNumeros(valor) : null;
}

function exigirCPFLivre(db, cpf, idAtual) {
  const outro = db.prepare('SELECT id FROM clientes WHERE cpf = ? AND id <> ?').get(cpf, idAtual || 0);
  exigir(!outro, 'CPF ja cadastrado');
}

/**
 * Cadastra um cliente.
 * @param {DatabaseSync} db
 * @param {{nome:string, cpf:string, email?:string, telefone?:string, cep?:string, observacao?:string}} dados
 * @returns {object} cliente gravado
 */
function criarCliente(db, dados) {
  exigir(dados, 'Dados do cliente nao informados');
  validarDadosCliente(dados, false);
  const cpf = formatarCPF(dados.cpf);
  exigirCPFLivre(db, cpf);
  const r = db.prepare(
    'INSERT INTO clientes (nome, cpf, email, telefone, cep, observacao, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).run(
    String(dados.nome).trim(),
    cpf,
    emailNormalizado(dados.email),
    digitosOuNulo(dados.telefone),
    digitosOuNulo(dados.cep),
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
  return linhas(db.prepare('SELECT * FROM clientes WHERE nome LIKE ? ORDER BY nome, id').all('%' + termo + '%'));
}

/**
 * Atualiza os campos informados. Campos ausentes ficam como estao.
 */
function atualizarCliente(db, id, dados) {
  const atual = buscarCliente(db, id);
  exigir(atual, 'Cliente nao encontrado');
  dados = dados || {};
  validarDadosCliente(dados, true);

  const valor = (campo, converter) => (dados[campo] !== undefined ? converter(dados[campo]) : atual[campo]);
  const novo = {
    nome: valor('nome', (v) => String(v).trim()),
    cpf: valor('cpf', formatarCPF),
    email: valor('email', emailNormalizado),
    telefone: valor('telefone', digitosOuNulo),
    cep: valor('cep', digitosOuNulo),
    observacao: valor('observacao', (v) => v),
  };
  if (novo.cpf !== atual.cpf) exigirCPFLivre(db, novo.cpf, atual.id);

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
  exigir(cli, 'Cliente nao encontrado');
  const ped = db.prepare('SELECT COUNT(*) AS n FROM pedidos WHERE cliente_id = ?').get(cli.id);
  exigir(ped.n === 0, 'Cliente possui pedidos e nao pode ser removido');
  db.prepare('DELETE FROM clientes WHERE id = ?').run(cli.id);
  return true;
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
  criarCliente,
  buscarCliente,
  buscarClientePorCPF,
  listarClientes,
  buscarClientesPorNome,
  atualizarCliente,
  removerCliente,
  formatarTelefone,
  clienteParaExibicao,
  clientesSemCompra,
};
