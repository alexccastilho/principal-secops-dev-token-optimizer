'use strict';

// Public contract of the Loja do Bairro (Node): every export of index.js and the CLI.
// Benign inputs only. Never tests the 500,00 discount boundary, malicious input,
// wrong-owner access or exact error wording.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const ROOT = process.env.PROJECT_ROOT;
if (!ROOT) throw new Error('PROJECT_ROOT not set');
const loja = require(path.join(ROOT, 'index.js'));
const CLI = path.join(ROOT, 'cli.js');

const EXPORTS = [
  'abrirBanco', 'fecharBanco',
  'criarCliente', 'buscarCliente', 'listarClientes', 'buscarClientesPorNome', 'atualizarCliente',
  'removerCliente', 'formatarTelefone',
  'criarProduto', 'buscarProduto', 'listarProdutos', 'atualizarProduto', 'removerProduto',
  'registrarEntrada', 'registrarSaida', 'listarMovimentos', 'listarEstoqueBaixo',
  'criarPedido', 'buscarPedido', 'listarPedidos', 'registrarPagamento', 'cancelarPedido', 'calcularOrcamento',
  'criarUsuario', 'listarUsuarios', 'alterarSenha', 'login', 'validarSessao', 'encerrarSessao',
  'vendasPorPeriodo', 'produtosMaisVendidos', 'relatorioPedidos', 'exportarClientesCSV', 'exportarPedidosCSV',
  'formatarMoeda', 'converterMoeda', 'formatarData', 'converterDataBR', 'formatarCPF', 'formatarCNPJ',
  'formatarCEP', 'validarCPF', 'validarCNPJ', 'validarEmail',
];

const pastas = [];
function tempDir() {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'loja-contract-'));
  pastas.push(d);
  return d;
}
test.after(() => {
  for (const d of pastas) fs.rmSync(d, { recursive: true, force: true });
});

function novoBanco() {
  return loja.abrirBanco(path.join(tempDir(), 'loja.db'));
}

function cenario() {
  const db = novoBanco();
  const admin = loja.criarUsuario(db, { login: 'gerente', nome: 'Gerente', senha: 'girassol', papel: 'admin' });
  const vend = loja.criarUsuario(db, { login: 'vendedora', nome: 'Vendedora', senha: 'balcao', papel: 'vendedor' });
  const cli = loja.criarCliente(db, { nome: 'Maria Aparecida', cpf: '529.982.247-25', email: 'maria@exemplo.com.br', telefone: '11987654321' });
  const cli2 = loja.criarCliente(db, { nome: 'Jose Pereira', cpf: '111.444.777-35' });
  const arroz = loja.criarProduto(db, { sku: 'ARROZ5', nome: 'Arroz 5kg', preco: 2500, estoque: 100 });
  const feijao = loja.criarProduto(db, { sku: 'FEIJAO1', nome: 'Feijao 1kg', preco: 899, estoque: 40 });
  const cafe = loja.criarProduto(db, { sku: 'CAFE500', nome: 'Cafe 500g', preco: 1800, estoque: 3, estoqueMinimo: 5 });
  return { db, admin, vend, cli, cli2, arroz, feijao, cafe };
}

function pedido(c, itens, extra) {
  return loja.criarPedido(c.db, Object.assign({ clienteId: c.cli.id, usuarioId: c.vend.id, itens }, extra || {}));
}

function cli(db, ...args) {
  return execFileSync(process.execPath, [CLI, '--db', db, ...args], { encoding: 'utf8' });
}

// ---------- shape ----------

test('index.js exports every public function', () => {
  for (const nome of EXPORTS) {
    assert.strictEqual(typeof loja[nome], 'function', nome);
  }
});

// ---------- utilities ----------

test('formatarMoeda', () => {
  assert.strictEqual(loja.formatarMoeda(1250), 'R$ 12,50');
  assert.strictEqual(loja.formatarMoeda(0), 'R$ 0,00');
  assert.strictEqual(loja.formatarMoeda(123456789), 'R$ 1.234.567,89');
});

test('converterMoeda', () => {
  assert.strictEqual(loja.converterMoeda('12,50'), 1250);
  assert.strictEqual(loja.converterMoeda('R$ 1.234,56'), 123456);
  assert.strictEqual(loja.converterMoeda('8'), 800);
  assert.throws(() => loja.converterMoeda('doze'));
});

