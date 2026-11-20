'use strict';

// Conferencias dos dados de entrada de um pedido (antes de qualquer calculo ou gravacao).

const { validarCPF, validarEmail, exigir } = require('../comum/validacao');
const { formatarCPF } = require('../comum/documentos');
const { converterDataBR } = require('../comum/datas');

const QUANTIDADE_MAXIMA_POR_ITEM = 999;

/**
 * Lista de itens nao vazia, cada um com produto e quantidade inteira positiva.
 */
function exigirItens(itens) {
  exigir(Array.isArray(itens) && itens.length > 0, 'Pedido sem itens');
  for (const it of itens) {
    exigir(it && it.produtoId, 'Item sem produto');
    exigir(Number.isInteger(it.quantidade) && it.quantidade > 0, 'Quantidade invalida para o produto ' + it.produtoId);
    exigir(it.quantidade <= QUANTIDADE_MAXIMA_POR_ITEM, 'Quantidade acima do permitido por item');
  }
}

function carregarCliente(db, clienteId) {
  exigir(clienteId, 'Cliente nao informado');
  const cliente = db.prepare('SELECT * FROM clientes WHERE id = ?').get(Number(clienteId));
  exigir(cliente, 'Cliente nao encontrado');
  return cliente;
}

function carregarUsuarioAtivo(db, usuarioId) {
  exigir(usuarioId, 'Usuario nao informado');
  const usuario = db.prepare('SELECT id, papel, ativo FROM usuarios WHERE id = ?').get(Number(usuarioId));
  exigir(usuario && usuario.ativo, 'Usuario invalido ou inativo');
  return usuario;
}

/**
 * CPF na nota (opcional). Devolve formatado ou null.
 */
function cpfDaNota(cpf) {
  if (!cpf) return null;
  exigir(validarCPF(cpf), 'CPF da nota invalido');
  return formatarCPF(cpf);
}

/**
 * E-mail do recibo: o informado (validado) ou o do cadastro do cliente.
 */
function emailDoRecibo(email, cliente) {
  if (!email) return cliente.email || null;
  exigir(validarEmail(email), 'E-mail do recibo invalido');
  return String(email).trim().toLowerCase();
}

/**
 * Data e hora do pedido: a data informada com a hora atual, ou agora.
 */
function dataDoPedido(data, agoraTexto) {
  if (!data) return agoraTexto;
  return converterDataBR(data) + agoraTexto.slice(10);
}

/**
 * Confere os dados do pedido e devolve o que foi carregado e normalizado.
 */
function validarDadosPedido(db, dados, agoraTexto) {
  exigir(dados, 'Dados do pedido nao informados');
  const cliente = carregarCliente(db, dados.clienteId);
  const usuario = carregarUsuarioAtivo(db, dados.usuarioId);
  exigirItens(dados.itens);
  return {
    cliente,
    usuario,
    cpfNota: cpfDaNota(dados.cpfNaNota),
    emailRecibo: emailDoRecibo(dados.emailRecibo, cliente),
    criadoEm: dataDoPedido(dados.data, agoraTexto),
  };
}

module.exports = {
  exigirItens,
  validarDadosPedido,
};
