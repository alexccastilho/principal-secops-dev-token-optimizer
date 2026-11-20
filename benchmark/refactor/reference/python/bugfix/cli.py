"""Linha de comando da Loja do Bairro.

Exemplos:
    python cli.py --db loja.db init
    python cli.py usuario-add ana --senha segredo1 --papel admin
    python cli.py cliente-add --nome "Maria Souza" --cpf 52998224725 --email maria@email.com
    python cli.py produto-add --codigo CAF-500 --nome "Café 500g" --preco 18,90 --estoque 40
    python cli.py pedido-add --usuario ana --senha segredo1 --cliente 1 --item 1:2
"""
import argparse
import os
import sys

import loja


def _conn(args):
    return loja.conectar(args.db)


def _logar(conn, args):
    token = loja.fazer_login(conn, args.usuario, args.senha)
    if token is None:
        raise ValueError("usuario ou senha invalidos")
    return token, loja.usuario_da_sessao(conn, token)


def _item(texto):
    try:
        produto, quantidade = texto.split(":")
        return {"produto_id": int(produto), "quantidade": int(quantidade)}
    except ValueError:
        raise argparse.ArgumentTypeError("item deve ser PRODUTO:QUANTIDADE, ex.: 3:2")


def cmd_init(args):
    conn = _conn(args)
    conn.close()
    print("Banco pronto: %s" % args.db)


def cmd_usuario_add(args):
    conn = _conn(args)
    usuario_id = loja.criar_usuario(conn, args.login, args.senha, args.papel, args.nome or "")
    print("Usuario %s criado (id %d, papel %s)" % (args.login.lower(), usuario_id, args.papel))


def cmd_cliente_add(args):
    conn = _conn(args)
    cliente_id = loja.cadastrar_cliente(
        conn, args.nome, args.cpf, args.email, args.telefone or "", args.cep or ""
    )
    print("Cliente cadastrado: %d" % cliente_id)


def cmd_clientes(args):
    conn = _conn(args)
    if args.busca:
        clientes = loja.buscar_clientes_por_nome(conn, args.busca)
    else:
        clientes = loja.listar_clientes(conn)
    if not clientes:
        print("Nenhum cliente encontrado.")
        return
    for c in clientes:
        print("%d | %s | %s | %s" % (c["id"], c["nome"], loja.formatar_cpf(c["cpf"]), c["email"]))


def cmd_produto_add(args):
    conn = _conn(args)
    preco = loja.converter_moeda(args.preco)
    produto_id = loja.cadastrar_produto(
        conn, args.codigo, args.nome, preco, args.estoque, args.minimo
    )
    print("Produto cadastrado: %d" % produto_id)


def cmd_produtos(args):
    conn = _conn(args)
    produtos = loja.listar_produtos(conn, apenas_ativos=not args.incluir_inativos)
    if not produtos:
        print("Nenhum produto cadastrado.")
        return
    for p in produtos:
        print("%d | %s | %s | %s | estoque %d" % (
            p["id"], p["codigo"], p["nome"], loja.formatar_moeda(p["preco"]), p["estoque"]))


def cmd_entrada(args):
    conn = _conn(args)
    saldo = loja.registrar_entrada(conn, args.produto, args.quantidade, args.motivo)
    produto = loja.buscar_produto(conn, args.produto)
    print("Estoque de %s: %d" % (produto["codigo"], saldo))


def cmd_estoque_baixo(args):
    conn = _conn(args)
    produtos = loja.produtos_estoque_baixo(conn)
    if not produtos:
        print("Nenhum produto com estoque baixo.")
        return
    for p in produtos:
        print("%s | %s | estoque %d (minimo %d)" % (
            p["codigo"], p["nome"], p["estoque"], p["estoque_minimo"]))


def cmd_pedido_add(args):
    conn = _conn(args)
    token, usuario = _logar(conn, args)
    try:
        pedido_id = loja.criar_pedido(conn, args.cliente, args.item, usuario["id"], args.cupom)
        pedido = loja.buscar_pedido(conn, pedido_id, usuario)
    finally:
        loja.encerrar_sessao(conn, token)
    print("Pedido %d criado: total %s" % (pedido_id, loja.formatar_moeda(pedido["total"])))