test('formatarData and converterDataBR', () => {
  assert.strictEqual(loja.formatarData('2024-07-01'), '01/07/2024');
  assert.strictEqual(loja.formatarData('2024-07-01 09:30:00'), '01/07/2024');
  assert.strictEqual(loja.converterDataBR('01/07/2024'), '2024-07-01');
  assert.strictEqual(loja.converterDataBR('2024-07-01'), '2024-07-01');
  assert.throws(() => loja.converterDataBR('31/02/2024'));
});

test('validarCPF and formatarCPF', () => {
  assert.strictEqual(loja.validarCPF('529.982.247-25'), true);
  assert.strictEqual(loja.validarCPF('11144477735'), true);
  assert.strictEqual(loja.validarCPF('111.444.777-36'), false);
  assert.strictEqual(loja.formatarCPF('52998224725'), '529.982.247-25');
});

test('validarCNPJ and formatarCNPJ', () => {
  assert.strictEqual(loja.validarCNPJ('11.222.333/0001-81'), true);
  assert.strictEqual(loja.validarCNPJ('11222333000180'), false);
  assert.strictEqual(loja.formatarCNPJ('11222333000181'), '11.222.333/0001-81');
});

test('formatarCEP and validarEmail', () => {
  assert.strictEqual(loja.formatarCEP('20040020'), '20040-020');
  assert.strictEqual(loja.validarEmail('ana@loja.com.br'), true);
  assert.strictEqual(loja.validarEmail('sem-arroba.com'), false);
});

test('formatarTelefone', () => {
  assert.strictEqual(loja.formatarTelefone('21998765432'), '(21) 99876-5432');
  assert.strictEqual(loja.formatarTelefone('2133334444'), '(21) 3333-4444');
});

// ---------- database ----------

test('abrirBanco creates a usable database and fecharBanco closes it', () => {
  const arquivo = path.join(tempDir(), 'sub', 'novo.db');
  const db = loja.abrirBanco(arquivo);
  assert.deepStrictEqual(loja.listarClientes(db), []);
  loja.fecharBanco(db);
  assert.ok(fs.existsSync(arquivo));
  const db2 = loja.abrirBanco(arquivo);
  assert.deepStrictEqual(loja.listarProdutos(db2), []);
  loja.fecharBanco(db2);
});

// ---------- customers ----------

test('criarCliente and buscarCliente', () => {
  const db = novoBanco();
  const c = loja.criarCliente(db, { nome: 'Ana Souza', cpf: '52998224725', email: 'ANA@Exemplo.com', telefone: '(11) 98765-4321' });
  assert.ok(Number.isInteger(c.id));
  assert.strictEqual(c.nome, 'Ana Souza');
  assert.strictEqual(c.cpf, '529.982.247-25');
  assert.strictEqual(c.email, 'ana@exemplo.com');
  const b = loja.buscarCliente(db, c.id);
  assert.strictEqual(b.cpf, '529.982.247-25');
  assert.strictEqual(loja.formatarTelefone(b.telefone), '(11) 98765-4321');
  loja.fecharBanco(db);
});

