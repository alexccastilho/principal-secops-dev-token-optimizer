'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loja, bancoNovo } = require('./apoio');

test('cadastra produto com estoque inicial e registra o movimento', () => {
  const db = bancoNovo();
  const p = loja.criarProduto(db, { sku: 'leite1', nome: 'Leite 1L', preco: 549, estoque: 24 });
  assert.strictEqual(p.sku, 'LEITE1');
  assert.strictEqual(p.estoque, 24);
  const mov = loja.listarMovimentos(db, p.id);
  assert.strictEqual(mov.length, 1);
  assert.strictEqual(mov[0].tipo, 'entrada');
  assert.strictEqual(mov[0].quantidade, 24);
  loja.fecharBanco(db);
});

test('nao aceita SKU repetido nem preco invalido', () => {
  const db = bancoNovo();
  loja.criarProduto(db, { sku: 'LEITE1', nome: 'Leite 1L', preco: 549 });
  assert.throws(() => loja.criarProduto(db, { sku: 'leite1', nome: 'Outro leite', preco: 600 }));
  assert.throws(() => loja.criarProduto(db, { sku: 'PAO', nome: 'Pao', preco: 1.5 }));
  loja.fecharBanco(db);
});

test('entrada e saida de estoque', () => {
  const db = bancoNovo();
  const p = loja.criarProduto(db, { sku: 'OVO12', nome: 'Ovos duzia', preco: 1290, estoque: 10 });
  assert.strictEqual(loja.registrarEntrada(db, p.id, 5, 'fornecedor').estoque, 15);
  assert.strictEqual(loja.registrarSaida(db, p.id, 2, 'quebrados').estoque, 13);
  assert.strictEqual(loja.listarMovimentos(db, p.id).length, 3);
  assert.throws(() => loja.registrarEntrada(db, p.id, 0));
  loja.fecharBanco(db);
});

test('lista produtos com estoque baixo', () => {
  const db = bancoNovo();
  loja.criarProduto(db, { sku: 'A1', nome: 'Acucar', preco: 450, estoque: 2, estoqueMinimo: 5 });
  loja.criarProduto(db, { sku: 'S1', nome: 'Sal', preco: 300, estoque: 20, estoqueMinimo: 5 });
  assert.deepStrictEqual(loja.listarEstoqueBaixo(db).map((p) => p.sku), ['A1']);
  loja.fecharBanco(db);
});

test('atualiza preco e desativa produto', () => {
  const db = bancoNovo();
  const p = loja.criarProduto(db, { sku: 'A1', nome: 'Acucar', preco: 450 });
  assert.strictEqual(loja.atualizarProduto(db, p.id, { preco: 499 }).preco, 499);
  loja.removerProduto(db, p.id);
  assert.strictEqual(loja.listarProdutos(db).length, 0);
  assert.strictEqual(loja.listarProdutos(db, { incluirInativos: true }).length, 1);
  loja.fecharBanco(db);
});
