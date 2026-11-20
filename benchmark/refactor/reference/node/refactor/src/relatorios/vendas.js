'use strict';

// Relatorios de vendas para o dono da loja. As exportacoes CSV ficam em exportacao.js.
// Pedidos cancelados nunca entram nos totais de venda.

const { linhas } = require('../infra/banco');
const { limitesDoMes, diasDeLojaAberta, mesPorExtenso } = require('../comum/datas');
const { intervalo, periodoOpcional } = require('./periodo');

/**
 * Vendas no periodo (datas 'DD/MM/AAAA' ou 'AAAA-MM-DD', inclusivas).
 * @returns {{inicio:string, fim:string, quantidade:number, subtotal:number, desconto:number, total:number, dias:Array}}
 */
function vendasPorPeriodo(db, inicio, fim) {
  const p = intervalo(inicio, fim);
  const tot = db.prepare(
    "SELECT COUNT(*) AS quantidade, COALESCE(SUM(subtotal), 0) AS subtotal, " +
    "COALESCE(SUM(desconto), 0) AS desconto, COALESCE(SUM(total), 0) AS total " +
    "FROM pedidos WHERE status <> 'cancelado' AND criado_em BETWEEN ? AND ?"
  ).get(p.ini, p.fim);
  const dias = db.prepare(
    "SELECT substr(criado_em, 1, 10) AS data, COUNT(*) AS quantidade, SUM(total) AS total " +
    "FROM pedidos WHERE status <> 'cancelado' AND criado_em BETWEEN ? AND ? " +
    "GROUP BY substr(criado_em, 1, 10) ORDER BY data"
  ).all(p.ini, p.fim);
  return {
    inicio: p.iniData,
    fim: p.fimData,
    quantidade: Number(tot.quantidade),
    subtotal: Number(tot.subtotal),
    desconto: Number(tot.desconto),
    total: Number(tot.total),
    dias: dias.map((d) => ({ data: d.data, quantidade: Number(d.quantidade), total: Number(d.total) })),
  };
}

/**
 * Produtos mais vendidos por quantidade.
 * opcoes: { limite = 10, inicio, fim }
 */
function produtosMaisVendidos(db, opcoes) {
  const op = opcoes || {};
  const limite = op.limite ? Number(op.limite) : 10;
  const { ini, fim } = periodoOpcional(op);
  return linhas(db.prepare(
    'SELECT pr.id AS produto_id, pr.sku, pr.nome, SUM(i.quantidade) AS quantidade, SUM(i.total) AS total ' +
    'FROM itens_pedido i ' +
    'JOIN pedidos pe ON pe.id = i.pedido_id ' +
    'JOIN produtos pr ON pr.id = i.produto_id ' +
    "WHERE pe.status <> 'cancelado' AND pe.criado_em BETWEEN ? AND ? " +
    'GROUP BY pr.id ORDER BY quantidade DESC, total DESC, pr.nome LIMIT ?'
  ).all(ini, fim, limite));
}

// colunas aceitas -> expressao SQL (nada vindo do chamador entra direto no SQL)
const COLUNAS_ORDENACAO = {
  criado_em: 'p.criado_em',
  total: 'p.total',
  cliente: 'c.nome',
  vendedor: 'u.nome',
  status: 'p.status',
};

/**
 * Lista de pedidos para a tela de relatorio, ordenada pela coluna escolhida.
 * Colunas usadas na tela: criado_em, total, cliente, vendedor, status.
 * @param {DatabaseSync} db
 * @param {string} [ordenarPor='criado_em']
 * @param {string} [direcao='asc']
 */
function relatorioPedidos(db, ordenarPor, direcao) {
  const chave = ordenarPor || 'criado_em';
  const coluna = Object.hasOwn(COLUNAS_ORDENACAO, chave) ? COLUNAS_ORDENACAO[chave] : null;
  if (!coluna) {
    throw new Error('Coluna de ordenacao invalida: ' + ordenarPor);
  }
  const dir = String(direcao || 'asc').toLowerCase() === 'desc' ? 'DESC' : 'ASC';
  const sql =
    'SELECT p.id, p.criado_em, c.nome AS cliente, u.nome AS vendedor, p.status, ' +
    'p.subtotal, p.desconto, p.total ' +
    'FROM pedidos p ' +
    'JOIN clientes c ON c.id = p.cliente_id ' +
    'JOIN usuarios u ON u.id = p.usuario_id ' +
    'ORDER BY ' + coluna + ' ' + dir + ', p.id';
  return linhas(db.prepare(sql).all());
}