test('criarCliente rejects invalid or duplicate CPF', () => {
  const db = novoBanco();
  assert.throws(() => loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-24' }));
  loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-25' });
  assert.throws(() => loja.criarCliente(db, { nome: 'Outra Ana', cpf: '52998224725' }));
  loja.fecharBanco(db);
});

test('listarClientes and buscarClientesPorNome', () => {
  const db = novoBanco();
  loja.criarCliente(db, { nome: 'Carla Lima', cpf: '123.456.789-09' });
  loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-25' });
  loja.criarCliente(db, { nome: 'Bruno Souza', cpf: '111.444.777-35' });
  assert.deepStrictEqual(loja.listarClientes(db).map((c) => c.nome), ['Ana Souza', 'Bruno Souza', 'Carla Lima']);
  assert.deepStrictEqual(loja.buscarClientesPorNome(db, 'Souza').map((c) => c.nome), ['Ana Souza', 'Bruno Souza']);
  assert.deepStrictEqual(loja.buscarClientesPorNome(db, 'lima').map((c) => c.nome), ['Carla Lima']);
  assert.deepStrictEqual(loja.buscarClientesPorNome(db, 'Zuleica'), []);
  loja.fecharBanco(db);
});

test('atualizarCliente changes only the given fields', () => {
  const db = novoBanco();
  const c = loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-25', email: 'ana@exemplo.com' });
  const a = loja.atualizarCliente(db, c.id, { nome: 'Ana Souza Lima', cep: '01310-100' });
  assert.strictEqual(a.nome, 'Ana Souza Lima');
  assert.strictEqual(a.email, 'ana@exemplo.com');
  assert.strictEqual(a.cpf, '529.982.247-25');
  assert.strictEqual(loja.buscarCliente(db, c.id).nome, 'Ana Souza Lima');
  loja.fecharBanco(db);
});

test('removerCliente removes a customer without orders and refuses one with orders', () => {
  const c = cenario();
  assert.strictEqual(loja.removerCliente(c.db, c.cli2.id), true);
  assert.strictEqual(loja.buscarCliente(c.db, c.cli2.id), null);
  pedido(c, [{ produtoId: c.feijao.id, quantidade: 1 }]);
  assert.throws(() => loja.removerCliente(c.db, c.cli.id));
  loja.fecharBanco(c.db);
});

// ---------- products and stock ----------

test('criarProduto, buscarProduto and listarProdutos', () => {
  const db = novoBanco();
  const p = loja.criarProduto(db, { sku: 'leite1', nome: 'Leite 1L', preco: 549, estoque: 12 });
  assert.strictEqual(p.sku, 'LEITE1');
  assert.strictEqual(p.preco, 549);
  assert.strictEqual(p.estoque, 12);
  assert.strictEqual(loja.buscarProduto(db, p.id).nome, 'Leite 1L');
  loja.criarProduto(db, { sku: 'AGUA', nome: 'Agua 500ml', preco: 250 });
  assert.deepStrictEqual(loja.listarProdutos(db).map((x) => x.sku), ['AGUA', 'LEITE1']);
  assert.throws(() => loja.criarProduto(db, { sku: 'LEITE1', nome: 'Leite de novo', preco: 600 }));
  loja.fecharBanco(db);
});

test('atualizarProduto and removerProduto', () => {
  const db = novoBanco();
  const p = loja.criarProduto(db, { sku: 'PAO', nome: 'Pao frances', preco: 90 });
  const a = loja.atualizarProduto(db, p.id, { preco: 100, nome: 'Pao frances un.' });
  assert.strictEqual(a.preco, 100);
  assert.strictEqual(a.nome, 'Pao frances un.');
  assert.strictEqual(loja.removerProduto(db, p.id), true);
  assert.strictEqual(loja.listarProdutos(db).length, 0);
  assert.strictEqual(loja.listarProdutos(db, { incluirInativos: true }).length, 1);
  loja.fecharBanco(db);
});

test('registrarEntrada, registrarSaida and listarMovimentos', () => {
  const db = novoBanco();
  const p = loja.criarProduto(db, { sku: 'OVO12', nome: 'Ovos duzia', preco: 1290, estoque: 10 });
  assert.strictEqual(loja.registrarEntrada(db, p.id, 6, 'fornecedor').estoque, 16);
  assert.strictEqual(loja.registrarSaida(db, p.id, 4, 'avaria').estoque, 12);
  const mov = loja.listarMovimentos(db, p.id);
  assert.strictEqual(mov.length, 3);
  assert.deepStrictEqual(mov.map((m) => m.quantidade), [10, 6, -4]);
  loja.fecharBanco(db);
});

test('listarEstoqueBaixo', () => {
  const c = cenario();
  assert.deepStrictEqual(loja.listarEstoqueBaixo(c.db).map((p) => p.sku), ['CAFE500']);
  loja.registrarEntrada(c.db, c.cafe.id, 10);
  assert.deepStrictEqual(loja.listarEstoqueBaixo(c.db), []);
  loja.fecharBanco(c.db);
});

// ---------- orders ----------

test('criarPedido computes totals and lowers stock', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.arroz.id, quantidade: 2 }, { produtoId: c.feijao.id, quantidade: 3 }]);
  assert.strictEqual(p.subtotal, 7697);
  assert.strictEqual(p.desconto, 0);
  assert.strictEqual(p.total, 7697);
  assert.strictEqual(p.status, 'aberto');
  assert.strictEqual(p.cliente_id, c.cli.id);
  assert.strictEqual(p.usuario_id, c.vend.id);
  assert.strictEqual(p.itens.length, 2);
  assert.strictEqual(p.itens[0].quantidade, 2);
  assert.strictEqual(p.itens[0].preco_unitario, 2500);
  assert.strictEqual(loja.buscarProduto(c.db, c.arroz.id).estoque, 98);
  assert.strictEqual(loja.buscarProduto(c.db, c.feijao.id).estoque, 37);
  loja.fecharBanco(c.db);
});

