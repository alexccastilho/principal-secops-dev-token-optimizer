#!/usr/bin/env node
'use strict';

// Linha de comando da loja. Uso:
//   node cli.js [--db arquivo.db] <comando> [argumentos]
// Sem --db usa a variavel LOJA_DB ou o arquivo loja.db na pasta atual.

const loja = require('./index');
const { buscarClientePorCPF, clienteParaExibicao, clientesSemCompra } = require('./src/cadastro/clientes');
const { buscarProdutoPorSku, buscarProdutos, reajustarPrecos } = require('./src/cadastro/produtos');
const { ajustarEstoque, valorEmEstoque, sugestaoCompra } = require('./src/estoque/movimentos');
const { pedidosDoCliente, pedidosEmAbertoAntigos } = require('./src/vendas/pedidos');
const { gerarRecibo } = require('./src/vendas/recibo');
const { desativarUsuario, redefinirSenha } = require('./src/acesso/usuarios');
const { sessoesAtivas } = require('./src/acesso/sessoes');
const { ticketMedio, vendasPorVendedor, resumoMensal, curvaABC } = require('./src/relatorios/vendas');
const { parcelar } = require('./src/comum/moeda');

const AJUDA = [
  'Uso: node cli.js [--db arquivo.db] <comando> [argumentos]',
  '',
  'Clientes:',
  '  cliente:novo <nome> <cpf> [email] [telefone]  cadastra cliente',
  '  cliente:ver <id ou cpf>                       ficha do cliente',
  '  cliente:editar <id> <campo> <valor>           altera nome, email, telefone, cep ou observacao',
  '  clientes [busca]                              lista clientes (ou busca por nome)',
  '  clientes:inativos [dias]                      sem compra ha mais de N dias (padrao 90)',
  'Produtos e estoque:',
  '  produto:novo <sku> <nome> <preco> [estoque]   cadastra produto (preco em reais, ex. 12,50)',
  '  produto:preco <produtoId> <preco>             altera o preco',
  '  produtos [busca]                              lista produtos ativos (ou busca por nome/sku)',
  '  produtos:reajuste <percentual>                reajusta os precos ativos',
  '  estoque:entrada <produtoId ou sku> <qtd>      entrada de mercadoria',
  '  estoque:ajuste <produtoId> <qtd contada>      ajuste de inventario',
  '  estoque:baixo                                 produtos com estoque baixo',
  '  estoque:valor                                 valor do estoque a preco de venda',
  '  estoque:sugestao [dias]                       sugestao de compra pelas vendas recentes',
  'Usuarios:',
  '  usuario:novo <login> <nome> <senha> <papel>   cria usuario (admin ou vendedor)',
  '  usuario:desativar <usuarioId>                 desativa usuario',
  '  usuario:senha <usuarioId> <senha nova>        redefine a senha',
  '  usuarios                                      lista usuarios',
  'Pedidos:',
  '  pedido:novo <usuarioId> <clienteId> <produtoId:qtd>... [--cupom CODIGO]',
  '  pedido:ver <pedidoId>                         mostra o pedido',
  '  pedido:recibo <pedidoId>                      recibo para impressora termica',
  '  pedido:pagar <pedidoId> <forma>               dinheiro, pix, cartao_credito, cartao_debito',
  '  pedido:cancelar <pedidoId> <usuarioId>        cancela e devolve ao estoque',
  '  pedidos [usuarioId]                           pedidos (de um vendedor ou geral)',
  '  pedidos:pendentes [dias]                      em aberto ha mais de N dias (padrao 7)',
  '  orcamento <produtoId:qtd>... [--cupom CODIGO] [--parcelas N]',
  'Relatorios:',
  '  vendas <inicio> <fim>                         total vendido no periodo (DD/MM/AAAA)',
  '  vendas:vendedores <inicio> <fim>              vendas por vendedor',
  '  resumo:mes <AAAA-MM>                          fechamento do mes',
  '  mais-vendidos [limite]                        produtos mais vendidos',
  '  relatorio:pedidos [coluna] [asc|desc]         lista de pedidos ordenada',
  '  relatorio:abc                                 curva ABC dos produtos',
  '  exportar:clientes                             CSV dos clientes na saida padrao',
  '  exportar:pedidos                              CSV dos pedidos na saida padrao',
  '  ajuda                                         esta mensagem',
].join('\n');

