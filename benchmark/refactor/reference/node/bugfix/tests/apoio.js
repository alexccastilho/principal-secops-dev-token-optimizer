'use strict';

// Funcoes de apoio para os testes: banco em memoria ja com um admin, um vendedor,
// um cliente e alguns produtos.

const loja = require('../index');

function bancoNovo() {
  return loja.abrirBanco(':memory:');
}

function bancoComDados() {
  const db = bancoNovo();
  const admin = loja.criarUsuario(db, { login: 'dona.rosa', nome: 'Rosa', senha: 'girassol', papel: 'admin' });
  const vendedor = loja.criarUsuario(db, { login: 'carlos', nome: 'Carlos', senha: 'balcao', papel: 'vendedor' });
  const cliente = loja.criarCliente(db, {
    nome: 'Maria Aparecida',
    cpf: '529.982.247-25',
    email: 'maria@exemplo.com.br',
    telefone: '11987654321',
  });
  const arroz = loja.criarProduto(db, { sku: 'ARROZ5', nome: 'Arroz 5kg', preco: 2500, estoque: 50 });
  const feijao = loja.criarProduto(db, { sku: 'FEIJAO1', nome: 'Feijao 1kg', preco: 899, estoque: 40 });
  const cafe = loja.criarProduto(db, { sku: 'CAFE500', nome: 'Cafe 500g', preco: 1800, estoque: 3, estoqueMinimo: 5 });
  return { db, admin, vendedor, cliente, arroz, feijao, cafe };
}

module.exports = { loja, bancoNovo, bancoComDados };