def cmd_pedido_ver(args):
    conn = _conn(args)
    token, usuario = _logar(conn, args)
    try:
        pedido = loja.buscar_pedido(conn, args.pedido, usuario)
    finally:
        loja.encerrar_sessao(conn, token)
    if pedido is None:
        raise ValueError("pedido %d nao encontrado" % args.pedido)
    print("Pedido %d - %s" % (pedido["id"], pedido["status"]))
    for item in pedido["itens"]:
        print("  %d x %s (%s) = %s" % (
            item["quantidade"], item["nome"],
            loja.formatar_moeda(item["preco_unitario"]), loja.formatar_moeda(item["total"])))
    print("Subtotal: %s" % loja.formatar_moeda(pedido["subtotal"]))
    print("Desconto: %s" % loja.formatar_moeda(pedido["desconto"]))
    print("Total: %s" % loja.formatar_moeda(pedido["total"]))


def cmd_pedidos(args):
    conn = _conn(args)
    token, usuario = _logar(conn, args)
    try:
        pedidos = loja.listar_pedidos(conn, usuario, args.status)
    finally:
        loja.encerrar_sessao(conn, token)
    if not pedidos:
        print("Nenhum pedido.")
        return
    for p in pedidos:
        print("%d | %s | %s" % (p["id"], p["status"], loja.formatar_moeda(p["total"])))


def cmd_pedido_cancelar(args):
    conn = _conn(args)
    token, usuario = _logar(conn, args)
    try:
        loja.cancelar_pedido(conn, args.pedido, usuario)
    finally:
        loja.encerrar_sessao(conn, token)
    print("Pedido %d cancelado." % args.pedido)


def cmd_pagar(args):
    conn = _conn(args)
    loja.registrar_pagamento(conn, args.pedido, args.forma)
    print("Pedido %d pago (%s)." % (args.pedido, args.forma.lower()))


def cmd_vendas(args):
    conn = _conn(args)
    r = loja.vendas_por_periodo(conn, args.inicio, args.fim)
    print("Pedidos: %d" % r["quantidade_pedidos"])
    print("Total: %s" % loja.formatar_moeda(r["total"]))


def cmd_resumo(args):
    conn = _conn(args)
    r = loja.resumo_do_dia(conn, args.data)
    print("Resumo de %s" % loja.formatar_data(r["data"]))
    print("Pedidos: %d (cancelados: %d)" % (r["pedidos"], r["cancelados"]))
    print("Total: %s" % loja.formatar_moeda(r["total"]))
    print("Ticket medio: %s" % loja.formatar_moeda(r["ticket_medio"]))
    for forma in sorted(r["pagamentos"]):
        print("  %s: %s" % (forma, loja.formatar_moeda(r["pagamentos"][forma])))


def cmd_exportar_clientes(args):
    conn = _conn(args)
    n = loja.exportar_clientes_csv(conn, args.arquivo)
    print("%d cliente(s) exportado(s) para %s" % (n, args.arquivo))


def cmd_importar_clientes(args):
    conn = _conn(args)
    r = loja.importar_clientes_csv(conn, args.arquivo)
    print("Importados: %d | Ignorados: %d | Erros: %d" % (
        r["importados"], r["ignorados"], len(r["erros"])))
    for erro in r["erros"]:
        print("  " + erro)


def cmd_fornecedor_add(args):
    conn = _conn(args)
    fornecedor_id = loja.cadastrar_fornecedor(
        conn, args.nome, args.cnpj, args.email or "", args.telefone or "", args.prazo)
    print("Fornecedor cadastrado: %d" % fornecedor_id)


def cmd_fornecedores(args):
    conn = _conn(args)
    fornecedores = loja.listar_fornecedores(conn)
    if not fornecedores:
        print("Nenhum fornecedor cadastrado.")
        return
    for f in fornecedores:
        print("%d | %s | %s | prazo %d dia(s)" % (
            f["id"], f["nome"], loja.formatar_cnpj(f["cnpj"]), f["prazo_entrega_dias"]))


