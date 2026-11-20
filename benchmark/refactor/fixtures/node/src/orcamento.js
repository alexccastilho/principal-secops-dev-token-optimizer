'use strict';

// Orcamento rapido para o balcao: calcula quanto o cliente vai pagar sem gravar nada
// e sem mexer no estoque.

const { descontoPorValor, agruparItens, totalDosItens } = require('./precos');

/**
 * Calcula o orcamento.
 * @param {DatabaseSync} db
 * @param {Array<{produtoId:number, quantidade:number}>} itens
 * @param {string} [cupom]
 * @returns {{itens:Array, subtotal:number, desconto:number, total:number, cupom:string|null}}
 */
function calcularOrcamento(db, itens, cupom) {
  if (!Array.isArray(itens) || itens.length === 0) {
    throw new Error('Orcamento sem itens');
  }
  for (const it of itens) {
    if (!it || !it.produtoId || !Number.isInteger(it.quantidade) || it.quantidade <= 0) {
      throw new Error('Item invalido no orcamento');
    }
  }

  const linhasOrc = [];
  for (const it of agruparItens(itens)) {
    const p = db.prepare('SELECT id, sku, nome, preco, ativo FROM produtos WHERE id = ?').get(it.produtoId);
    if (!p || !p.ativo) {
      throw new Error('Produto nao encontrado: ' + it.produtoId);
    }
    linhasOrc.push({
      produto_id: p.id,
      sku: p.sku,
      nome: p.nome,
      quantidade: it.quantidade,
      preco_unitario: p.preco,
      total: p.preco * it.quantidade,
    });
  }

  const subtotal = totalDosItens(linhasOrc);

  let codigo = null;
  let descCupom = 0;
  if (cupom) {
    codigo = String(cupom).trim().toUpperCase();
    switch (codigo) {
      case 'BAIRRO10':
        descCupom = Math.round(subtotal * 0.10);
        break;
      case 'PRIMEIRA':
        descCupom = Math.round(subtotal * 0.20);
        break;
      default:
        throw new Error('Cupom invalido: ' + codigo);
    }
  }

  const desconto = Math.max(descCupom, descontoPorValor(subtotal));
  return {
    itens: linhasOrc,
    subtotal: subtotal,
    desconto: desconto,
    total: subtotal - desconto,
    cupom: codigo,
  };
}

module.exports = { calcularOrcamento };
