'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loja, bancoComDados } = require('./apoio');

test('cria pedido, calcula o total e baixa o estoque', () => {
  const { db, vendedor, cliente, arroz, feijao } = bancoComDados();
  const ped = loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: arroz.id, quantidade: 2 }, { produtoId: feijao.id, quantidade: 3 }],
  });
  assert.strictEqual(ped.subtotal, 2 * 2500 + 3 * 899);
  assert.strictEqual(ped.desconto, 0);
  assert.strictEqual(ped.total, 7697);
  assert.strictEqual(ped.status, 'aberto');
  assert.strictEqual(ped.itens.length, 2);
  assert.strictEqual(loja.buscarProduto(db, arroz.id).estoque, 48);
  assert.strictEqual(loja.buscarProduto(db, feijao.id).estoque, 37);
  loja.fecharBanco(db);
});

test('itens repetidos do mesmo produto sao somados', () => {
  const { db, vendedor, cliente, feijao } = bancoComDados();
  const ped = loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: feijao.id, quantidade: 1 }, { produtoId: feijao.id, quantidade: 2 }],
  });
  assert.strictEqual(ped.itens.length, 1);
  assert.strictEqual(ped.itens[0].quantidade, 3);
  loja.fecharBanco(db);
});

test('cupom BAIRRO10 da 10% de desconto', () => {
  const { db, vendedor, cliente, arroz } = bancoComDados();
  const ped = loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: arroz.id, quantidade: 8 }],
    cupom: 'bairro10',
  });
  assert.strictEqual(ped.subtotal, 20000);
  assert.strictEqual(ped.desconto, 2000);
  assert.strictEqual(ped.total, 18000);
  assert.strictEqual(ped.cupom, 'BAIRRO10');
  loja.fecharBanco(db);
});

test('pedido grande ganha 10% de desconto', () => {
  const { db, vendedor, cliente, arroz } = bancoComDados();
  const ped = loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: arroz.id, quantidade: 32 }],
  });
  assert.strictEqual(ped.subtotal, 80000);
  assert.strictEqual(ped.desconto, 8000);
  assert.strictEqual(ped.total, 72000);
  loja.fecharBanco(db);
});

test('recusa pedido sem estoque suficiente e nao grava nada', () => {
  const { db, vendedor, cliente, cafe } = bancoComDados();
  assert.throws(() => loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: cafe.id, quantidade: 10 }],
  }));
  assert.strictEqual(loja.buscarProduto(db, cafe.id).estoque, 3);
  assert.strictEqual(loja.listarPedidos(db, { id: 0, papel: 'admin' }).length, 0);
  loja.fecharBanco(db);
});

test('registra pagamento', () => {
  const { db, vendedor, cliente, feijao } = bancoComDados();
  const ped = loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: feijao.id, quantidade: 1 }],
  });
  const pago = loja.registrarPagamento(db, ped.id, 'pix');
  assert.strictEqual(pago.status, 'pago');
  assert.strictEqual(pago.forma_pagamento, 'pix');
  assert.throws(() => loja.registrarPagamento(db, ped.id, 'pix'));
  loja.fecharBanco(db);
});

test('cancelamento devolve os itens ao estoque', () => {
  const { db, admin, vendedor, cliente, arroz } = bancoComDados();
  const ped = loja.criarPedido(db, {
    clienteId: cliente.id,
    usuarioId: vendedor.id,
    itens: [{ produtoId: arroz.id, quantidade: 5 }],
  });
  assert.strictEqual(loja.buscarProduto(db, arroz.id).estoque, 45);
  const c = loja.cancelarPedido(db, ped.id, admin);
  assert.strictEqual(c.status, 'cancelado');
  assert.strictEqual(loja.buscarProduto(db, arroz.id).estoque, 50);
  assert.throws(() => loja.cancelarPedido(db, ped.id, admin));
  loja.fecharBanco(db);
});

test('orcamento calcula sem gravar pedido', () => {
  const { db, admin, arroz, feijao } = bancoComDados();
  const orc = loja.calcularOrcamento(db, [{ produtoId: arroz.id, quantidade: 4 }, { produtoId: feijao.id, quantidade: 2 }]);
  assert.strictEqual(orc.subtotal, 11798);
  assert.strictEqual(orc.total, 11798);
  assert.strictEqual(loja.listarPedidos(db, admin).length, 0);
  assert.strictEqual(loja.buscarProduto(db, arroz.id).estoque, 50);
  loja.fecharBanco(db);
});
