'use strict';

// Orcamento rapido para o balcao: calcula quanto o cliente vai pagar sem gravar nada
// e sem mexer no estoque. Mesmas regras de desconto do pedido.

const { lerCupom, calcularDesconto, precificarItens, totalDosItens } = require('./descontos');
const { exigirItens } = require('./validacaoPedido');

/**
 * Calcula o orcamento.
 * @param {DatabaseSync} db
 * @param {Array<{produtoId:number, quantidade:number}>} itens
 * @param {string} [cupom]
 * @returns {{itens:Array, subtotal:number, desconto:number, total:number, cupom:string|null}}
 */
function calcularOrcamento(db, itens, cupom) {
  exigirItens(itens);
  const linhas = precificarItens(db, itens, false);
  const subtotal = totalDosItens(linhas);
  const regra = lerCupom(cupom);
  const desconto = calcularDesconto(subtotal, regra);
  return {
    itens: linhas,
    subtotal: subtotal,
    desconto: desconto,
    total: subtotal - desconto,
    cupom: regra ? regra.codigo : null,
  };
}

module.exports = { calcularOrcamento };
