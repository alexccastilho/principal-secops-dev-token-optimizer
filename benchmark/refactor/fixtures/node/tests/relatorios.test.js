'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loja, bancoComDados } = require('./apoio');

function venda(ctx, itens, data) {
  return loja.criarPedido(ctx.db, {
    clienteId: ctx.cliente.id,
    usuarioId: ctx.vendedor.id,
    itens: itens,
    data: data,
  });
}

test('vendas por periodo ignoram cancelados', () => {
  const ctx = bancoComDados();
  venda(ctx, [{ produtoId: ctx.arroz.id, quantidade: 2 }], '2024-05-10');
  venda(ctx, [{ produtoId: ctx.feijao.id, quantidade: 1 }], '2024-05-11');
  const c = venda(ctx, [{ produtoId: ctx.feijao.id, quantidade: 4 }], '2024-05-11');
  venda(ctx, [{ produtoId: ctx.arroz.id, quantidade: 1 }], '2024-06-01');
  loja.cancelarPedido(ctx.db, c.id, ctx.admin);

  const v = loja.vendasPorPeriodo(ctx.db, '01/05/2024', '31/05/2024');
  assert.strictEqual(v.quantidade, 2);
  assert.strictEqual(v.total, 5000 + 899);
  assert.strictEqual(v.dias.length, 2);
  loja.fecharBanco(ctx.db);
});

test('produtos mais vendidos', () => {
  const ctx = bancoComDados();
  venda(ctx, [{ produtoId: ctx.arroz.id, quantidade: 1 }, { produtoId: ctx.feijao.id, quantidade: 5 }]);
  venda(ctx, [{ produtoId: ctx.feijao.id, quantidade: 2 }]);
  const top = loja.produtosMaisVendidos(ctx.db, { limite: 2 });
  assert.strictEqual(top.length, 2);
  assert.strictEqual(top[0].sku, 'FEIJAO1');
  assert.strictEqual(top[0].quantidade, 7);
  loja.fecharBanco(ctx.db);
});

test('relatorio de pedidos ordenado por total', () => {
  const ctx = bancoComDados();
  venda(ctx, [{ produtoId: ctx.feijao.id, quantidade: 1 }]);
  venda(ctx, [{ produtoId: ctx.arroz.id, quantidade: 3 }]);
  venda(ctx, [{ produtoId: ctx.arroz.id, quantidade: 1 }]);
  const lista = loja.relatorioPedidos(ctx.db, 'total', 'desc');
  assert.deepStrictEqual(lista.map((p) => p.total), [7500, 2500, 899]);
  assert.strictEqual(lista[0].cliente, 'Maria Aparecida');
  loja.fecharBanco(ctx.db);
});

test('exporta clientes em CSV com ponto e virgula', () => {
  const ctx = bancoComDados();
  const csv = loja.exportarClientesCSV(ctx.db, { bom: false });
  const linhas = csv.trim().split('\r\n');
  assert.strictEqual(linhas.length, 2);
  assert.ok(linhas[0].startsWith('id;nome;cpf;email'));
  assert.ok(linhas[1].includes('Maria Aparecida;529.982.247-25;maria@exemplo.com.br;(11) 98765-4321'));
  loja.fecharBanco(ctx.db);
});
