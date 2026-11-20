'use strict';

// Datas: no banco guardamos 'AAAA-MM-DD' ou 'AAAA-MM-DD HH:MM:SS' (hora local).
// Na tela e no CSV mostramos no formato brasileiro DD/MM/AAAA.

const MESES = [
  'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

function doisDigitos(n) {
  return String(n).padStart(2, '0');
}

/**
 * Formata uma data para DD/MM/AAAA.
 * Aceita Date, 'AAAA-MM-DD' ou 'AAAA-MM-DD HH:MM:SS'.
 * Nao usa new Date(string) para nao sofrer com fuso (UTC x horario de Brasilia).
 */
function formatarData(valor) {
  if (!valor) return '';
  if (valor instanceof Date) {
    return doisDigitos(valor.getDate()) + '/' + doisDigitos(valor.getMonth() + 1) + '/' + valor.getFullYear();
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(valor));
  if (!m) {
    throw new Error('Data invalida: ' + valor);
  }
  return m[3] + '/' + m[2] + '/' + m[1];
}

/**
 * Formata data e hora: 'AAAA-MM-DD HH:MM:SS' -> 'DD/MM/AAAA HH:MM'
 */
function formatarDataHora(valor) {
  if (!valor) return '';
  const m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/.exec(String(valor));
  if (!m) {
    return formatarData(valor);
  }
  return m[3] + '/' + m[2] + '/' + m[1] + ' ' + m[4] + ':' + m[5];
}

function anoBissexto(ano) {
  return (ano % 4 === 0 && ano % 100 !== 0) || ano % 400 === 0;
}

function diasNoMes(ano, mes) {
  const dias = [31, anoBissexto(ano) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return dias[mes - 1];
}

/**
 * Converte 'DD/MM/AAAA' em 'AAAA-MM-DD'. Lanca erro se a data nao existir.
 * Tambem aceita 'AAAA-MM-DD' (devolve como esta, depois de validar).
 */
function converterDataBR(texto) {
  if (!texto) throw new Error('Data nao informada');
  texto = String(texto).trim();
  let dia, mes, ano;
  let m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(texto);
  if (m) {
    dia = parseInt(m[1], 10);
    mes = parseInt(m[2], 10);
    ano = parseInt(m[3], 10);
  } else {
    m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto);
    if (!m) throw new Error('Data invalida: ' + texto);
    ano = parseInt(m[1], 10);
    mes = parseInt(m[2], 10);
    dia = parseInt(m[3], 10);
  }
  if (mes < 1 || mes > 12) throw new Error('Data invalida: ' + texto);
  if (dia < 1 || dia > diasNoMes(ano, mes)) throw new Error('Data invalida: ' + texto);
  return ano + '-' + doisDigitos(mes) + '-' + doisDigitos(dia);
}

/**
 * Data de hoje em 'AAAA-MM-DD' (hora local).
 */
function hoje() {
  const d = new Date();
  return d.getFullYear() + '-' + doisDigitos(d.getMonth() + 1) + '-' + doisDigitos(d.getDate());
}

/**
 * Soma dias a uma data 'AAAA-MM-DD'.
 */
function somarDias(dataIso, dias) {
  const [a, m, d] = dataIso.split('-').map((x) => parseInt(x, 10));
  const dt = new Date(a, m - 1, d);
  dt.setDate(dt.getDate() + dias);
  return dt.getFullYear() + '-' + doisDigitos(dt.getMonth() + 1) + '-' + doisDigitos(dt.getDate());
}

/**
 * Nome do mes por extenso, ex.: mesPorExtenso('2024-03-10') -> 'marco de 2024'
 */
function mesPorExtenso(dataIso) {
  const m = /^(\d{4})-(\d{2})/.exec(String(dataIso));
  if (!m) return '';
  return MESES[parseInt(m[2], 10) - 1] + ' de ' + m[1];
}

// Feriados nacionais de data fixa (MM-DD). Carnaval e Corpus Christi a loja abre.
const FERIADOS_FIXOS = ['01-01', '04-21', '05-01', '09-07', '10-12', '11-02', '11-15', '11-20', '12-25'];

/**
 * Dia da semana de uma data 'AAAA-MM-DD' (0 = domingo).
 */
function diaDaSemana(dataIso) {
  const [a, m, d] = dataIso.split('-').map((x) => parseInt(x, 10));
  return new Date(a, m - 1, d).getDay();
}

function ehFeriado(dataIso) {
  return FERIADOS_FIXOS.includes(dataIso.slice(5));
}

/**
 * A loja fecha domingo e feriado.
 */
function lojaAberta(dataIso) {
  return diaDaSemana(dataIso) !== 0 && !ehFeriado(dataIso);
}

/**
 * Conta os dias de loja aberta entre duas datas (inclusive).
 */
function diasDeLojaAberta(inicioIso, fimIso) {
  if (inicioIso > fimIso) return 0;
  let n = 0;
  let d = inicioIso;
  let guarda = 0;
  while (d <= fimIso && guarda < 3700) {
    if (lojaAberta(d)) n++;
    d = somarDias(d, 1);
    guarda++;
  }
  return n;
}

/**
 * Primeiro e ultimo dia do mes de uma data.
 */
function limitesDoMes(ano, mes) {
  return {
    inicio: ano + '-' + doisDigitos(mes) + '-01',
    fim: ano + '-' + doisDigitos(mes) + '-' + doisDigitos(diasNoMes(ano, mes)),
  };
}

module.exports = {
  diaDaSemana,
  lojaAberta,
  diasDeLojaAberta,
  limitesDoMes,
  formatarData,
  formatarDataHora,
  converterDataBR,
  hoje,
  somarDias,
  mesPorExtenso,
  diasNoMes,
};
