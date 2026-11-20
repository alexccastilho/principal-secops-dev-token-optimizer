'use strict';

// Geracao de CSV no formato que o Excel em portugues abre direto:
// separador ponto e virgula, quebra de linha CRLF e BOM no inicio.

const SEPARADOR = ';';
const QUEBRA = '\r\n';

/**
 * Prepara um valor para entrar numa celula do CSV.
 * Coloca aspas quando o texto tem separador, aspas ou quebra de linha.
 */
function campoCSV(valor) {
  if (valor === null || valor === undefined) return '';
  let txt = String(valor);
  if (txt.indexOf('"') >= 0) {
    txt = txt.replace(/"/g, '""');
  }
  if (txt.indexOf(SEPARADOR) >= 0 || txt.indexOf('"') >= 0 || /[\r\n]/.test(txt)) {
    txt = '"' + txt + '"';
  }
  return txt;
}

function linhaCSV(campos) {
  return campos.map(campoCSV).join(SEPARADOR);
}

/**
 * Monta o CSV completo a partir do cabecalho e das linhas (arrays).
 * @param {string[]} cabecalho
 * @param {Array<Array<any>>} linhas
 * @param {object} [opcoes] { bom: true }
 */
function gerarCSV(cabecalho, linhas, opcoes) {
  const op = Object.assign({ bom: true }, opcoes || {});
  const saida = [linhaCSV(cabecalho)];
  for (const l of linhas) {
    saida.push(linhaCSV(l));
  }
  return (op.bom ? '﻿' : '') + saida.join(QUEBRA) + QUEBRA;
}

module.exports = {
  campoCSV,
  linhaCSV,
  gerarCSV,
  SEPARADOR,
};