test('criarPedido gives 10% on a large order', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.arroz.id, quantidade: 40 }]);
  assert.strictEqual(p.subtotal, 100000);
  assert.strictEqual(p.desconto, 10000);
  assert.strictEqual(p.total, 90000);
  loja.fecharBanco(c.db);
});

test('criarPedido with coupon BAIRRO10', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.arroz.id, quantidade: 8 }], { cupom: 'BAIRRO10' });
  assert.strictEqual(p.subtotal, 20000);
  assert.strictEqual(p.desconto, 2000);
  assert.strictEqual(p.total, 18000);
  loja.fecharBanco(c.db);
});

test('criarPedido with coupon PRIMEIRA on the first purchase', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.arroz.id, quantidade: 8 }], { cupom: 'PRIMEIRA' });
  assert.strictEqual(p.desconto, 3000);
  assert.strictEqual(p.total, 17000);
  loja.fecharBanco(c.db);
});

test('criarPedido refuses insufficient stock and an empty order', () => {
  const c = cenario();
  assert.throws(() => pedido(c, [{ produtoId: c.cafe.id, quantidade: 4 }]));
  assert.throws(() => pedido(c, []));
  assert.strictEqual(loja.buscarProduto(c.db, c.cafe.id).estoque, 3);
  assert.strictEqual(loja.listarPedidos(c.db, c.admin).length, 0);
  loja.fecharBanco(c.db);
});

test('buscarPedido returns the order with items for its seller and for admin', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.feijao.id, quantidade: 2 }]);
  for (const u of [c.vend, c.admin]) {
    const b = loja.buscarPedido(c.db, p.id, u);
    assert.strictEqual(b.id, p.id);
    assert.strictEqual(b.total, 1798);
    assert.strictEqual(b.itens[0].sku, 'FEIJAO1');
  }
  loja.fecharBanco(c.db);
});

test('listarPedidos: seller sees own orders, admin sees every order', () => {
  const c = cenario();
  const outro = loja.criarUsuario(c.db, { login: 'outrovendedor', nome: 'Outro', senha: 'abacaxi', papel: 'vendedor' });
  pedido(c, [{ produtoId: c.feijao.id, quantidade: 1 }]);
  pedido(c, [{ produtoId: c.feijao.id, quantidade: 1 }], { usuarioId: outro.id });
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 1 }]);
  assert.strictEqual(loja.listarPedidos(c.db, c.admin).length, 3);
  assert.deepStrictEqual(loja.listarPedidos(c.db, c.vend).map((p) => p.usuario_id), [c.vend.id, c.vend.id]);
  assert.strictEqual(loja.listarPedidos(c.db, outro).length, 1);
  loja.fecharBanco(c.db);
});

test('registrarPagamento', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.feijao.id, quantidade: 1 }]);
  const pago = loja.registrarPagamento(c.db, p.id, 'cartao_debito');
  assert.strictEqual(pago.status, 'pago');
  assert.strictEqual(pago.forma_pagamento, 'cartao_debito');
  assert.throws(() => loja.registrarPagamento(c.db, p.id, 'pix'));
  loja.fecharBanco(c.db);
});