/**
 * Ticket medio do periodo, em centavos (0 se nao houve venda).
 */
function ticketMedio(db, inicio, fim) {
  const v = vendasPorPeriodo(db, inicio, fim);
  if (v.quantidade === 0) return 0;
  return Math.round(v.total / v.quantidade);
}

/**
 * Vendas por vendedor no periodo.
 */
function vendasPorVendedor(db, inicio, fim) {
  const p = intervalo(inicio, fim);
  return linhas(db.prepare(
    'SELECT u.id AS usuario_id, u.login, u.nome, COUNT(p.id) AS quantidade, COALESCE(SUM(p.total), 0) AS total ' +
    'FROM usuarios u LEFT JOIN pedidos p ON p.usuario_id = u.id ' +
    "AND p.status <> 'cancelado' AND p.criado_em BETWEEN ? AND ? " +
    'GROUP BY u.id ORDER BY total DESC, u.login'
  ).all(p.ini, p.fim));
}

/**
 * Curva ABC dos produtos pelo faturamento: A ate 80% do total, B ate 95%, C o resto.
 */
function curvaABC(db) {
  const rows = db.prepare(
    'SELECT pr.id AS produto_id, pr.sku, pr.nome, SUM(i.total) AS total ' +
    'FROM itens_pedido i JOIN pedidos pe ON pe.id = i.pedido_id JOIN produtos pr ON pr.id = i.produto_id ' +
    "WHERE pe.status <> 'cancelado' GROUP BY pr.id ORDER BY total DESC, pr.nome"
  ).all();
  const geral = rows.reduce((s, r) => s + Number(r.total), 0);
  let acumulado = 0;
  return rows.map((r) => {
    // a classe vem do acumulado ate o produto anterior: o primeiro e sempre A
    const antes = geral ? (acumulado * 100) / geral : 0;
    acumulado += Number(r.total);
    const pct = geral ? (acumulado * 100) / geral : 0;
    let classe = 'C';
    if (antes < 80) classe = 'A';
    else if (antes < 95) classe = 'B';
    return {
      produto_id: r.produto_id,
      sku: r.sku,
      nome: r.nome,
      total: Number(r.total),
      acumulado: Math.round(pct * 10) / 10,
      classe: classe,
    };
  });
}

/**
 * Resumo do mes para o fechamento: vendas, ticket medio, media por dia de loja aberta,
 * cancelamentos e o produto campeao.
 */
function resumoMensal(db, ano, mes) {
  ano = Number(ano);
  mes = Number(mes);
  if (!Number.isInteger(ano) || !Number.isInteger(mes) || mes < 1 || mes > 12) {
    throw new Error('Mes invalido');
  }
  const lim = limitesDoMes(ano, mes);
  const v = vendasPorPeriodo(db, lim.inicio, lim.fim);
  const canc = db.prepare(
    "SELECT COUNT(*) AS n, COALESCE(SUM(total), 0) AS total FROM pedidos " +
    "WHERE status = 'cancelado' AND criado_em BETWEEN ? AND ?"
  ).get(lim.inicio + ' 00:00:00', lim.fim + ' 23:59:59');
  const top = produtosMaisVendidos(db, { limite: 1, inicio: lim.inicio, fim: lim.fim });
  const diasAbertos = diasDeLojaAberta(lim.inicio, lim.fim);
  return {
    mes: mesPorExtenso(lim.inicio),
    quantidade: v.quantidade,
    total: v.total,
    desconto: v.desconto,
    ticketMedio: ticketMedio(db, lim.inicio, lim.fim),
    mediaPorDia: diasAbertos ? Math.round(v.total / diasAbertos) : 0,
    diasAbertos: diasAbertos,
    cancelados: Number(canc.n),
    totalCancelado: Number(canc.total),
    campeao: top.length ? top[0].nome : null,
  };
}

module.exports = {
  curvaABC,
  resumoMensal,
  vendasPorPeriodo,
  produtosMaisVendidos,
  relatorioPedidos,
  ticketMedio,
  vendasPorVendedor,
};