const OPCOES_COM_VALOR = ['db', 'cupom', 'parcelas'];

function separarOpcoes(argv) {
  const args = [];
  const opcoes = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const eq = a.indexOf('=');
      const nome = eq > 0 ? a.slice(2, eq) : a.slice(2);
      if (OPCOES_COM_VALOR.includes(nome)) {
        if (eq > 0) {
          opcoes[nome] = a.slice(eq + 1);
        } else {
          opcoes[nome] = argv[i + 1];
          i++;
        }
        continue;
      }
    }
    args.push(a);
  }
  return { args, opcoes };
}

function exigirArgs(args, n, uso) {
  if (args.length < n) {
    throw new Error('Argumentos insuficientes. Uso: ' + uso);
  }
}

function inteiro(txt, nome) {
  const n = Number(txt);
  if (!Number.isInteger(n) || n <= 0) {
    throw new Error(nome + ' invalido: ' + txt);
  }
  return n;
}

function lerItens(lista) {
  return lista.map((t) => {
    const [prod, qtd] = t.split(':');
    return { produtoId: inteiro(prod, 'Produto'), quantidade: qtd === undefined ? 1 : inteiro(qtd, 'Quantidade') };
  });
}

function acharUsuario(db, id) {
  const u = loja.listarUsuarios(db).find((x) => x.id === id);
  if (!u) throw new Error('Usuario nao encontrado: ' + id);
  return u;
}

function linhaCliente(c) {
  return '#' + c.id + ' | ' + c.nome + ' | ' + c.cpf + ' | ' + (c.email || '-') + ' | ' +
    (c.telefone ? loja.formatarTelefone(c.telefone) : '-');
}

function linhaProduto(p) {
  return '#' + p.id + ' | ' + p.sku + ' | ' + p.nome + ' | ' + loja.formatarMoeda(p.preco) + ' | estoque ' + p.estoque;
}

function linhaPedido(p) {
  return '#' + p.id + ' | ' + loja.formatarData(p.criado_em) + ' | cliente ' + p.cliente_id +
    ' | ' + p.status + ' | ' + loja.formatarMoeda(p.total);
}

function imprimirPedido(out, ped) {
  out.push('Pedido #' + ped.id + ' - ' + loja.formatarData(ped.criado_em) + ' - ' + ped.status);
  for (const it of ped.itens) {
    out.push('  ' + it.quantidade + ' x ' + it.sku + ' ' + it.nome + ' ' +
      loja.formatarMoeda(it.preco_unitario) + ' = ' + loja.formatarMoeda(it.total));
  }
  out.push('Subtotal: ' + loja.formatarMoeda(ped.subtotal));
  out.push('Desconto: ' + loja.formatarMoeda(ped.desconto));
  out.push('Total: ' + loja.formatarMoeda(ped.total));
}

// a CLI roda na maquina do escritorio, com acesso de administrador
const ADMIN_LOCAL = { id: 0, login: 'cli', papel: 'admin' };

/**
 * Executa um comando e devolve as linhas de saida.
 * Separado do main para facilitar o teste.
 */
