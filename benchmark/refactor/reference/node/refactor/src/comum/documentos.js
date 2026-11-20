'use strict';

// Formatacao de documentos brasileiros: CPF, CNPJ e CEP.
// A validacao fica em validacao.js.

/**
 * Remove tudo que nao for digito.
 */
function limparNumeros(valor) {
  if (valor === null || valor === undefined) return '';
  return String(valor).replace(/\D/g, '');
}

/**
 * 12345678909 -> 123.456.789-09
 */
function formatarCPF(cpf) {
  const n = limparNumeros(cpf);
  if (n.length !== 11) return String(cpf || '');
  return n.slice(0, 3) + '.' + n.slice(3, 6) + '.' + n.slice(6, 9) + '-' + n.slice(9);
}

/**
 * 11222333000181 -> 11.222.333/0001-81
 */
function formatarCNPJ(cnpj) {
  const n = limparNumeros(cnpj);
  if (n.length !== 14) return String(cnpj || '');
  return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8, 12) + '-' + n.slice(12);
}

/**
 * 01310100 -> 01310-100
 */
function formatarCEP(cep) {
  const n = limparNumeros(cep);
  if (n.length !== 8) {
    throw new Error('CEP invalido: ' + cep);
  }
  return n.slice(0, 5) + '-' + n.slice(5);
}

/**
 * Esconde o meio do CPF para relatorios impressos: ***.456.789-**
 */
function mascararCPF(cpf) {
  const f = formatarCPF(cpf);
  if (f.length !== 14) return f;
  return '***' + f.slice(3, 11) + '-**';
}

// Faixas de CEP por estado (Correios). Usado so para conferir o endereco digitado.
const FAIXAS_CEP = [
  ['SP', 1000000, 19999999],
  ['RJ', 20000000, 28999999],
  ['ES', 29000000, 29999999],
  ['MG', 30000000, 39999999],
  ['BA', 40000000, 48999999],
  ['SE', 49000000, 49999999],
  ['PE', 50000000, 56999999],
  ['AL', 57000000, 57999999],
  ['PB', 58000000, 58999999],
  ['RN', 59000000, 59999999],
  ['CE', 60000000, 63999999],
  ['PI', 64000000, 64999999],
  ['MA', 65000000, 65999999],
  ['PA', 66000000, 68899999],
  ['AP', 68900000, 68999999],
  ['AM', 69000000, 69299999],
  ['RR', 69300000, 69399999],
  ['AM', 69400000, 69899999],
  ['AC', 69900000, 69999999],
  ['DF', 70000000, 73699999],
  ['GO', 73700000, 76799999],
  ['RO', 76800000, 76999999],
  ['TO', 77000000, 77999999],
  ['MT', 78000000, 78899999],
  ['MS', 79000000, 79999999],
  ['PR', 80000000, 87999999],
  ['SC', 88000000, 89999999],
  ['RS', 90000000, 99999999],
];

/**
 * Estado (UF) pela faixa do CEP, ou null se nao achar.
 */
function ufPorCEP(cep) {
  const n = limparNumeros(cep);
  if (n.length !== 8) return null;
  const v = parseInt(n, 10);
  for (const [uf, ini, fim] of FAIXAS_CEP) {
    if (v >= ini && v <= fim) return uf;
  }
  return null;
}

module.exports = {
  ufPorCEP,
  limparNumeros,
  formatarCPF,
  formatarCNPJ,
  formatarCEP,
  mascararCPF,
};
