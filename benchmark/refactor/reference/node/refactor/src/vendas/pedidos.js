'use strict';

// Pedidos de venda: criacao, consulta, pagamento e cancelamento.

const { agora, linha, linhas, transacao } = require('../infra/banco');
const { atualizarEstoque } = require('../estoque/movimentos');
const { lerCupom, calcularDesconto, precificarItens, totalDosItens } = require('./descontos');
const { validarDadosPedido } = require('./validacaoPedido');
const { hoje, somarDias } = require('../comum/datas');
const { exigir } = require('../comum/validacao');

const FORMAS_PAGAMENTO = ['dinheiro', 'pix', 'cartao_credito', 'cartao_debito'];

function exigirUsuario(usuario) {
  exigir(usuario, 'Usuario nao informado');
}

/**
 * Vendedor so acessa os proprios pedidos; admin acessa qualquer um.
 */
function podeAcessar(usuario, pedido) {
  return usuario.papel === 'admin' || pedido.usuario_id === usuario.id;
}

function clienteJaComprou(db, clienteId) {
  const r = db.prepare(
    "SELECT COUNT(*) AS n FROM pedidos WHERE cliente_id = ? AND status <> 'cancelado'"
  ).get(clienteId);
  return r.n > 0;
}

/**
 * Subtotal, cupom e desconto do pedido.
 */
function precificarPedido(db, cliente, itens, cupomInformado) {
  const subtotal = totalDosItens(itens);
  const cupom = lerCupom(cupomInformado);
  if (cupom && cupom.somentePrimeiraCompra && clienteJaComprou(db, cliente.id)) {
    throw new Error('Cupom ' + cupom.codigo + ' vale apenas na primeira compra');
  }
  const desconto = calcularDesconto(subtotal, cupom);
  return { subtotal, desconto, total: subtotal - desconto, cupom: cupom ? cupom.codigo : null };
}

/**
 * Grava pedido e itens e baixa o estoque, tudo na mesma transacao.
 */
function gravarPedido(db, base, itens, precos) {
  return transacao(db, () => {
    const r = db.prepare(
      'INSERT INTO pedidos (cliente_id, usuario_id, subtotal, desconto, total, cupom, cpf_nota, email_recibo, status, criado_em) ' +
      'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    ).run(base.cliente.id, base.usuario.id, precos.subtotal, precos.desconto, precos.total, precos.cupom,
      base.cpfNota, base.emailRecibo, 'aberto', base.criadoEm);
    const id = Number(r.lastInsertRowid);
    const insItem = db.prepare(
      'INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, total) VALUES (?, ?, ?, ?, ?)'
    );
    for (const it of itens) {
      insItem.run(id, it.produto_id, it.quantidade, it.preco_unitario, it.total);
      atualizarEstoque(db, it.produto_id, -it.quantidade, 'venda', 'pedido ' + id);
    }
    return id;
  });
}

/**
 * Cria um pedido com os itens informados, aplica descontos, baixa o estoque e grava.
 *
 * dados = {
 *   clienteId, usuarioId,
 *   itens: [{ produtoId, quantidade }],
 *   cupom?, cpfNaNota?, emailRecibo?,
 *   data?  ('AAAA-MM-DD' ou 'DD/MM/AAAA'; padrao hoje)
 * }
 *
 * Retorna o pedido completo (mesmo formato de buscarPedido).
 */
function criarPedido(db, dados) {
  const base = validarDadosPedido(db, dados, agora());
  const itens = precificarItens(db, dados.itens, true);
  const precos = precificarPedido(db, base.cliente, itens, dados.cupom);
  return carregarPedido(db, gravarPedido(db, base, itens, precos));
}

function carregarPedido(db, id) {
  const ped = linha(db.prepare('SELECT * FROM pedidos WHERE id = ?').get(Number(id)));
  if (!ped) return null;
  ped.itens = linhas(db.prepare(
    'SELECT i.produto_id, p.sku, p.nome, i.quantidade, i.preco_unitario, i.total ' +
    'FROM itens_pedido i JOIN produtos p ON p.id = i.produto_id WHERE i.pedido_id = ? ORDER BY i.id'
  ).all(ped.id));
  return ped;
}