function executar(db, cmd, args, opcoes) {
  const out = [];
  switch (cmd) {
    case 'init':
      out.push('Banco pronto.');
      break;

    // ---- clientes ----
    case 'cliente:novo': {
      exigirArgs(args, 2, 'cliente:novo <nome> <cpf> [email] [telefone]');
      const c = loja.criarCliente(db, { nome: args[0], cpf: args[1], email: args[2], telefone: args[3] });
      out.push('Cliente #' + c.id + ' cadastrado: ' + c.nome);
      break;
    }

    case 'cliente:ver': {
      exigirArgs(args, 1, 'cliente:ver <id ou cpf>');
      const chave = args[0];
      const c = chave.replace(/\D/g, '').length === 11 ? buscarClientePorCPF(db, chave) : loja.buscarCliente(db, inteiro(chave, 'Cliente'));
      if (!c) throw new Error('Cliente nao encontrado');
      const f = clienteParaExibicao(c);
      const peds = pedidosDoCliente(db, c.id).filter((p) => p.status !== 'cancelado');
      out.push('Cliente #' + f.id + ': ' + f.nome);
      out.push('CPF: ' + f.cpf);
      out.push('E-mail: ' + (f.email || '-'));
      out.push('Telefone: ' + (f.telefone || '-'));
      out.push('CEP: ' + (f.cep ? f.cep + (f.uf ? ' (' + f.uf + ')' : '') : '-'));
      if (f.observacao) out.push('Obs.: ' + f.observacao);
      out.push('Pedidos: ' + peds.length + (peds.length ? ' (ultimo em ' + loja.formatarData(peds[0].criado_em) + ')' : ''));
      break;
    }

    case 'cliente:editar': {
      exigirArgs(args, 3, 'cliente:editar <id> <campo> <valor>');
      const campos = ['nome', 'email', 'telefone', 'cep', 'observacao'];
      if (!campos.includes(args[1])) {
        throw new Error('Campo invalido: ' + args[1] + ' (use ' + campos.join(', ') + ')');
      }
      const dados = {};
      dados[args[1]] = args[2];
      const c = loja.atualizarCliente(db, inteiro(args[0], 'Cliente'), dados);
      out.push('Cliente #' + c.id + ' atualizado.');
      break;
    }

    case 'clientes:inativos': {
      const dias = args[0] ? inteiro(args[0], 'Dias') : 90;
      const lista = clientesSemCompra(db, dias);
      if (lista.length === 0) out.push('Nenhum cliente inativo.');
      for (const c of lista) {
        out.push(linhaCliente(c) + ' | ultima compra: ' + (c.ultima_compra ? loja.formatarData(c.ultima_compra) : 'nunca'));
      }
      break;
    }

    case 'clientes': {
      const lista = args[0] ? loja.buscarClientesPorNome(db, args[0]) : loja.listarClientes(db);
      if (lista.length === 0) {
        out.push('Nenhum cliente encontrado.');
      }
      for (const c of lista) out.push(linhaCliente(c));
      break;
    }

    // ---- produtos e estoque ----
    case 'produto:novo': {
      exigirArgs(args, 3, 'produto:novo <sku> <nome> <preco> [estoque]');
      const p = loja.criarProduto(db, {
        sku: args[0],
        nome: args[1],
        preco: loja.converterMoeda(args[2]),
        estoque: args[3] !== undefined ? Number(args[3]) : 0,
      });
      out.push('Produto #' + p.id + ' cadastrado: ' + p.sku + ' ' + p.nome + ' ' + loja.formatarMoeda(p.preco));
      break;
    }

    case 'produto:preco': {
      exigirArgs(args, 2, 'produto:preco <produtoId> <preco>');
      const p = loja.atualizarProduto(db, inteiro(args[0], 'Produto'), { preco: loja.converterMoeda(args[1]) });
      out.push('Preco de ' + p.sku + ': ' + loja.formatarMoeda(p.preco));
      break;
    }

    case 'produtos': {
      const lista = args[0] ? buscarProdutos(db, args[0]) : loja.listarProdutos(db);
      if (lista.length === 0) out.push(args[0] ? 'Nenhum produto encontrado.' : 'Nenhum produto cadastrado.');
      for (const p of lista) out.push(linhaProduto(p));
      break;
    }

    case 'produtos:reajuste': {
      exigirArgs(args, 1, 'produtos:reajuste <percentual>');
      const pct = Number(String(args[0]).replace(',', '.'));
      const n = reajustarPrecos(db, pct);
      out.push(n + ' produto(s) reajustado(s) em ' + args[0] + '%.');
      break;
    }

    case 'estoque:entrada': {
      exigirArgs(args, 2, 'estoque:entrada <produtoId ou sku> <quantidade>');
      let id;
      if (/^\d+$/.test(args[0])) {
        id = inteiro(args[0], 'Produto');
      } else {
        const prod = buscarProdutoPorSku(db, args[0]);
        if (!prod) throw new Error('Produto nao encontrado: ' + args[0]);
        id = prod.id;
      }
      const p = loja.registrarEntrada(db, id, inteiro(args[1], 'Quantidade'));
      out.push('Estoque de ' + p.sku + ': ' + p.estoque);
      break;
    }

    case 'estoque:ajuste': {
      exigirArgs(args, 2, 'estoque:ajuste <produtoId> <quantidade contada>');
      const p = ajustarEstoque(db, inteiro(args[0], 'Produto'), Number(args[1]));
      out.push('Estoque de ' + p.sku + ': ' + p.estoque);
      break;
    }

    case 'estoque:baixo': {
      const lista = loja.listarEstoqueBaixo(db);
      if (lista.length === 0) out.push('Nenhum produto com estoque baixo.');
      for (const p of lista) out.push(linhaProduto(p));
      break;
    }

    case 'estoque:valor':
      out.push('Valor em estoque: ' + loja.formatarMoeda(valorEmEstoque(db)));
      break;

    case 'estoque:sugestao': {
      const dias = args[0] ? inteiro(args[0], 'Dias') : 30;
      const lista = sugestaoCompra(db, dias);
      if (lista.length === 0) out.push('Nada para comprar.');
      for (const s of lista) {
        out.push(s.sku + ' | ' + s.nome + ' | estoque ' + s.estoque + ' | vendido ' + s.vendido + ' | comprar ' + s.comprar);
      }
      break;
    }

    // ---- usuarios ----
    case 'usuario:novo': {
      exigirArgs(args, 4, 'usuario:novo <login> <nome> <senha> <papel>');
      const u = loja.criarUsuario(db, { login: args[0], nome: args[1], senha: args[2], papel: args[3] });
      out.push('Usuario ' + u.login + ' criado (' + u.papel + ').');
      break;
    }

    case 'usuario:desativar': {
      exigirArgs(args, 1, 'usuario:desativar <usuarioId>');
      const u = acharUsuario(db, inteiro(args[0], 'Usuario'));
      desativarUsuario(db, u.id);
      out.push('Usuario ' + u.login + ' desativado.');
      break;
    }

    case 'usuario:senha': {
      exigirArgs(args, 2, 'usuario:senha <usuarioId> <senha nova>');
      const u = acharUsuario(db, inteiro(args[0], 'Usuario'));
      redefinirSenha(db, u.id, args[1]);
      out.push('Senha de ' + u.login + ' redefinida.');
      break;
    }

    case 'usuarios':
      for (const u of loja.listarUsuarios(db)) {
        const n = sessoesAtivas(db, u.id);
        out.push('#' + u.id + ' | ' + u.login + ' | ' + u.nome + ' | ' + u.papel +
          (u.ativo ? '' : ' | inativo') + (n ? ' | ' + n + ' sessao(oes)' : ''));
      }
      break;

    // ---- pedidos ----
    case 'pedido:novo': {
      exigirArgs(args, 3, 'pedido:novo <usuarioId> <clienteId> <produtoId:qtd>... [--cupom CODIGO]');
      const ped = loja.criarPedido(db, {
        usuarioId: inteiro(args[0], 'Usuario'),
        clienteId: inteiro(args[1], 'Cliente'),
        itens: lerItens(args.slice(2)),
        cupom: opcoes.cupom,
      });
      out.push('Pedido #' + ped.id + ' criado. Subtotal: ' + loja.formatarMoeda(ped.subtotal) +
        ' | Desconto: ' + loja.formatarMoeda(ped.desconto) + ' | Total: ' + loja.formatarMoeda(ped.total));
      break;
    }

    case 'pedido:ver': {
      exigirArgs(args, 1, 'pedido:ver <pedidoId>');
      const ped = loja.buscarPedido(db, inteiro(args[0], 'Pedido'), ADMIN_LOCAL);
      if (!ped) throw new Error('Pedido nao encontrado');
      imprimirPedido(out, ped);
      break;
    }

    case 'pedido:recibo':
      exigirArgs(args, 1, 'pedido:recibo <pedidoId>');
      out.push(gerarRecibo(db, inteiro(args[0], 'Pedido')));
      break;

    case 'pedido:pagar': {
      exigirArgs(args, 2, 'pedido:pagar <pedidoId> <forma>');
      const ped = loja.registrarPagamento(db, inteiro(args[0], 'Pedido'), args[1]);
      out.push('Pedido #' + ped.id + ' pago (' + ped.forma_pagamento + ').');
      break;
    }

    case 'pedido:cancelar': {
      exigirArgs(args, 2, 'pedido:cancelar <pedidoId> <usuarioId>');
      const usuario = acharUsuario(db, inteiro(args[1], 'Usuario'));
      const ped = loja.cancelarPedido(db, inteiro(args[0], 'Pedido'), usuario);
      out.push('Pedido #' + ped.id + ' cancelado.');
      break;
    }

    case 'pedidos': {
      const usuario = args[0] ? acharUsuario(db, inteiro(args[0], 'Usuario')) : ADMIN_LOCAL;
      const lista = loja.listarPedidos(db, usuario);
      if (lista.length === 0) out.push('Nenhum pedido.');
      for (const p of lista) out.push(linhaPedido(p));
      break;
    }

    case 'pedidos:pendentes': {
      const dias = args[0] ? inteiro(args[0], 'Dias') : 7;
      const lista = pedidosEmAbertoAntigos(db, dias);
      if (lista.length === 0) out.push('Nenhum pedido pendente ha mais de ' + dias + ' dias.');
      for (const p of lista) out.push(linhaPedido(p));
      break;
    }

    case 'orcamento': {
      exigirArgs(args, 1, 'orcamento <produtoId:qtd>... [--cupom CODIGO] [--parcelas N]');
      const orc = loja.calcularOrcamento(db, lerItens(args), opcoes.cupom);
      for (const it of orc.itens) {
        out.push('  ' + it.quantidade + ' x ' + it.sku + ' ' + it.nome + ' = ' + loja.formatarMoeda(it.total));
      }
      out.push('Subtotal: ' + loja.formatarMoeda(orc.subtotal));
      out.push('Desconto: ' + loja.formatarMoeda(orc.desconto));
      out.push('Total: ' + loja.formatarMoeda(orc.total));
      if (opcoes.parcelas) {
        const parc = parcelar(orc.total, inteiro(opcoes.parcelas, 'Parcelas'));
        out.push('Em ' + parc.length + 'x: ' + parc.map((v) => loja.formatarMoeda(v)).join(' + '));
      }
      break;
    }

    // ---- relatorios ----
    case 'vendas': {
      exigirArgs(args, 2, 'vendas <inicio> <fim>');
      const v = loja.vendasPorPeriodo(db, args[0], args[1]);
      out.push('Periodo: ' + loja.formatarData(v.inicio) + ' a ' + loja.formatarData(v.fim));
      out.push('Pedidos: ' + v.quantidade);
      out.push('Descontos: ' + loja.formatarMoeda(v.desconto));
      out.push('Total: ' + loja.formatarMoeda(v.total));
      out.push('Ticket medio: ' + loja.formatarMoeda(ticketMedio(db, args[0], args[1])));
      break;
    }

    case 'vendas:vendedores': {
      exigirArgs(args, 2, 'vendas:vendedores <inicio> <fim>');
      for (const r of vendasPorVendedor(db, args[0], args[1])) {
        out.push(r.login + ' | ' + r.quantidade + ' pedido(s) | ' + loja.formatarMoeda(r.total));
      }
      break;
    }

    case 'resumo:mes': {
      exigirArgs(args, 1, 'resumo:mes <AAAA-MM>');
      const m = /^(\d{4})-(\d{1,2})$/.exec(args[0]);
      if (!m) throw new Error('Mes invalido: ' + args[0]);
      const r = resumoMensal(db, m[1], m[2]);
      out.push('Resumo de ' + r.mes);
      out.push('Pedidos: ' + r.quantidade + ' | Total: ' + loja.formatarMoeda(r.total));
      out.push('Ticket medio: ' + loja.formatarMoeda(r.ticketMedio));
      out.push('Media por dia aberto (' + r.diasAbertos + ' dias): ' + loja.formatarMoeda(r.mediaPorDia));
      out.push('Cancelados: ' + r.cancelados + ' (' + loja.formatarMoeda(r.totalCancelado) + ')');
      out.push('Mais vendido: ' + (r.campeao || '-'));
      break;
    }

    case 'mais-vendidos': {
      const lim = args[0] ? inteiro(args[0], 'Limite') : 10;
      const lista = loja.produtosMaisVendidos(db, { limite: lim });
      if (lista.length === 0) out.push('Nenhuma venda registrada.');
      lista.forEach((p, i) => {
        out.push((i + 1) + '. ' + p.sku + ' ' + p.nome + ' | ' + p.quantidade + ' un. | ' + loja.formatarMoeda(p.total));
      });
      break;
    }

    case 'relatorio:pedidos': {
      const lista = loja.relatorioPedidos(db, args[0], args[1]);
      for (const p of lista) {
        out.push('#' + p.id + ' | ' + loja.formatarData(p.criado_em) + ' | ' + p.cliente + ' | ' + p.vendedor +
          ' | ' + p.status + ' | ' + loja.formatarMoeda(p.total));
      }
      break;
    }

    case 'relatorio:abc': {
      const lista = curvaABC(db);
      if (lista.length === 0) out.push('Nenhuma venda registrada.');
      for (const p of lista) {
        out.push(p.classe + ' | ' + p.sku + ' | ' + p.nome + ' | ' + loja.formatarMoeda(p.total) + ' | ' +
          String(p.acumulado).replace('.', ',') + '%');
      }
      break;
    }

    case 'exportar:clientes':
      out.push(loja.exportarClientesCSV(db, { bom: false }).replace(/\r\n$/, ''));
      break;

    case 'exportar:pedidos':
      out.push(loja.exportarPedidosCSV(db, { bom: false }).replace(/\r\n$/, ''));
      break;

    default:
      throw new Error('Comando desconhecido: ' + cmd + '. Use "ajuda".');
  }
  return out;
}

function main(argv) {
  const { args, opcoes } = separarOpcoes(argv);
  const cmd = args.shift();
  if (cmd === 'ajuda' || cmd === undefined || cmd === '--help' || cmd === '-h') {
    process.stdout.write(AJUDA + '\n');
    return 0;
  }
  const caminho = opcoes.db || process.env.LOJA_DB || 'loja.db';
  let db;
  try {
    db = loja.abrirBanco(caminho);
    const linhas = executar(db, cmd, args, opcoes);
    process.stdout.write(linhas.join('\n') + '\n');
    return 0;
  } catch (e) {
    process.stderr.write('Erro: ' + e.message + '\n');
    return 1;
  } finally {
    loja.fecharBanco(db);
  }
}

if (require.main === module) {
  process.exitCode = main(process.argv.slice(2));
}

module.exports = { executar, main };
