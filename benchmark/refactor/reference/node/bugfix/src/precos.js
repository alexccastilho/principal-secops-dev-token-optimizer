'use strict';

// Regras de preco compartilhadas entre pedido e orcamento.

/**
 * Desconto por valor do pedido (desconto progressivo), em centavos.
 * @param {number} subtotal em centavos
 * @returns {number} desconto em centavos
 */
function descontoPorValor(subtotal) {
  if (subtotal >= 50000) {
    return Math.round(subtotal / 10);
  }
  return 0;
}

/**
 * Soma quantidade x preco unitario dos itens ja precificados.
 * @param {Array<{quantidade:number, preco_unitario:number}>} itens
 */
function totalDosItens(itens) {
  let total = 0;
  for (const it of itens) {
    total += it.quantidade * it.preco_unitario;
  }
  return total;
}

/**
 * Junta itens repetidos do mesmo produto somando as quantidades,
 * mantendo a ordem em que apareceram.
 */
function agruparItens(itens) {
  const mapa = new Map();
  for (const it of itens) {
    const id = Number(it.produtoId);
    if (mapa.has(id)) {
      mapa.get(id).quantidade += it.quantidade;
    } else {
      mapa.set(id, { produtoId: id, quantidade: it.quantidade });
    }
  }
  return Array.from(mapa.values());
}

module.exports = {
  descontoPorValor,
  totalDosItens,
  agruparItens,
};