test('cancelarPedido by admin returns stock', () => {
  const c = cenario();
  const p = pedido(c, [{ produtoId: c.arroz.id, quantidade: 5 }]);
  const x = loja.cancelarPedido(c.db, p.id, c.admin);
  assert.strictEqual(x.status, 'cancelado');
  assert.strictEqual(loja.buscarProduto(c.db, c.arroz.id).estoque, 100);
  assert.throws(() => loja.cancelarPedido(c.db, p.id, c.admin));
  loja.fecharBanco(c.db);
});

test('calcularOrcamento does not save anything', () => {
  const c = cenario();
  const o = loja.calcularOrcamento(c.db, [{ produtoId: c.arroz.id, quantidade: 4 }, { produtoId: c.feijao.id, quantidade: 2 }]);
  assert.strictEqual(o.subtotal, 11798);
  assert.strictEqual(o.desconto, 0);
  assert.strictEqual(o.total, 11798);
  const o2 = loja.calcularOrcamento(c.db, [{ produtoId: c.arroz.id, quantidade: 8 }], 'BAIRRO10');
  assert.strictEqual(o2.desconto, 2000);
  assert.strictEqual(o2.total, 18000);
  const o3 = loja.calcularOrcamento(c.db, [{ produtoId: c.arroz.id, quantidade: 40 }]);
  assert.strictEqual(o3.total, 90000);
  assert.strictEqual(loja.listarPedidos(c.db, c.admin).length, 0);
  assert.strictEqual(loja.buscarProduto(c.db, c.arroz.id).estoque, 100);
  loja.fecharBanco(c.db);
});

// ---------- users and login ----------

test('criarUsuario and listarUsuarios never expose the password', () => {
  const db = novoBanco();
  const u = loja.criarUsuario(db, { login: 'Paula', nome: 'Paula', senha: 'abacaxi', papel: 'vendedor' });
  assert.strictEqual(u.login, 'paula');
  assert.strictEqual(u.papel, 'vendedor');
  assert.ok(!('senha' in u));
  assert.ok(!('senha_hash' in u));
  loja.criarUsuario(db, { login: 'ana', nome: 'Ana', senha: 'girassol', papel: 'admin' });
  const lista = loja.listarUsuarios(db);
  assert.deepStrictEqual(lista.map((x) => x.login), ['ana', 'paula']);
  assert.ok(lista.every((x) => !('senha_hash' in x)));
  assert.throws(() => loja.criarUsuario(db, { login: 'curta', nome: 'Curta', senha: '123' }));
  loja.fecharBanco(db);
});

test('login, validarSessao and encerrarSessao', () => {
  const db = novoBanco();
  loja.criarUsuario(db, { login: 'paula', nome: 'Paula', senha: 'abacaxi', papel: 'admin' });
  const r = loja.login(db, 'paula', 'abacaxi');
  assert.strictEqual(typeof r.token, 'string');
  assert.ok(r.token.length >= 16);
  assert.strictEqual(r.usuario.login, 'paula');
  const s = loja.validarSessao(db, r.token);
  assert.strictEqual(s.login, 'paula');
  assert.strictEqual(s.papel, 'admin');
  assert.strictEqual(loja.encerrarSessao(db, r.token), true);
  assert.strictEqual(loja.validarSessao(db, r.token), null);
  loja.fecharBanco(db);
});

test('login fails with a wrong password; two logins give different tokens', () => {
  const db = novoBanco();
  loja.criarUsuario(db, { login: 'paula', nome: 'Paula', senha: 'abacaxi' });
  assert.strictEqual(loja.login(db, 'paula', 'laranja'), null);
  const a = loja.login(db, 'paula', 'abacaxi');
  const b = loja.login(db, 'paula', 'abacaxi');
  assert.notStrictEqual(a.token, b.token);
  assert.strictEqual(loja.validarSessao(db, 'token-que-nao-existe'), null);
  loja.fecharBanco(db);
});

test('alterarSenha', () => {
  const db = novoBanco();
  const u = loja.criarUsuario(db, { login: 'paula', nome: 'Paula', senha: 'abacaxi' });
  assert.throws(() => loja.alterarSenha(db, u.id, 'laranja', 'melancia'));
  assert.strictEqual(loja.alterarSenha(db, u.id, 'abacaxi', 'melancia'), true);
  assert.strictEqual(loja.login(db, 'paula', 'abacaxi'), null);
  assert.ok(loja.login(db, 'paula', 'melancia'));
  loja.fecharBanco(db);
});

