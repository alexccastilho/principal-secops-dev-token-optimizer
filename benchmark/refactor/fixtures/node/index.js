'use strict';

// Ponto de entrada da biblioteca da Loja do Bairro.
// Tudo que o resto do sistema (CLI, scripts do caixa) usa sai daqui.

const db = require('./src/db');
const clientes = require('./src/clientes');
const produtos = require('./src/produtos');
const estoque = require('./src/estoque');
const pedidos = require('./src/pedidos');
const { calcularOrcamento } = require('./src/orcamento');
const usuarios = require('./src/usuarios');
const autenticacao = require('./src/autenticacao');
const relatorios = require('./src/relatorios');
const dinheiro = require('./src/util/dinheiro');
const datas = require('./src/util/datas');
const documentos = require('./src/util/documentos');

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
  exportarClientesCSV: relatorios.exportarClientesCSV,
  exportarPedidosCSV: relatorios.exportarPedidosCSV,

  // utilitarios
  formatarMoeda: dinheiro.formatarMoeda,
  converterMoeda: dinheiro.converterMoeda,
  formatarData: datas.formatarData,
  converterDataBR: datas.converterDataBR,
  formatarCPF: documentos.formatarCPF,
  formatarCNPJ: documentos.formatarCNPJ,
  formatarCEP: documentos.formatarCEP,
  validarCPF: documentos.validarCPF,
  validarCNPJ: documentos.validarCNPJ,
  validarEmail: documentos.validarEmail,
};
