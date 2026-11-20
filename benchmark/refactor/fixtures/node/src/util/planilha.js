'use strict';

// Leitura da planilha de clientes exportada pelo sistema anterior da loja
// (arquivo .csv com virgula como separador e colunas fixas).
// Usado na migracao de 2019.

const fs = require('node:fs');
const { limparNumeros, validarCPF, formatarCPF } = require('./documentos');

const COLUNAS_ANTIGAS = ['codigo', 'nome', 'cpf', 'fone', 'email', 'cep', 'obs'];

/**
 * Quebra uma linha de CSV respeitando campos entre aspas.
 */
function quebrarLinha(linha, separador) {
  const campos = [];
  let atual = '';
  let dentroAspas = false;
  for (let i = 0; i < linha.length; i++) {
    const c = linha[i];
    if (dentroAspas) {
      if (c === '"') {
        if (linha[i + 1] === '"') {
          atual += '"';
          i++;
        } else {
          dentroAspas = false;
        }
      } else {
        atual += c;
      }
    } else if (c === '"') {
      dentroAspas = true;
    } else if (c === separador) {
      campos.push(atual);
      atual = '';
    } else {
      atual += c;
    }
  }
  campos.push(atual);
  return campos;
}

/**
 * Le o texto da planilha e devolve { validos, rejeitados }.
 * Cada valido vem no formato aceito por criarCliente.
 */
function lerPlanilhaClientes(texto, opcoes) {
  const op = Object.assign({ separador: ',', temCabecalho: true }, opcoes || {});
  const linhas = String(texto).replace(/^﻿/, '').split(/\r?\n/);
  const validos = [];
  const rejeitados = [];
  let inicio = op.temCabecalho ? 1 : 0;

  for (let i = inicio; i < linhas.length; i++) {
    const bruta = linhas[i];
    if (!bruta || !bruta.trim()) continue;
    const campos = quebrarLinha(bruta, op.separador);
    const reg = {};
    COLUNAS_ANTIGAS.forEach((col, idx) => {
      reg[col] = (campos[idx] || '').trim();
    });

    if (!reg.nome) {
      rejeitados.push({ linha: i + 1, motivo: 'sem nome', dados: reg });
      continue;
    }
    const cpf = limparNumeros(reg.cpf);
    if (!validarCPF(cpf)) {
      rejeitados.push({ linha: i + 1, motivo: 'cpf invalido', dados: reg });
      continue;
    }
    let telefone = limparNumeros(reg.fone);
    // o sistema antigo gravava sem DDD; a loja e de Sao Paulo
    if (telefone.length === 8 || telefone.length === 9) {
      telefone = '11' + telefone;
    }
    validos.push({
      nome: normalizarNome(reg.nome),
      cpf: formatarCPF(cpf),
      email: reg.email ? reg.email.toLowerCase() : null,
      telefone: telefone || null,
      cep: limparNumeros(reg.cep) || null,
      observacao: reg.obs || null,
      codigoAntigo: reg.codigo,
    });
  }
  return { validos, rejeitados };
}

/**
 * "MARIA DA SILVA" -> "Maria da Silva"
 */
function normalizarNome(nome) {
  const minusculas = ['da', 'de', 'do', 'das', 'dos', 'e'];
  return String(nome)
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .map((p, i) => (i > 0 && minusculas.includes(p) ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join(' ');
}

/**
 * Le o arquivo do disco (latin1, como o sistema antigo gravava).
 */
function lerArquivoPlanilha(caminho, opcoes) {
  const buf = fs.readFileSync(caminho);
  const texto = buf.toString('latin1');
  return lerPlanilhaClientes(texto, opcoes);
}

/**
 * Resumo para mostrar no fim da importacao.
 */
function resumoImportacao(resultado) {
  const porMotivo = {};
  for (const r of resultado.rejeitados) {
    porMotivo[r.motivo] = (porMotivo[r.motivo] || 0) + 1;
  }
  const partes = Object.keys(porMotivo).map((k) => k + ': ' + porMotivo[k]);
  return 'Importados: ' + resultado.validos.length +
    '. Rejeitados: ' + resultado.rejeitados.length +
    (partes.length ? ' (' + partes.join(', ') + ')' : '') + '.';
}

module.exports = {
  quebrarLinha,
  lerPlanilhaClientes,
  lerArquivoPlanilha,
  normalizarNome,
  resumoImportacao,
};
