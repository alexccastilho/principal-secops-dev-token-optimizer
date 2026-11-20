'use strict';

// Exportacoes em CSV (separador ;) do cadastro de clientes e dos pedidos.

const { formatarData, formatarDataHora } = require('../comum/datas');
const { gerarCSV } = require('../comum/csv');
const { formatarTelefone } = require('../cadastro/clientes');
const { periodoOpcional } = require('./periodo');

/**
 * Exporta o cadastro de clientes em CSV (separador ;).
 */
function exportarClientesCSV(db, opcoes) {
  const rows = db.prepare('SELECT * FROM clientes ORDER BY nome, id').all();
  const cab = ['id', 'nome', 'cpf', 'email', 'telefone', 'cep', 'observacao', 'cadastro'];
  const dados = rows.map((c) => [
    c.id,
    c.nome,
    c.cpf,
    c.email || '',
    c.telefone ? formatarTelefone(c.telefone) : '',
    c.cep ? c.cep.slice(0, 5) + '-' + c.cep.slice(5) : '',
    c.observacao || '',
    formatarData(c.criado_em),
  ]);
  return gerarCSV(cab, dados, opcoes);
}

function centavosParaTexto(c) {
  const neg = c < 0;
  const abs = Math.abs(c);
  return (neg ? '-' : '') + Math.floor(abs / 100) + ',' + String(abs % 100).padStart(2, '0');
}

/**
 * Exporta pedidos em CSV. Valores em reais com virgula (sem "R$"), para somar na planilha.
 * opcoes: { inicio, fim, bom }
 */
function exportarPedidosCSV(db, opcoes) {
  const op = opcoes || {};
  const { ini, fim } = periodoOpcional(op);
  const rows = db.prepare(
    'SELECT p.id, p.criado_em, c.nome AS cliente, c.cpf, u.login AS vendedor, p.status, ' +
    'p.forma_pagamento, p.cupom, p.subtotal, p.desconto, p.total ' +
    'FROM pedidos p JOIN clientes c ON c.id = p.cliente_id JOIN usuarios u ON u.id = p.usuario_id ' +
    'WHERE p.criado_em BETWEEN ? AND ? ORDER BY p.id'
  ).all(ini, fim);
  const cab = ['pedido', 'data', 'cliente', 'cpf', 'vendedor', 'status', 'pagamento', 'cupom', 'subtotal', 'desconto', 'total'];
  const dados = rows.map((r) => [
    r.id,
    formatarDataHora(r.criado_em),
    r.cliente,
    r.cpf,
    r.vendedor,
    r.status,
    r.forma_pagamento || '',
    r.cupom || '',
    centavosParaTexto(r.subtotal),
    centavosParaTexto(r.desconto),
    centavosParaTexto(r.total),
  ]);
  return gerarCSV(cab, dados, { bom: op.bom !== false });
}

module.exports = {
  exportarClientesCSV,
  exportarPedidosCSV,
};
