'use strict';

// Pedidos de venda: criacao, consulta, pagamento e cancelamento.

const { agora, linha, linhas, transacao } = require('./db');
const { atualizarEstoque } = require('./estoque');
const { descontoPorValor, agruparItens } = require('./precos');
const { converterDataBR, formatarDataHora, hoje, somarDias } = require('./util/datas');
const { formatarMoeda, valorPorExtenso } = require('./util/dinheiro');
const { mascararCPF } = require('./util/documentos');

const FORMAS_PAGAMENTO = ['dinheiro', 'pix', 'cartao_credito', 'cartao_debito'];

/**
 * Cria um pedido com os itens informados, aplica descontos, baixa o estoque e grava.
 *
 * dados = {
 *   clienteId, usuarioId,
 *   itens: [{ produtoId, quantidade }],
 *   cupom?, cpfNaNota?, emailRecibo?,
 *   data?  ('AAAA-MM-DD' ou 'DD/MM/AAAA'; padrao hoje)
 * }
 *
 * Retorna o pedido completo (mesmo formato de buscarPedido).
 */
function criarPedido(db, dados) {
  if (!dados) {
    throw new Error('Dados do pedido nao informados');
  }

  // cliente
  if (!dados.clienteId) {
    throw new Error('Cliente nao informado');
  }
  const cliente = db.prepare('SELECT * FROM clientes WHERE id = ?').get(Number(dados.clienteId));
  if (!cliente) {
    throw new Error('Cliente nao encontrado');
  }

  // vendedor / usuario que esta lancando
  if (!dados.usuarioId) {
    throw new Error('Usuario nao informado');
  }
  const usuario = db.prepare('SELECT id, papel, ativo FROM usuarios WHERE id = ?').get(Number(dados.usuarioId));
  if (!usuario || !usuario.ativo) {
    throw new Error('Usuario invalido ou inativo');
  }

  // itens
  if (!Array.isArray(dados.itens) || dados.itens.length === 0) {
    throw new Error('Pedido sem itens');
  }
  for (const it of dados.itens) {
    if (!it || !it.produtoId) {
      throw new Error('Item sem produto');
    }
    if (!Number.isInteger(it.quantidade) || it.quantidade <= 0) {
      throw new Error('Quantidade invalida para o produto ' + it.produtoId);
    }
    if (it.quantidade > 999) {
      throw new Error('Quantidade acima do permitido por item');
    }
  }
  const agrupados = agruparItens(dados.itens);

  const itensPrecificados = [];
  for (const it of agrupados) {
    const prod = db.prepare('SELECT * FROM produtos WHERE id = ?').get(it.produtoId);
    if (!prod) {
      throw new Error('Produto nao encontrado: ' + it.produtoId);
    }
    if (!prod.ativo) {
      throw new Error('Produto inativo: ' + prod.sku);
    }
    if (prod.estoque < it.quantidade) {
      throw new Error('Estoque insuficiente para ' + prod.sku + ' (disponivel: ' + prod.estoque + ')');
    }
    itensPrecificados.push({
      produto_id: prod.id,
      sku: prod.sku,
      nome: prod.nome,
      quantidade: it.quantidade,
      preco_unitario: prod.preco,
      total: prod.preco * it.quantidade,
    });
  }

  // CPF na nota (opcional)
  let cpfNota = null;
  if (dados.cpfNaNota) {
    const n = String(dados.cpfNaNota).replace(/[.-]/g, '');
    let ok = /^\d{11}$/.test(n) && !/^(\d)\1+$/.test(n);
    if (ok) {
      for (let t = 9; t < 11; t++) {
        let s = 0;
        for (let i = 0; i < t; i++) {
          s += parseInt(n[i], 10) * (t + 1 - i);
        }
        const dv = ((s * 10) % 11) % 10;
        if (dv !== parseInt(n[t], 10)) {
          ok = false;
          break;
        }
      }
    }
    if (!ok) {
      throw new Error('CPF da nota invalido');
    }
    cpfNota = n.slice(0, 3) + '.' + n.slice(3, 6) + '.' + n.slice(6, 9) + '-' + n.slice(9);
  }

  // e-mail para o recibo (opcional; se nao vier usa o do cadastro)
  let emailRecibo = cliente.email || null;
  if (dados.emailRecibo) {
    const e = String(dados.emailRecibo).trim().toLowerCase();
    if (!/^[\w.+-]+@[\w-]+(\.[\w-]+)+$/.test(e)) {
      throw new Error('E-mail do recibo invalido');
    }
    emailRecibo = e;
  }

  // data
  let criadoEm = agora();
  if (dados.data) {
    criadoEm = converterDataBR(dados.data) + criadoEm.slice(10);
  }

  // precos e descontos
  let subtotal = 0;
  for (const it of itensPrecificados) {
    subtotal += it.total;
  }

  let cupom = null;
  let descontoCupom = 0;
  if (dados.cupom) {
    cupom = String(dados.cupom).trim().toUpperCase();
    if (cupom === 'BAIRRO10') {
      descontoCupom = Math.round(subtotal * 10 / 100);
    } else if (cupom === 'PRIMEIRA') {
      const anteriores = db.prepare(
        "SELECT COUNT(*) AS n FROM pedidos WHERE cliente_id = ? AND status <> 'cancelado'"
      ).get(cliente.id);
      if (anteriores.n > 0) {
        throw new Error('Cupom PRIMEIRA vale apenas na primeira compra');
      }
      descontoCupom = Math.round(subtotal * 15 / 100);
    } else {
      throw new Error('Cupom invalido: ' + cupom);
    }
  }

  // cupom e desconto por valor nao acumulam: vale o maior
  const descontoValor = descontoPorValor(subtotal);
  const desconto = Math.max(descontoCupom, descontoValor);
  const total = subtotal - desconto;

  // grava
  const pedidoId = transacao(db, () => {
    const r = db.prepare(
      'INSERT INTO pedidos (cliente_id, usuario_id, subtotal, desconto, total, cupom, cpf_nota, email_recibo, status, criado_em) ' +
      'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    ).run(cliente.id, usuario.id, subtotal, desconto, total, cupom, cpfNota, emailRecibo, 'aberto', criadoEm);
    const id = Number(r.lastInsertRowid);

    const insItem = db.prepare(
      'INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, total) VALUES (?, ?, ?, ?, ?)'
    );
    for (const it of itensPrecificados) {
      insItem.run(id, it.produto_id, it.quantidade, it.preco_unitario, it.total);
      atualizarEstoque(db, it.produto_id, -it.quantidade, 'venda', 'pedido ' + id);
    }
    return id;
  });

  return carregarPedido(db, pedidoId);
}

function carregarPedido(db, id) {
  const ped = linha(db.prepare('SELECT * FROM pedidos WHERE id = ?').get(Number(id)));
  if (!ped) return null;
  ped.itens = linhas(db.prepare(
    'SELECT i.produto_id, p.sku, p.nome, i.quantidade, i.preco_unitario, i.total ' +
    'FROM itens_pedido i JOIN produtos p ON p.id = i.produto_id WHERE i.pedido_id = ? ORDER BY i.id'
  ).all(ped.id));
  return ped;
}

/**
 * Busca um pedido com os itens.
 * @param {DatabaseSync} db
 * @param {number} id
 * @param {object} usuario usuario logado ({ id, papel })
 * @returns {object|null}
 */
function buscarPedido(db, id, usuario) {
  if (!usuario) {
    throw new Error('Usuario nao informado');
  }
  return carregarPedido(db, id);
}

/**
 * Lista pedidos visiveis para o usuario. Vendedor ve so os dele; admin ve tudo.
 * filtros: { status }
 */
function listarPedidos(db, usuario, filtros) {
  if (!usuario) {
    throw new Error('Usuario nao informado');
  }
  const f = filtros || {};
  const status = f.status || null;
  let rows;
  if (usuario.papel === 'admin') {
    rows = db.prepare(
      'SELECT * FROM pedidos WHERE (? IS NULL OR status = ?) ORDER BY id'
    ).all(status, status);
  } else {
    rows = db.prepare(
      'SELECT * FROM pedidos WHERE usuario_id = ? AND (? IS NULL OR status = ?) ORDER BY id'
    ).all(usuario.id, status, status);
  }
  return linhas(rows);
}

/**
 * Registra o pagamento de um pedido em aberto.
 */
function registrarPagamento(db, id, forma) {
  const ped = carregarPedido(db, id);
  if (!ped) throw new Error('Pedido nao encontrado');
  if (ped.status !== 'aberto') {
    throw new Error('Pedido nao esta em aberto (status: ' + ped.status + ')');
  }
  if (!FORMAS_PAGAMENTO.includes(forma)) {
    throw new Error('Forma de pagamento invalida: ' + forma);
  }
  db.prepare("UPDATE pedidos SET status = 'pago', forma_pagamento = ?, pago_em = ? WHERE id = ?")
    .run(forma, agora(), ped.id);
  return carregarPedido(db, ped.id);
}

/**
 * Cancela o pedido e devolve os itens ao estoque.
 * Pedido pago tambem pode ser cancelado (o estorno e feito no caixa).
 */
function cancelarPedido(db, id, usuario) {
  if (!usuario) {
    throw new Error('Usuario nao informado');
  }
  const ped = carregarPedido(db, id);
  if (!ped) throw new Error('Pedido nao encontrado');
  if (ped.status === 'cancelado') {
    throw new Error('Pedido ja cancelado');
  }
  transacao(db, () => {
    for (const it of ped.itens) {
      atualizarEstoque(db, it.produto_id, it.quantidade, 'devolucao', 'cancelamento pedido ' + ped.id);
    }
    db.prepare("UPDATE pedidos SET status = 'cancelado', cancelado_em = ?, cancelado_por = ? WHERE id = ?")
      .run(agora(), usuario.id, ped.id);
  });
  return carregarPedido(db, ped.id);
}

/**
 * Pedidos de um cliente (historico), do mais recente para o mais antigo.
 */
function pedidosDoCliente(db, clienteId) {
  return linhas(db.prepare(
    'SELECT * FROM pedidos WHERE cliente_id = ? ORDER BY criado_em DESC, id DESC'
  ).all(Number(clienteId)));
}

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

/**
 * Pedidos em aberto ha mais de N dias (para cobrar ou cancelar).
 */
function pedidosEmAbertoAntigos(db, dias) {
  const limite = somarDias(hoje(), -(dias || 7)) + ' 00:00:00';
  return linhas(db.prepare(
    "SELECT * FROM pedidos WHERE status = 'aberto' AND criado_em < ? ORDER BY criado_em"
  ).all(limite));
}

module.exports = {
  criarPedido,
  buscarPedido,
  listarPedidos,
  registrarPagamento,
  cancelarPedido,
  pedidosDoCliente,
  gerarRecibo,
  pedidosEmAbertoAntigos,
  FORMAS_PAGAMENTO,
};