def cmd_caixa_abrir(args):
    conn = _conn(args)
    token, usuario = _logar(conn, args)
    try:
        caixa_id = loja.abrir_caixa(conn, usuario["id"], loja.converter_moeda(args.troco))
    finally:
        loja.encerrar_sessao(conn, token)
    print("Caixa %d aberto com %s" % (caixa_id, loja.formatar_moeda(loja.converter_moeda(args.troco))))


def cmd_caixa_fechar(args):
    conn = _conn(args)
    token, usuario = _logar(conn, args)
    try:
        r = loja.fechar_caixa(conn, loja.converter_moeda(args.contado))
    finally:
        loja.encerrar_sessao(conn, token)
    print("Caixa %d fechado" % r["caixa_id"])
    print("Esperado em dinheiro: %s" % loja.formatar_moeda(r["esperado_em_dinheiro"]))
    print("Contado: %s" % loja.formatar_moeda(r["valor_contado"]))
    print("Diferenca: %s" % loja.formatar_moeda(r["diferenca"]))


def cmd_recibo(args):
    conn = _conn(args)
    sys.stdout.write(loja.gerar_recibo(conn, args.pedido))


def cmd_mais_vendidos(args):
    conn = _conn(args)
    produtos = loja.produtos_mais_vendidos(conn, args.limite)
    if not produtos:
        print("Nenhuma venda registrada.")
        return
    for posicao, p in enumerate(produtos, start=1):
        print("%d. %s | %d un. | %s" % (
            posicao, p["nome"], p["quantidade"], loja.formatar_moeda(p["total"])))


def cmd_entrega(args):
    conn = _conn(args)
    data = args.data or loja.proxima_data_livre(conn)
    entrega_id = loja.agendar_entrega(conn, args.pedido, args.cep, data, args.endereco or "")
    print("Entrega %d agendada para %s" % (entrega_id, loja.formatar_data(loja.converter_data(data))))


def cmd_entregas(args):
    conn = _conn(args)
    entregas = loja.entregas_do_dia(conn, args.data)
    if not entregas:
        print("Nenhuma entrega para o dia.")
        return
    for e in entregas:
        print("%d | pedido %d | %s | %s | %s | %s" % (
            e["id"], e["pedido_id"], e["cliente"], e["cep"], e["endereco"], e["status"]))


def cmd_backup(args):
    conn = _conn(args)
    destino = loja.fazer_backup(conn, args.pasta, args.manter)
    if not loja.verificar_backup(destino):
        raise ValueError("backup gravado mas não passou na verificação: %s" % destino)
    print("Backup gravado em %s" % destino)


