'use strict';

// Recibo do pedido para a impressora termica.

const { carregarPedido } = require('./pedidos');
const { formatarDataHora } = require('../comum/datas');
const { formatarMoeda, valorPorExtenso } = require('../comum/moeda');
const { mascararCPF } = require('../comum/documentos');

const NOMES_PAGAMENTO = {
  dinheiro: 'Dinheiro',
  pix: 'PIX',
  cartao_credito: 'Cartao de credito',
  cartao_debito: 'Cartao de debito',
};

/**
 * Texto do recibo para imprimir na termica (40 colunas).
 */
function gerarRecibo(db, id) {
  const ped = carregarPedido(db, id);
  if (!ped) throw new Error('Pedido nao encontrado');
  const cli = db.prepare('SELECT nome, cpf FROM clientes WHERE id = ?').get(ped.cliente_id);
  const vend = db.prepare('SELECT nome FROM usuarios WHERE id = ?').get(ped.usuario_id);
  const larg = 40;
  const sep = '-'.repeat(larg);
  const centro = (t) => {
    const esp = Math.max(0, Math.floor((larg - t.length) / 2));
    return ' '.repeat(esp) + t;
  };
  const coluna = (esq, dir) => {
    const esp = Math.max(1, larg - esq.length - dir.length);
    return esq + ' '.repeat(esp) + dir;
  };

  const l = [];
  l.push(centro('LOJA DO BAIRRO'));
  l.push(centro('Recibo do pedido ' + ped.id));
  l.push(sep);
  l.push('Data: ' + formatarDataHora(ped.criado_em));
  l.push('Cliente: ' + (cli ? cli.nome : '?'));
  if (ped.cpf_nota) l.push('CPF na nota: ' + mascararCPF(ped.cpf_nota));
  l.push('Vendedor: ' + (vend ? vend.nome : '?'));
  l.push(sep);
  for (const it of ped.itens) {
    l.push(it.nome.slice(0, larg));
    l.push(coluna('  ' + it.quantidade + ' x ' + formatarMoeda(it.preco_unitario), formatarMoeda(it.total)));
  }
  l.push(sep);
  l.push(coluna('Subtotal', formatarMoeda(ped.subtotal)));
  if (ped.desconto > 0) {
    l.push(coluna('Desconto' + (ped.cupom ? ' (' + ped.cupom + ')' : ''), '-' + formatarMoeda(ped.desconto)));
  }
  l.push(coluna('TOTAL', formatarMoeda(ped.total)));
  l.push('(' + valorPorExtenso(ped.total) + ')');
  if (ped.status === 'pago') {
    l.push('Pago em ' + (NOMES_PAGAMENTO[ped.forma_pagamento] || ped.forma_pagamento));
  } else if (ped.status === 'cancelado') {
    l.push(centro('*** PEDIDO CANCELADO ***'));
  } else {
    l.push('Aguardando pagamento');
  }
  l.push(sep);
  l.push(centro('Obrigado pela preferencia!'));
  return l.join('\n');
}

module.exports = { gerarRecibo };
