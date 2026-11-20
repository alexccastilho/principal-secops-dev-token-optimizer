'use strict';

// Periodos dos relatorios: datas 'DD/MM/AAAA' ou 'AAAA-MM-DD', inclusivas.

const { converterDataBR } = require('../comum/datas');

function intervalo(inicio, fim) {
  const ini = converterDataBR(inicio);
  const f = converterDataBR(fim);
  if (ini > f) {
    throw new Error('Data inicial maior que a final');
  }
  // criado_em tem hora; o fim do periodo vai ate 23:59:59
  return { ini: ini + ' 00:00:00', fim: f + ' 23:59:59', iniData: ini, fimData: f };
}

/**
 * Periodo opcional ({ inicio, fim }); sem as duas datas, pega o historico inteiro.
 */
function periodoOpcional(opcoes) {
  if (opcoes && opcoes.inicio && opcoes.fim) {
    return intervalo(opcoes.inicio, opcoes.fim);
  }
  return { ini: '0000-01-01 00:00:00', fim: '9999-12-31 23:59:59' };
}

module.exports = { intervalo, periodoOpcional };
