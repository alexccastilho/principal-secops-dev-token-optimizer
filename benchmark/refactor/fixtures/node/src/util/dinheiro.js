'use strict';

// Valores em dinheiro sao sempre inteiros em centavos (R$ 12,50 = 1250).
// Nunca guardar float no banco.

/**
 * Formata centavos no padrao brasileiro: 123456 -> "R$ 1.234,56"
 * @param {number} centavos
 * @returns {string}
 */
function formatarMoeda(centavos) {
  if (centavos === null || centavos === undefined || isNaN(centavos)) {
    centavos = 0;
  }
  centavos = Math.round(Number(centavos));
  const negativo = centavos < 0;
  const abs = Math.abs(centavos);
  const reais = Math.floor(abs / 100);
  const cents = abs % 100;
  let txt = String(reais);
  // separador de milhar
  let partes = [];
  while (txt.length > 3) {
    partes.unshift(txt.slice(-3));
    txt = txt.slice(0, -3);
  }
  partes.unshift(txt);
  const resultado = 'R$ ' + partes.join('.') + ',' + String(cents).padStart(2, '0');
  return negativo ? '-' + resultado : resultado;
}

/**
 * Converte texto digitado pelo usuario em centavos.
 * Aceita "12,50", "1.234,56", "R$ 10", "10.5" (ponto como decimal quando
 * nao ha virgula e so uma casa ou duas depois do ponto) e numeros.
 * @param {string|number} valor
 * @returns {number} centavos
 */
function converterMoeda(valor) {
  if (typeof valor === 'number') {
    if (!isFinite(valor)) throw new Error('Valor invalido: ' + valor);
    return Math.round(valor * 100);
  }
  if (valor === null || valor === undefined) {
    throw new Error('Valor nao informado');
  }
  let txt = String(valor).trim().replace(/^R\$\s*/i, '').replace(/\s/g, '');
  if (txt === '') throw new Error('Valor nao informado');
  let negativo = false;
  if (txt.startsWith('-')) {
    negativo = true;
    txt = txt.slice(1);
  }
  if (txt.indexOf(',') >= 0) {
    txt = txt.replace(/\./g, '').replace(',', '.');
  } else if (/^\d+\.\d{3}$/.test(txt) || /^\d{1,3}(\.\d{3})+$/.test(txt)) {
    // 1.234 -> mil duzentos e trinta e quatro
    txt = txt.replace(/\./g, '');
  }
  if (!/^\d+(\.\d{1,2})?$/.test(txt)) {
    throw new Error('Valor invalido: ' + valor);
  }
  const [inteiro, dec = ''] = txt.split('.');
  const centavos = parseInt(inteiro, 10) * 100 + parseInt((dec + '00').slice(0, 2), 10);
  return negativo ? -centavos : centavos;
}

// usado na epoca do caixa antigo, que so trabalhava com multiplos de 5 centavos
function arredondarCincoCentavos(centavos) {
  const resto = centavos % 5;
  if (resto === 0) return centavos;
  if (resto >= 3) return centavos + (5 - resto);
  return centavos - resto;
}

const UNIDADES = ['', 'um', 'dois', 'tres', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove',
  'dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove'];
const DEZENAS = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa'];
const CENTENAS = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos',
  'setecentos', 'oitocentos', 'novecentos'];

function extensoAteMil(n) {
  if (n === 0) return '';
  if (n === 100) return 'cem';
  const partes = [];
  const c = Math.floor(n / 100);
  const resto = n % 100;
  if (c > 0) partes.push(CENTENAS[c]);
  if (resto > 0) {
    if (resto < 20) {
      partes.push(UNIDADES[resto]);
    } else {
      const d = Math.floor(resto / 10);
      const u = resto % 10;
      partes.push(u > 0 ? DEZENAS[d] + ' e ' + UNIDADES[u] : DEZENAS[d]);
    }
  }
  return partes.join(' e ');
}

/**
 * Valor por extenso para o recibo: 12345 -> "cento e vinte e tres reais e quarenta e cinco centavos"
 * Vai ate 999.999,99, que e mais do que a loja vende num pedido.
 */
function valorPorExtenso(centavos) {
  centavos = Math.round(Number(centavos) || 0);
  if (centavos < 0) {
    return 'menos ' + valorPorExtenso(-centavos);
  }
  if (centavos === 0) return 'zero real';
  const reais = Math.floor(centavos / 100);
  const cents = centavos % 100;
  if (reais > 999999) {
    throw new Error('Valor alto demais para escrever por extenso');
  }
  const partes = [];
  if (reais > 0) {
    const milhares = Math.floor(reais / 1000);
    const resto = reais % 1000;
    let txt = '';
    if (milhares > 0) {
      txt = milhares === 1 ? 'mil' : extensoAteMil(milhares) + ' mil';
      if (resto > 0) {
        txt += (resto < 100 || resto % 100 === 0 ? ' e ' : ' ') + extensoAteMil(resto);
      }
    } else {
      txt = extensoAteMil(resto);
    }
    partes.push(txt + (reais === 1 ? ' real' : ' reais'));
  }
  if (cents > 0) {
    partes.push(extensoAteMil(cents) + (cents === 1 ? ' centavo' : ' centavos'));
  }
  return partes.join(' e ');
}

/**
 * Divide um valor em N parcelas iguais; a diferenca de centavos vai na primeira.
 * 10000 em 3 -> [3334, 3333, 3333]
 */
function parcelar(centavos, parcelas) {
  if (!Number.isInteger(parcelas) || parcelas < 1 || parcelas > 12) {
    throw new Error('Numero de parcelas invalido');
  }
  const base = Math.floor(centavos / parcelas);
  const resto = centavos - base * parcelas;
  const lista = [];
  for (let i = 0; i < parcelas; i++) {
    lista.push(i === 0 ? base + resto : base);
  }
  return lista;
}

module.exports = {
  formatarMoeda,
  converterMoeda,
  arredondarCincoCentavos,
  valorPorExtenso,
  parcelar,
};