/**
 * Busca um pedido com os itens. Vendedor so ve os proprios pedidos.
 * @param {DatabaseSync} db
 * @param {number} id
 * @param {object} usuario usuario logado ({ id, papel })
 * @returns {object|null}
 */
function buscarPedido(db, id, usuario) {
  exigirUsuario(usuario);
  const ped = carregarPedido(db, id);
  if (!ped) return null;
  exigir(podeAcessar(usuario, ped), 'Acesso negado ao pedido ' + ped.id);
  return ped;
}

/**
 * Lista pedidos visiveis para o usuario. Vendedor ve so os dele; admin ve a loja inteira.
 * filtros: { status }
 */
function listarPedidos(db, usuario, filtros) {
  exigirUsuario(usuario);
  const status = (filtros && filtros.status) || null;
  const doUsuario = usuario.papel === 'admin' ? null : usuario.id;
  return linhas(db.prepare(
    'SELECT * FROM pedidos WHERE (? IS NULL OR usuario_id = ?) AND (? IS NULL OR status = ?) ORDER BY id'
  ).all(doUsuario, doUsuario, status, status));
}

/**
 * Registra o pagamento de um pedido em aberto.
 */
function registrarPagamento(db, id, forma) {
  const ped = carregarPedido(db, id);
  exigir(ped, 'Pedido nao encontrado');
  exigir(ped.status === 'aberto', 'Pedido nao esta em aberto (status: ' + (ped && ped.status) + ')');
  exigir(FORMAS_PAGAMENTO.includes(forma), 'Forma de pagamento invalida: ' + forma);
  db.prepare("UPDATE pedidos SET status = 'pago', forma_pagamento = ?, pago_em = ? WHERE id = ?")
    .run(forma, agora(), ped.id);
  return carregarPedido(db, ped.id);
}

/**
 * Cancela o pedido e devolve os itens ao estoque.
 * Pedido pago tambem pode ser cancelado (o estorno e feito no caixa).
 * Vendedor so cancela os proprios pedidos.
 */
function cancelarPedido(db, id, usuario) {
  exigirUsuario(usuario);
  const ped = carregarPedido(db, id);
  exigir(ped, 'Pedido nao encontrado');
  exigir(podeAcessar(usuario, ped), 'Acesso negado ao pedido ' + ped.id);
  exigir(ped.status !== 'cancelado', 'Pedido ja cancelado');
  transacao(db, () => {
    for (const it of ped.itens) {
      atualizarEstoque(db, it.produto_id, it.quantidade, 'devolucao', 'cancelamento pedido ' + ped.id);
    }
    db.prepare("UPDATE pedidos SET status = 'cancelado', cancelado_em = ?, cancelado_por = ? WHERE id = ?")
      .run(agora(), usuario.id, ped.id);
  });
  return carregarPedido(db, ped.id);
}

/**
 * Pedidos de um cliente (historico), do mais recente para o mais antigo.
 */
function pedidosDoCliente(db, clienteId) {
  return linhas(db.prepare(
    'SELECT * FROM pedidos WHERE cliente_id = ? ORDER BY criado_em DESC, id DESC'
  ).all(Number(clienteId)));
}

/**
 * Pedidos em aberto ha mais de N dias (para cobrar ou cancelar).
 */
function pedidosEmAbertoAntigos(db, dias) {
  const limite = somarDias(hoje(), -(dias || 7)) + ' 00:00:00';
  return linhas(db.prepare(
    "SELECT * FROM pedidos WHERE status = 'aberto' AND criado_em < ? ORDER BY criado_em"
  ).all(limite));
}

module.exports = {
  criarPedido,
  carregarPedido,
  buscarPedido,
  listarPedidos,
  registrarPagamento,
  cancelarPedido,
  pedidosDoCliente,
  pedidosEmAbertoAntigos,
  FORMAS_PAGAMENTO,
};