def montar_parser():
    p = argparse.ArgumentParser(prog="loja", description="Back office da Loja do Bairro")
    p.add_argument("--db", default=os.environ.get("LOJA_DB", "loja.db"),
                   help="arquivo do banco SQLite (padrão: loja.db ou $LOJA_DB)")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("init", help="cria o banco")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("usuario-add", help="cria usuário")
    s.add_argument("login")
    s.add_argument("--senha", required=True)
    s.add_argument("--papel", default="vendedor", choices=["admin", "vendedor"])
    s.add_argument("--nome")
    s.set_defaults(func=cmd_usuario_add)

    s = sub.add_parser("cliente-add", help="cadastra cliente")
    s.add_argument("--nome", required=True)
    s.add_argument("--cpf", required=True)
    s.add_argument("--email", required=True)
    s.add_argument("--telefone")
    s.add_argument("--cep")
    s.set_defaults(func=cmd_cliente_add)

    s = sub.add_parser("clientes", help="lista clientes")
    s.add_argument("--busca", help="parte do nome")
    s.set_defaults(func=cmd_clientes)

    s = sub.add_parser("produto-add", help="cadastra produto")
    s.add_argument("--codigo", required=True)
    s.add_argument("--nome", required=True)
    s.add_argument("--preco", required=True, help="em reais, ex.: 18,90")
    s.add_argument("--estoque", type=int, default=0)
    s.add_argument("--minimo", type=int, default=None)
    s.set_defaults(func=cmd_produto_add)

    s = sub.add_parser("produtos", help="lista produtos")
    s.add_argument("--inativos", dest="incluir_inativos", action="store_true",
                   help="inclui produtos fora de venda")
    s.set_defaults(func=cmd_produtos)

    s = sub.add_parser("entrada", help="entrada de estoque")
    s.add_argument("produto", type=int)
    s.add_argument("quantidade", type=int)
    s.add_argument("--motivo", default="compra")
    s.set_defaults(func=cmd_entrada)

    s = sub.add_parser("estoque-baixo", help="produtos abaixo do mínimo")
    s.set_defaults(func=cmd_estoque_baixo)

    for nome, func, ajuda in (
        ("pedido-add", cmd_pedido_add, "cria pedido"),
        ("pedido-ver", cmd_pedido_ver, "mostra pedido"),
        ("pedidos", cmd_pedidos, "lista pedidos"),
        ("pedido-cancelar", cmd_pedido_cancelar, "cancela pedido"),
    ):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("--usuario", required=True)
        s.add_argument("--senha", required=True)
        if nome == "pedido-add":
            s.add_argument("--cliente", type=int, required=True)
            s.add_argument("--item", type=_item, action="append", required=True)
            s.add_argument("--cupom")
        elif nome == "pedidos":
            s.add_argument("--status")
        else:
            s.add_argument("pedido", type=int)
        s.set_defaults(func=func)

    s = sub.add_parser("pagar", help="registra pagamento")
    s.add_argument("pedido", type=int)
    s.add_argument("--forma", required=True)
    s.set_defaults(func=cmd_pagar)

    s = sub.add_parser("vendas", help="vendas no período")
    s.add_argument("--inicio", required=True)
    s.add_argument("--fim", required=True)
    s.set_defaults(func=cmd_vendas)

    s = sub.add_parser("resumo", help="resumo de vendas do dia")
    s.add_argument("--data", help="dd/mm/aaaa (padrão: hoje)")
    s.set_defaults(func=cmd_resumo)

    s = sub.add_parser("mais-vendidos", help="produtos mais vendidos")
    s.add_argument("--limite", type=int, default=5)
    s.set_defaults(func=cmd_mais_vendidos)

    s = sub.add_parser("recibo", help="imprime o recibo do pedido")
    s.add_argument("pedido", type=int)
    s.set_defaults(func=cmd_recibo)

    s = sub.add_parser("fornecedor-add", help="cadastra fornecedor")
    s.add_argument("--nome", required=True)
    s.add_argument("--cnpj", required=True)
    s.add_argument("--email")
    s.add_argument("--telefone")
    s.add_argument("--prazo", type=int, default=7, help="prazo de entrega em dias")
    s.set_defaults(func=cmd_fornecedor_add)

    s = sub.add_parser("fornecedores", help="lista fornecedores")
    s.set_defaults(func=cmd_fornecedores)

    for nome, func, campo in (("caixa-abrir", cmd_caixa_abrir, "--troco"),
                              ("caixa-fechar", cmd_caixa_fechar, "--contado")):
        s = sub.add_parser(nome)
        s.add_argument("--usuario", required=True)
        s.add_argument("--senha", required=True)
        s.add_argument(campo, required=True, help="valor em reais, ex.: 100,00")
        s.set_defaults(func=func)

    s = sub.add_parser("entrega", help="agenda entrega do pedido")
    s.add_argument("pedido", type=int)
    s.add_argument("--cep", required=True)
    s.add_argument("--data", help="dd/mm/aaaa; sem data usa o próximo dia livre")
    s.add_argument("--endereco")
    s.set_defaults(func=cmd_entrega)

    s = sub.add_parser("entregas", help="entregas do dia")
    s.add_argument("--data")
    s.set_defaults(func=cmd_entregas)

    s = sub.add_parser("backup", help="cópia de segurança do banco")
    s.add_argument("--pasta", default="backups")
    s.add_argument("--manter", type=int, default=7)
    s.set_defaults(func=cmd_backup)

    s = sub.add_parser("exportar-clientes", help="exporta clientes em CSV")
    s.add_argument("arquivo")
    s.set_defaults(func=cmd_exportar_clientes)

    s = sub.add_parser("importar-clientes", help="importa clientes de CSV")
    s.add_argument("arquivo")
    s.set_defaults(func=cmd_importar_clientes)
    return p


def main(argv=None):
    args = montar_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, PermissionError) as erro:
        print("Erro: %s" % erro, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
