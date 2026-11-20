'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loja, bancoNovo } = require('./apoio');

test('cria usuario sem devolver a senha', () => {
  const db = bancoNovo();
  const u = loja.criarUsuario(db, { login: 'Paula', nome: 'Paula', senha: 'abacaxi', papel: 'vendedor' });
  assert.strictEqual(u.login, 'paula');
  assert.strictEqual(u.papel, 'vendedor');
  assert.strictEqual(u.senha_hash, undefined);
  assert.throws(() => loja.criarUsuario(db, { login: 'paula', nome: 'Outra', senha: 'abacaxi' }));
  assert.throws(() => loja.criarUsuario(db, { login: 'zeca', nome: 'Zeca', senha: '123' }));
  loja.fecharBanco(db);
});

test('login abre sessao e logout encerra', () => {
  const db = bancoNovo();
  loja.criarUsuario(db, { login: 'paula', nome: 'Paula', senha: 'abacaxi', papel: 'admin' });
  const r = loja.login(db, 'paula', 'abacaxi');
  assert.ok(r);
  assert.strictEqual(typeof r.token, 'string');
  assert.strictEqual(r.usuario.login, 'paula');
  assert.strictEqual(loja.validarSessao(db, r.token).login, 'paula');
  assert.strictEqual(loja.encerrarSessao(db, r.token), true);
  assert.strictEqual(loja.validarSessao(db, r.token), null);
  loja.fecharBanco(db);
});

test('senha errada nao faz login', () => {
  const db = bancoNovo();
  loja.criarUsuario(db, { login: 'paula', nome: 'Paula', senha: 'abacaxi' });
  assert.strictEqual(loja.login(db, 'paula', 'errada'), null);
  assert.strictEqual(loja.login(db, 'ninguem', 'abacaxi'), null);
  loja.fecharBanco(db);
});

test('troca de senha', () => {
  const db = bancoNovo();
  const u = loja.criarUsuario(db, { login: 'paula', nome: 'Paula', senha: 'abacaxi' });
  assert.strictEqual(loja.alterarSenha(db, u.id, 'abacaxi', 'melancia'), true);
  assert.strictEqual(loja.login(db, 'paula', 'abacaxi'), null);
  assert.ok(loja.login(db, 'paula', 'melancia'));
  loja.fecharBanco(db);
});
