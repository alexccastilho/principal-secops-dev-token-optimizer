'use strict';

// Unica fonte de validacao de dados de cadastro: CPF, CNPJ, e-mail, telefone, CEP,
// login e senha. Clientes, pedidos e usuarios usam estas funcoes.

const { limparNumeros } = require('./documentos');

function digitoCPF(n, tamanho) {
  let soma = 0;
  for (let i = 0; i < tamanho; i++) {
    soma += parseInt(n[i], 10) * (tamanho + 1 - i);
  }
  const d = (soma * 10) % 11;
  return d === 10 ? 0 : d;
}

/**
 * CPF valido pelos digitos verificadores. Aceita com ou sem pontuacao.
 * Sequencias repetidas (111.111.111-11) sao recusadas.
 */
function validarCPF(cpf) {
  const n = limparNumeros(cpf);
  if (n.length !== 11 || /^(\d)\1{10}$/.test(n)) return false;
  return digitoCPF(n, 9) === parseInt(n[9], 10) && digitoCPF(n, 10) === parseInt(n[10], 10);
}

function digitoCNPJ(base) {
  const pesos = base.length === 12
    ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  let soma = 0;
  for (let i = 0; i < base.length; i++) {
    soma += parseInt(base[i], 10) * pesos[i];
  }
  const resto = soma % 11;
  return resto < 2 ? 0 : 11 - resto;
}

/**
 * CNPJ valido pelos digitos verificadores.
 */
function validarCNPJ(cnpj) {
  const n = limparNumeros(cnpj);
  if (n.length !== 14 || /^(\d)\1{13}$/.test(n)) return false;
  return digitoCNPJ(n.slice(0, 12)) === parseInt(n[12], 10) &&
    digitoCNPJ(n.slice(0, 13)) === parseInt(n[13], 10);
}

/**
 * E-mail no formato algo@dominio.ext
 */
function validarEmail(email) {
  if (!email) return false;
  const txt = String(email).trim();
  if (txt.length > 254) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(txt);
}

function telefoneValido(telefone) {
  const t = limparNumeros(telefone);
  return t.length >= 10 && t.length <= 13;
}

function cepValido(cep) {
  return limparNumeros(cep).length === 8;
}

// As funcoes "exigir" lancam erro com a mensagem pronta para o usuario.

function exigir(condicao, mensagem) {
  if (!condicao) {
    throw new Error(mensagem);
  }
}

function exigirInteiroPositivo(valor, mensagem) {
  exigir(Number.isInteger(valor) && valor > 0, mensagem);
}

function exigirInteiroNaoNegativo(valor, mensagem) {
  exigir(Number.isInteger(valor) && valor >= 0, mensagem);
}

/**
 * Login: 3 a 30 caracteres, comecando com letra. Devolve normalizado (minusculas).
 */
function normalizarLogin(login) {
  const l = String(login || '').trim().toLowerCase();
  exigir(/^[a-z][a-z0-9._]{2,29}$/.test(l), 'Login invalido (3 a 30 caracteres, comecando com letra)');
  return l;
}

function exigirSenhaNova(senha) {
  exigir(typeof senha === 'string' && senha.length >= 6, 'Senha deve ter pelo menos 6 caracteres');
}

module.exports = {
  validarCPF,
  validarCNPJ,
  validarEmail,
  telefoneValido,
  cepValido,
  exigir,
  exigirInteiroPositivo,
  exigirInteiroNaoNegativo,
  normalizarLogin,
  exigirSenhaNova,
};
