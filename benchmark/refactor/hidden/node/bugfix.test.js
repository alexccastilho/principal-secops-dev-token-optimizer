'use strict';

// README rule: "Pedidos a partir de R$ 500,00 têm 10% de desconto."
// Checks the boundary: exactly 500,00 gets the discount, 499,99 does not, 500,01 does.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = process.env.PROJECT_ROOT;
if (!ROOT) throw new Error('PROJECT_ROOT not set');
const loja = require(path.join(ROOT, 'index.js'));

const pastas = [];
test.after(() => {
  for (const d of pastas) fs.rmSync(d, { recursive: true, force: true });
});

function pedidoDeUmItem(preco) {
  const pasta = fs.mkdtempSync(path.join(os.tmpdir(), 'loja-bugfix-'));
  pastas.push(pasta);
  const db = loja.abrirBanco(path.join(pasta, 'loja.db'));
  const u = loja.criarUsuario(db, { login: 'vendedora', nome: 'Vendedora', senha: 'balcao', papel: 'vendedor' });
  const c = loja.criarCliente(db, { nome: 'Maria Aparecida', cpf: '529.982.247-25' });
  const p = loja.criarProduto(db, { sku: 'CESTA', nome: 'Cesta basica', preco: preco, estoque: 10 });
  const ped = loja.criarPedido(db, { clienteId: c.id, usuarioId: u.id, itens: [{ produtoId: p.id, quantidade: 1 }] });
  loja.fecharBanco(db);
  return ped;
}

test('order of exactly R$ 500,00 gets 10% off', () => {
  const ped = pedidoDeUmItem(50000);
  assert.strictEqual(ped.subtotal, 50000);
  assert.strictEqual(ped.desconto, 5000);
  assert.strictEqual(ped.total, 45000);
});

test('order of R$ 499,99 gets no discount', () => {
  const ped = pedidoDeUmItem(49999);
  assert.strictEqual(ped.desconto, 0);
  assert.strictEqual(ped.total, 49999);
});

test('order of R$ 500,01 gets 10% off', () => {
  const ped = pedidoDeUmItem(50001);
  assert.strictEqual(ped.desconto, 5000);
  assert.strictEqual(ped.total, 45001);
});
