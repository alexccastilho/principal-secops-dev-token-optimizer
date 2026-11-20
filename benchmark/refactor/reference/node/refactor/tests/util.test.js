'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { loja } = require('./apoio');

test('formatarMoeda formata centavos no padrao brasileiro', () => {
  assert.strictEqual(loja.formatarMoeda(1250), 'R$ 12,50');
  assert.strictEqual(loja.formatarMoeda(5), 'R$ 0,05');
  assert.strictEqual(loja.formatarMoeda(123456789), 'R$ 1.234.567,89');
  assert.strictEqual(loja.formatarMoeda(-990), '-R$ 9,90');
});

test('converterMoeda entende o que o usuario digita', () => {
  assert.strictEqual(loja.converterMoeda('12,50'), 1250);
  assert.strictEqual(loja.converterMoeda('R$ 1.234,56'), 123456);
  assert.strictEqual(loja.converterMoeda('10'), 1000);
  assert.strictEqual(loja.converterMoeda(7.5), 750);
  assert.throws(() => loja.converterMoeda('abc'));
});

test('datas no formato brasileiro', () => {
  assert.strictEqual(loja.formatarData('2024-03-09'), '09/03/2024');
  assert.strictEqual(loja.formatarData('2024-03-09 14:20:00'), '09/03/2024');
  assert.strictEqual(loja.converterDataBR('9/3/2024'), '2024-03-09');
  assert.strictEqual(loja.converterDataBR('29/02/2024'), '2024-02-29');
  assert.throws(() => loja.converterDataBR('29/02/2023'));
});

test('validarCPF confere os digitos', () => {
  assert.strictEqual(loja.validarCPF('529.982.247-25'), true);
  assert.strictEqual(loja.validarCPF('52998224725'), true);
  assert.strictEqual(loja.validarCPF('529.982.247-26'), false);
  assert.strictEqual(loja.validarCPF('123'), false);
});

test('validarCNPJ e formatacao de documentos', () => {
  assert.strictEqual(loja.validarCNPJ('11.222.333/0001-81'), true);
  assert.strictEqual(loja.validarCNPJ('11.222.333/0001-82'), false);
  assert.strictEqual(loja.formatarCNPJ('11222333000181'), '11.222.333/0001-81');
  assert.strictEqual(loja.formatarCPF('12345678909'), '123.456.789-09');
});

test('formatarCEP', () => {
  assert.strictEqual(loja.formatarCEP('01310100'), '01310-100');
  assert.strictEqual(loja.formatarCEP('01310-100'), '01310-100');
  assert.throws(() => loja.formatarCEP('123'));
});

test('validarEmail', () => {
  assert.strictEqual(loja.validarEmail('joao@loja.com.br'), true);
  assert.strictEqual(loja.validarEmail('joao@loja'), false);
  assert.strictEqual(loja.validarEmail(''), false);
});