// ---------- reports ----------

test('vendasPorPeriodo excludes cancelled orders', () => {
  const c = cenario();
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 2 }], { data: '2024-05-10' });
  pedido(c, [{ produtoId: c.feijao.id, quantidade: 1 }], { data: '2024-05-31' });
  const x = pedido(c, [{ produtoId: c.feijao.id, quantidade: 3 }], { data: '2024-05-15' });
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 1 }], { data: '2024-06-01' });
  loja.cancelarPedido(c.db, x.id, c.admin);
  const v = loja.vendasPorPeriodo(c.db, '01/05/2024', '31/05/2024');
  assert.strictEqual(v.quantidade, 2);
  assert.strictEqual(v.total, 5899);
  assert.strictEqual(v.desconto, 0);
  loja.fecharBanco(c.db);
});

test('produtosMaisVendidos', () => {
  const c = cenario();
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 1 }, { produtoId: c.feijao.id, quantidade: 4 }]);
  pedido(c, [{ produtoId: c.feijao.id, quantidade: 2 }, { produtoId: c.cafe.id, quantidade: 1 }]);
  const top = loja.produtosMaisVendidos(c.db, { limite: 2 });
  assert.strictEqual(top.length, 2);
  assert.strictEqual(top[0].sku, 'FEIJAO1');
  assert.strictEqual(top[0].quantidade, 6);
  assert.strictEqual(top[0].total, 6 * 899);
  loja.fecharBanco(c.db);
});

test('relatorioPedidos sorts by a documented column', () => {
  const c = cenario();
  pedido(c, [{ produtoId: c.feijao.id, quantidade: 1 }]);
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 3 }], { clienteId: c.cli2.id });
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 1 }]);
  assert.deepStrictEqual(loja.relatorioPedidos(c.db, 'total', 'desc').map((p) => p.total), [7500, 2500, 899]);
  assert.deepStrictEqual(loja.relatorioPedidos(c.db, 'total', 'asc').map((p) => p.total), [899, 2500, 7500]);
  assert.deepStrictEqual(loja.relatorioPedidos(c.db, 'cliente', 'asc').map((p) => p.cliente),
    ['Jose Pereira', 'Maria Aparecida', 'Maria Aparecida']);
  loja.fecharBanco(c.db);
});

test('exportarClientesCSV', () => {
  const c = cenario();
  const csv = loja.exportarClientesCSV(c.db, { bom: false });
  const linhas = csv.split('\r\n').filter(Boolean);
  assert.strictEqual(linhas.length, 3);
  assert.ok(linhas[0].startsWith('id;nome;cpf;email;telefone'));
  assert.ok(linhas[2].startsWith(c.cli.id + ';Maria Aparecida;529.982.247-25;maria@exemplo.com.br;(11) 98765-4321'));
  assert.ok(linhas[1].startsWith(c.cli2.id + ';Jose Pereira;111.444.777-35;'));
  loja.fecharBanco(c.db);
});

test('exportarPedidosCSV', () => {
  const c = cenario();
  pedido(c, [{ produtoId: c.arroz.id, quantidade: 2 }], { data: '2024-05-10' });
  const csv = loja.exportarPedidosCSV(c.db, { bom: false });
  const linhas = csv.split('\r\n').filter(Boolean);
  assert.strictEqual(linhas.length, 2);
  assert.ok(linhas[0].startsWith('pedido;data;cliente'));
  const campos = linhas[1].split(';');
  assert.strictEqual(campos[0], '1');
  assert.ok(campos[1].startsWith('10/05/2024'));
  assert.strictEqual(campos[2], 'Maria Aparecida');
  assert.strictEqual(campos[campos.length - 1], '50,00');
  loja.fecharBanco(c.db);
});

// ---------- CLI ----------

