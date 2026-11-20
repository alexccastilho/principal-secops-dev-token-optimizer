'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loja, bancoNovo } = require('./apoio');

test('cadastra cliente e formata o CPF', () => {
  const db = bancoNovo();
  const c = loja.criarCliente(db, { nome: 'Joao Batista', cpf: '11144477735', email: 'JOAO@Exemplo.com' });
  assert.ok(c.id > 0);
  assert.strictEqual(c.cpf, '111.444.777-35');
  assert.strictEqual(c.email, 'joao@exemplo.com');
  assert.strictEqual(loja.buscarCliente(db, c.id).nome, 'Joao Batista');
  loja.fecharBanco(db);
});

test('nao aceita CPF invalido nem repetido', () => {
  const db = bancoNovo();
  assert.throws(() => loja.criarCliente(db, { nome: 'Fulano', cpf: '111.444.777-00' }));
  loja.criarCliente(db, { nome: 'Fulano', cpf: '111.444.777-35' });
  assert.throws(() => loja.criarCliente(db, { nome: 'Outro', cpf: '11144477735' }));
  loja.fecharBanco(db);
});

test('lista e busca clientes pelo nome', () => {
  const db = bancoNovo();
  loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-25' });
  loja.criarCliente(db, { nome: 'Bruno Souza', cpf: '111.444.777-35' });
  loja.criarCliente(db, { nome: 'Carla Lima', cpf: '123.456.789-09' });
  assert.deepStrictEqual(loja.listarClientes(db).map((c) => c.nome), ['Ana Souza', 'Bruno Souza', 'Carla Lima']);
  assert.deepStrictEqual(loja.buscarClientesPorNome(db, 'souza').map((c) => c.nome), ['Ana Souza', 'Bruno Souza']);
  loja.fecharBanco(db);
});

test('atualiza so os campos informados', () => {
  const db = bancoNovo();
  const c = loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-25', email: 'ana@exemplo.com' });
  const a = loja.atualizarCliente(db, c.id, { telefone: '(11) 3456-7890' });
  assert.strictEqual(a.telefone, '1134567890');
  assert.strictEqual(a.email, 'ana@exemplo.com');
  assert.strictEqual(a.nome, 'Ana Souza');
  loja.fecharBanco(db);
});

test('remove cliente sem pedidos', () => {
  const db = bancoNovo();
  const c = loja.criarCliente(db, { nome: 'Ana Souza', cpf: '529.982.247-25' });
  assert.strictEqual(loja.removerCliente(db, c.id), true);
  assert.strictEqual(loja.buscarCliente(db, c.id), null);
  loja.fecharBanco(db);
});

test('formatarTelefone', () => {
  assert.strictEqual(loja.formatarTelefone('11987654321'), '(11) 98765-4321');
  assert.strictEqual(loja.formatarTelefone('1134567890'), '(11) 3456-7890');
  assert.strictEqual(loja.formatarTelefone('123'), '123');
});
