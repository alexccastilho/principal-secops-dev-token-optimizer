'use strict';

// Regras de preco e desconto, compartilhadas entre pedido e orcamento.
// Cupom e desconto por valor nao acumulam: vale o maior.

const CUPONS = {
  BAIRRO10: { percentual: 10, somentePrimeiraCompra: false },
  PRIMEIRA: { percentual: 15, somentePrimeiraCompra: true },
};

const DESCONTO_POR_VALOR_PCT = 10;

/**
 * Desconto por valor do pedido (desconto progressivo), em centavos.
 * @param {number} subtotal em centavos
 * @returns {number} desconto em centavos
 */
function descontoPorValor(subtotal) {
  if (subtotal > 50000) {
    return Math.round((subtotal * DESCONTO_POR_VALOR_PCT) / 100);
  }
  return 0;
}

/**
 * Normaliza e confere o codigo do cupom. Devolve null quando nao ha cupom.
 * @returns {{codigo:string, percentual:number, somentePrimeiraCompra:boolean}|null}
 */
function lerCupom(cupom) {
  if (!cupom) return null;
  const codigo = String(cupom).trim().toUpperCase();
  const regra = CUPONS[codigo];
  if (!regra) {
    throw new Error('Cupom invalido: ' + codigo);
  }
  return Object.assign({ codigo }, regra);
}

/**
 * Calcula o desconto final do subtotal com o cupom (ja lido por lerCupom).
 */
function calcularDesconto(subtotal, cupom) {
  const doCupom = cupom ? Math.round((subtotal * cupom.percentual) / 100) : 0;
  return Math.max(doCupom, descontoPorValor(subtotal));
}

/**
 * Soma quantidade x preco unitario dos itens ja precificados.
 */
function totalDosItens(itens) {
  return itens.reduce((total, it) => total + it.quantidade * it.preco_unitario, 0);
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

/**
 * Busca os produtos dos itens e devolve as linhas precificadas.
 * Confere produto existente e ativo; com conferirEstoque, confere tambem a quantidade disponivel.
 */
function precificarItens(db, itens, conferirEstoque) {
  return agruparItens(itens).map((it) => {
    const prod = db.prepare('SELECT * FROM produtos WHERE id = ?').get(it.produtoId);
    if (!prod) throw new Error('Produto nao encontrado: ' + it.produtoId);
    if (!prod.ativo) throw new Error('Produto inativo: ' + prod.sku);
    if (conferirEstoque && prod.estoque < it.quantidade) {
      throw new Error('Estoque insuficiente para ' + prod.sku + ' (disponivel: ' + prod.estoque + ')');
    }
    return {
      produto_id: prod.id,
      sku: prod.sku,
      nome: prod.nome,
      quantidade: it.quantidade,
      preco_unitario: prod.preco,
      total: prod.preco * it.quantidade,
    };
  });
}

module.exports = {
  descontoPorValor,
  lerCupom,
  calcularDesconto,
  totalDosItens,
  agruparItens,
  precificarItens,
};