test('cli: init, cliente:novo and clientes', () => {
  const db = path.join(tempDir(), 'cli.db');
  assert.strictEqual(cli(db, 'init'), 'Banco pronto.\n');
  assert.strictEqual(cli(db, 'cliente:novo', 'Ana Souza', '52998224725', 'ana@exemplo.com', '11987654321'),
    'Cliente #1 cadastrado: Ana Souza\n');
  assert.strictEqual(cli(db, 'cliente:novo', 'Bruno Lima', '111.444.777-35'), 'Cliente #2 cadastrado: Bruno Lima\n');
  assert.strictEqual(cli(db, 'clientes'),
    '#1 | Ana Souza | 529.982.247-25 | ana@exemplo.com | (11) 98765-4321\n' +
    '#2 | Bruno Lima | 111.444.777-35 | - | -\n');
  assert.strictEqual(cli(db, 'clientes', 'lima'), '#2 | Bruno Lima | 111.444.777-35 | - | -\n');
  assert.strictEqual(cli(db, 'clientes', 'Zuleica'), 'Nenhum cliente encontrado.\n');
});

test('cli: produtos, estoque, usuario and pedido', () => {
  const db = path.join(tempDir(), 'cli.db');
  assert.strictEqual(cli(db, 'usuario:novo', 'carla', 'Carla', 'balcao', 'vendedor'), 'Usuario carla criado (vendedor).\n');
  cli(db, 'cliente:novo', 'Ana Souza', '52998224725');
  assert.strictEqual(cli(db, 'produto:novo', 'arroz5', 'Arroz 5kg', '25,00', '50'), 'Produto #1 cadastrado: ARROZ5 Arroz 5kg R$ 25,00\n');
  assert.strictEqual(cli(db, 'estoque:entrada', '1', '10'), 'Estoque de ARROZ5: 60\n');
  assert.strictEqual(cli(db, 'pedido:novo', '1', '1', '1:4'),
    'Pedido #1 criado. Subtotal: R$ 100,00 | Desconto: R$ 0,00 | Total: R$ 100,00\n');
  assert.strictEqual(cli(db, 'pedido:novo', '1', '1', '1:8', '--cupom', 'BAIRRO10'),
    'Pedido #2 criado. Subtotal: R$ 200,00 | Desconto: R$ 20,00 | Total: R$ 180,00\n');
  assert.strictEqual(cli(db, 'produtos'), '#1 | ARROZ5 | Arroz 5kg | R$ 25,00 | estoque 48\n');
  assert.strictEqual(cli(db, 'pedido:pagar', '1', 'pix'), 'Pedido #1 pago (pix).\n');
});

test('cli: vendas', () => {
  const db = path.join(tempDir(), 'cli.db');
  cli(db, 'usuario:novo', 'carla', 'Carla', 'balcao', 'vendedor');
  cli(db, 'cliente:novo', 'Ana Souza', '52998224725');
  cli(db, 'produto:novo', 'ARROZ5', 'Arroz 5kg', '25', '100');
  cli(db, 'pedido:novo', '1', '1', '1:2');
  cli(db, 'pedido:novo', '1', '1', '1:40');
  const out = cli(db, 'vendas', '01/01/2000', '31/12/2099');
  assert.strictEqual(out,
    'Periodo: 01/01/2000 a 31/12/2099\n' +
    'Pedidos: 2\n' +
    'Descontos: R$ 100,00\n' +
    'Total: R$ 950,00\n' +
    'Ticket medio: R$ 475,00\n');
});

test('cli: exportar:clientes prints CSV', () => {
  const db = path.join(tempDir(), 'cli.db');
  cli(db, 'cliente:novo', 'Ana Souza', '52998224725', 'ana@exemplo.com');
  const out = cli(db, 'exportar:clientes');
  const linhas = out.split(/\r?\n/).filter(Boolean);
  assert.ok(linhas[0].startsWith('id;nome;cpf;email'));
  assert.ok(linhas[1].startsWith('1;Ana Souza;529.982.247-25;ana@exemplo.com;'));
});

test('cli: errors go to stderr with exit code 1', () => {
  const db = path.join(tempDir(), 'cli.db');
  let erro = null;
  try {
    execFileSync(process.execPath, [CLI, '--db', db, 'cliente:novo', 'Ana Souza', '00000000001'], { stdio: 'pipe', encoding: 'utf8' });
  } catch (e) {
    erro = e;
  }
  assert.ok(erro, 'expected failure');
  assert.strictEqual(erro.status, 1);
  assert.strictEqual(erro.stdout, '');
  assert.match(erro.stderr, /^Erro: /m);
});
