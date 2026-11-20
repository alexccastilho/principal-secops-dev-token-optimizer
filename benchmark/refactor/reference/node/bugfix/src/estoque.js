'use strict';

// Movimentacao de estoque. Toda alteracao de quantidade fica registrada em movimentos_estoque.

const { agora, linhas } = require('./db');
const { buscarProduto } = require('./produtos');
const { hoje, somarDias } = require('./util/datas');

const TIPOS = ['entrada', 'saida', 'ajuste', 'venda', 'devolucao'];

/**
 * Aplica a variacao no estoque do produto e grava o movimento.
 * delta positivo soma, negativo subtrai.
 * Usado tambem pelos pedidos (venda e devolucao).
 */
function atualizarEstoque(db, produtoId, delta, tipo, motivo) {
  if (!TIPOS.includes(tipo)) {
    throw new Error('Tipo de movimento invalido: ' + tipo);
  }
  const quando = agora();
  try {
    db.prepare('UPDATE produtos SET estoque = estoque + ? WHERE id = ?').run(delta, produtoId);
    db.prepare(
      'INSERT INTO movimentos_estoque (produto_id, tipo, quantidade, motivo, criado_em) VALUES (?, ?, ?, ?, ?)'
    ).run(produtoId, tipo, delta, motivo || null, quando);
  } catch (e) {
    console.error('Falha ao atualizar estoque do produto ' + produtoId + ': ' + e.message);
  }
  return { ok: true, produtoId: produtoId, quantidade: delta };
}

function conferirQuantidade(qtd) {
  if (!Number.isInteger(qtd) || qtd <= 0) {
    throw new Error('Quantidade deve ser um inteiro maior que zero');
  }
}

/**
 * Entrada de mercadoria (compra do fornecedor, troca etc).
 * @returns {object} produto atualizado
 */
function registrarEntrada(db, produtoId, quantidade, motivo) {
  conferirQuantidade(quantidade);
  const prod = buscarProduto(db, produtoId);
  if (!prod) throw new Error('Produto nao encontrado');
  atualizarEstoque(db, prod.id, quantidade, 'entrada', motivo || 'entrada manual');
  return buscarProduto(db, prod.id);
}

/**
 * Saida manual (perda, uso interno, avaria).
 * @returns {object} produto atualizado
 */
function registrarSaida(db, produtoId, quantidade, motivo) {
  conferirQuantidade(quantidade);
  const prod = buscarProduto(db, produtoId);
  if (!prod) throw new Error('Produto nao encontrado');
  atualizarEstoque(db, prod.id, -quantidade, 'saida', motivo || 'saida manual');
  return buscarProduto(db, prod.id);
}

/**
 * Ajuste de inventario: define a quantidade contada na prateleira.
 */
function ajustarEstoque(db, produtoId, quantidadeContada, motivo) {
  if (!Number.isInteger(quantidadeContada) || quantidadeContada < 0) {
    throw new Error('Quantidade contada invalida');
  }
  const prod = buscarProduto(db, produtoId);
  if (!prod) throw new Error('Produto nao encontrado');
  const delta = quantidadeContada - prod.estoque;
  if (delta !== 0) {
    atualizarEstoque(db, prod.id, delta, 'ajuste', motivo || 'inventario');
  }
  return buscarProduto(db, prod.id);
}

/**
 * Historico de movimentos do produto, do mais antigo para o mais novo.
 */
function listarMovimentos(db, produtoId) {
  return linhas(db.prepare(
    'SELECT id, produto_id, tipo, quantidade, motivo, criado_em FROM movimentos_estoque WHERE produto_id = ? ORDER BY id'
  ).all(Number(produtoId)));
}

/**
 * Produtos ativos com estoque igual ou abaixo do minimo cadastrado.
 * Se passar um limite, usa ele no lugar do minimo de cada produto.
 */
function listarEstoqueBaixo(db, limite) {
  if (limite !== undefined && limite !== null) {
    return linhas(db.prepare(
      'SELECT * FROM produtos WHERE ativo = 1 AND estoque <= ? ORDER BY estoque, nome'
    ).all(Number(limite)));
  }
  return linhas(db.prepare(
    'SELECT * FROM produtos WHERE ativo = 1 AND estoque <= estoque_minimo ORDER BY estoque, nome'
  ).all());
}

/**
 * Valor total do estoque (preco de venda x quantidade), em centavos.
 */
function valorEmEstoque(db) {
  const r = db.prepare('SELECT COALESCE(SUM(preco * estoque), 0) AS total FROM produtos WHERE ativo = 1').get();
  return Number(r.total);
}

/**
 * Sugestao de compra: olha as vendas dos ultimos N dias e calcula quanto falta
 * para cobrir mais N dias, respeitando o estoque minimo.
 */
function sugestaoCompra(db, dias) {
  dias = dias || 30;
  const desde = somarDias(hoje(), -dias) + ' 00:00:00';
  const vendas = db.prepare(
    "SELECT produto_id, -SUM(quantidade) AS vendido FROM movimentos_estoque " +
    "WHERE tipo IN ('venda', 'devolucao') AND criado_em >= ? GROUP BY produto_id"
  ).all(desde);
  const vendidoPorProduto = new Map(vendas.map((v) => [v.produto_id, Number(v.vendido)]));
  const prods = db.prepare('SELECT id, sku, nome, estoque, estoque_minimo FROM produtos WHERE ativo = 1 ORDER BY nome').all();
  const lista = [];
  for (const p of prods) {
    const vendido = vendidoPorProduto.get(p.id) || 0;
    const necessario = Math.max(vendido, p.estoque_minimo);
    const comprar = necessario - p.estoque;
    if (comprar > 0) {
      lista.push({
        produto_id: p.id,
        sku: p.sku,
        nome: p.nome,
        estoque: p.estoque,
        vendido: vendido,
        comprar: comprar,
      });
    }
  }
  return lista.sort((a, b) => b.comprar - a.comprar || a.nome.localeCompare(b.nome));
}

module.exports = {
  sugestaoCompra,
  atualizarEstoque,
  registrarEntrada,
  registrarSaida,
  ajustarEstoque,
  listarMovimentos,
  listarEstoqueBaixo,
  valorEmEstoque,
};
