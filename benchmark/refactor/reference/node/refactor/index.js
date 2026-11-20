'use strict';

// Ponto de entrada da biblioteca da Loja do Bairro.
// Tudo que o resto do sistema (CLI, scripts do caixa) usa sai daqui.

const db = require('./src/infra/banco');
const clientes = require('./src/cadastro/clientes');
const produtos = require('./src/cadastro/produtos');
const estoque = require('./src/estoque/movimentos');
const pedidos = require('./src/vendas/pedidos');
const { calcularOrcamento } = require('./src/vendas/orcamento');
const usuarios = require('./src/acesso/usuarios');
const autenticacao = require('./src/acesso/sessoes');
const relatorios = require('./src/relatorios/vendas');
const exportacao = require('./src/relatorios/exportacao');
const dinheiro = require('./src/comum/moeda');
const datas = require('./src/comum/datas');
const documentos = require('./src/comum/documentos');
const validacao = require('./src/comum/validacao');

module.exports = {
  // banco
  abrirBanco: db.abrirBanco,
  fecharBanco: db.fecharBanco,

  // clientes
  criarCliente: clientes.criarCliente,
  buscarCliente: clientes.buscarCliente,
  listarClientes: clientes.listarClientes,
  buscarClientesPorNome: clientes.buscarClientesPorNome,
  atualizarCliente: clientes.atualizarCliente,
  removerCliente: clientes.removerCliente,
  formatarTelefone: clientes.formatarTelefone,

  // produtos e estoque
  criarProduto: produtos.criarProduto,
  buscarProduto: produtos.buscarProduto,
  listarProdutos: produtos.listarProdutos,
  atualizarProduto: produtos.atualizarProduto,
  removerProduto: produtos.removerProduto,
  registrarEntrada: estoque.registrarEntrada,
  registrarSaida: estoque.registrarSaida,
  listarMovimentos: estoque.listarMovimentos,
  listarEstoqueBaixo: estoque.listarEstoqueBaixo,

  // pedidos
  criarPedido: pedidos.criarPedido,
  buscarPedido: pedidos.buscarPedido,
  listarPedidos: pedidos.listarPedidos,
  registrarPagamento: pedidos.registrarPagamento,
  cancelarPedido: pedidos.cancelarPedido,
  calcularOrcamento: calcularOrcamento,

  // usuarios e login
  criarUsuario: usuarios.criarUsuario,
  listarUsuarios: usuarios.listarUsuarios,
  alterarSenha: usuarios.alterarSenha,
  login: autenticacao.login,
  validarSessao: autenticacao.validarSessao,
  encerrarSessao: autenticacao.encerrarSessao,

  // relatorios
  vendasPorPeriodo: relatorios.vendasPorPeriodo,
  produtosMaisVendidos: relatorios.produtosMaisVendidos,
  relatorioPedidos: relatorios.relatorioPedidos,
  exportarClientesCSV: exportacao.exportarClientesCSV,
  exportarPedidosCSV: exportacao.exportarPedidosCSV,

  // utilitarios
  formatarMoeda: dinheiro.formatarMoeda,
  converterMoeda: dinheiro.converterMoeda,
  formatarData: datas.formatarData,
  converterDataBR: datas.converterDataBR,
  formatarCPF: documentos.formatarCPF,
  formatarCNPJ: documentos.formatarCNPJ,
  formatarCEP: documentos.formatarCEP,
  validarCPF: validacao.validarCPF,
  validarCNPJ: validacao.validarCNPJ,
  validarEmail: validacao.validarEmail,
};
