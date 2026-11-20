'use strict';

// Cadastro de produtos. Preco sempre em centavos.
// O estoque so muda pelas funcoes de estoque.js (entrada/saida), para ficar registrado.

const { agora, linha, linhas, transacao } = require('../infra/banco');
const { exigir, exigirInteiroPositivo, exigirInteiroNaoNegativo } = require('../comum/validacao');

function normalizarSku(sku) {
  return String(sku || '').trim().toUpperCase();
}

function validarProduto(dados, parcial) {
  if (!parcial || dados.sku !== undefined) {
    exigir(/^[A-Z0-9][A-Z0-9-]{1,19}$/.test(normalizarSku(dados.sku)),
      'SKU invalido (use letras, numeros e hifen, ate 20 caracteres)');
  }
  if (!parcial || dados.nome !== undefined) {
    exigir(dados.nome && String(dados.nome).trim().length >= 2, 'Nome do produto obrigatorio');
  }
  if (!parcial || dados.preco !== undefined) {
    exigirInteiroPositivo(dados.preco, 'Preco deve ser um inteiro em centavos maior que zero');
  }
  if (dados.estoque !== undefined) exigirInteiroNaoNegativo(dados.estoque, 'Estoque inicial invalido');
  if (dados.estoqueMinimo !== undefined) exigirInteiroNaoNegativo(dados.estoqueMinimo, 'Estoque minimo invalido');
}

/**
 * Cadastra um produto.
 * @param {DatabaseSync} db
 * @param {{sku:string, nome:string, preco:number, estoque?:number, estoqueMinimo?:number}} dados
 */
function criarProduto(db, dados) {
  if (!dados) throw new Error('Dados do produto nao informados');
  validarProduto(dados, false);
  const sku = normalizarSku(dados.sku);
  if (db.prepare('SELECT id FROM produtos WHERE sku = ?').get(sku)) {
    throw new Error('SKU ja cadastrado: ' + sku);
  }
  const estoque = dados.estoque || 0;
  const minimo = dados.estoqueMinimo !== undefined ? dados.estoqueMinimo : 5;
  const quando = agora();

  const id = transacao(db, () => {
    const r = db.prepare(
      'INSERT INTO produtos (sku, nome, preco, estoque, estoque_minimo, ativo, criado_em) VALUES (?, ?, ?, ?, ?, 1, ?)'
    ).run(sku, String(dados.nome).trim(), dados.preco, estoque, minimo, quando);
    const novoId = Number(r.lastInsertRowid);
    if (estoque > 0) {
      db.prepare(
        'INSERT INTO movimentos_estoque (produto_id, tipo, quantidade, motivo, criado_em) VALUES (?, ?, ?, ?, ?)'
      ).run(novoId, 'entrada', estoque, 'estoque inicial', quando);
    }
    return novoId;
  });
  return buscarProduto(db, id);
}

function buscarProduto(db, id) {
  return linha(db.prepare('SELECT * FROM produtos WHERE id = ?').get(Number(id)));
}

function buscarProdutoPorSku(db, sku) {
  return linha(db.prepare('SELECT * FROM produtos WHERE sku = ?').get(normalizarSku(sku)));
}

/**
 * Lista produtos ativos por nome. Com { incluirInativos: true } traz tambem os desativados.
 */
function listarProdutos(db, opcoes) {
  const op = opcoes || {};
  if (op.incluirInativos) {
    return linhas(db.prepare('SELECT * FROM produtos ORDER BY nome, id').all());
  }
  return linhas(db.prepare('SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome, id').all());
}

/**
 * Busca produtos ativos pelo nome ou pelo SKU.
 */
function buscarProdutos(db, termo) {
  const t = String(termo || '').trim();
  if (!t) return listarProdutos(db);
  const like = '%' + t + '%';
  return linhas(db.prepare(
    'SELECT * FROM produtos WHERE ativo = 1 AND (nome LIKE ? OR sku LIKE ?) ORDER BY nome, id'
  ).all(like, like));
}

/**
 * Atualiza nome, preco, sku ou estoque minimo. Estoque nao muda por aqui.
 */
function atualizarProduto(db, id, dados) {
  const atual = buscarProduto(db, id);
  if (!atual) throw new Error('Produto nao encontrado');
  dados = dados || {};
  if (dados.estoque !== undefined) {
    throw new Error('Use entrada ou saida de estoque para alterar a quantidade');
  }
  validarProduto(dados, true);
  const sku = dados.sku !== undefined ? normalizarSku(dados.sku) : atual.sku;
  if (sku !== atual.sku) {
    const outro = db.prepare('SELECT id FROM produtos WHERE sku = ? AND id <> ?').get(sku, atual.id);
    if (outro) throw new Error('SKU ja cadastrado: ' + sku);
  }
  const nome = dados.nome !== undefined ? String(dados.nome).trim() : atual.nome;
  const preco = dados.preco !== undefined ? dados.preco : atual.preco;
  const minimo = dados.estoqueMinimo !== undefined ? dados.estoqueMinimo : atual.estoque_minimo;
  db.prepare('UPDATE produtos SET sku = ?, nome = ?, preco = ?, estoque_minimo = ? WHERE id = ?')
    .run(sku, nome, preco, minimo, atual.id);
  return buscarProduto(db, atual.id);
}

/**
 * Desativa o produto. Nao apagamos para nao perder o historico de pedidos.
 */
function removerProduto(db, id) {
  const atual = buscarProduto(db, id);
  if (!atual) throw new Error('Produto nao encontrado');
  db.prepare('UPDATE produtos SET ativo = 0 WHERE id = ?').run(atual.id);
  return true;
}

/**
 * Reajusta o preco dos produtos ativos por um percentual (ex.: 5 = +5%).
 * Arredonda para o centavo.
 */
function reajustarPrecos(db, pct) {
  if (typeof pct !== 'number' || !isFinite(pct) || pct <= -100) {
    throw new Error('Percentual invalido');
  }
  const prods = db.prepare('SELECT id, preco FROM produtos WHERE ativo = 1').all();
  const upd = db.prepare('UPDATE produtos SET preco = ? WHERE id = ?');
  transacao(db, () => {
    for (const p of prods) {
      const novo = Math.max(1, Math.round(p.preco * (100 + pct) / 100));
      upd.run(novo, p.id);
    }
  });
  return prods.length;
}

module.exports = {
  criarProduto,
  buscarProduto,
  buscarProdutoPorSku,
  listarProdutos,
  buscarProdutos,
  atualizarProduto,
  removerProduto,
  reajustarPrecos,
  normalizarSku,
};
