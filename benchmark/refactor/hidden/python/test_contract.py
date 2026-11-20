"""Contrato público da Loja do Bairro (Python).

Usa só os nomes de loja.__all__ e a linha de comando. Entradas benignas,
totais longe do limite de R$ 500,00, sem cupons cujo valor varia entre
cópias, sem acesso de dono errado e sem conferir texto de mensagem de erro.

PROJECT_ROOT aponta para a raiz do projeto (onde ficam loja/ e cli.py).
"""
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = os.path.abspath(os.environ.get("PROJECT_ROOT", os.getcwd()))
sys.path.insert(0, ROOT)

import loja  # noqa: E402

CPF_MARIA = "529.982.247-25"
CPF_JOAO = "111.444.777-35"
CPF_ANA = "123.456.789-09"
CNPJ_FORNECEDOR = "11.222.333/0001-81"
SENHA = "abacaxi1"

EXPORTS = {
    "conectar", "inicializar_banco",
    "converter_data", "converter_moeda", "formatar_cep", "formatar_cnpj", "formatar_cpf",
    "formatar_data", "formatar_moeda", "somente_digitos", "validar_cnpj", "validar_cpf",
    "validar_email",
    "atualizar_cliente", "buscar_cliente", "buscar_cliente_por_cpf", "buscar_clientes_por_nome",
    "cadastrar_cliente", "formatar_telefone", "listar_clientes", "remover_cliente",
    "atualizar_produto", "buscar_produto", "buscar_produto_por_codigo", "cadastrar_produto",
    "desativar_produto", "listar_produtos", "reajustar_precos", "reativar_produto",
    "atualizar_estoque", "historico_estoque", "produtos_estoque_baixo", "registrar_entrada",
    "registrar_saida", "valor_em_estoque",
    "calcular_desconto", "buscar_pedido", "cancelar_pedido", "criar_pedido", "listar_pedidos",
    "previa_pedido", "registrar_pagamento",
    "alterar_senha", "buscar_usuario", "criar_usuario", "desativar_usuario", "listar_usuarios",
    "verificar_senha", "encerrar_sessao", "fazer_login", "limpar_sessoes_vencidas",
    "usuario_da_sessao",
    "exportar_clientes_csv", "exportar_pedidos_csv", "produtos_mais_vendidos",
    "relatorio_pedidos", "vendas_por_periodo", "vendas_por_vendedor", "importar_clientes_csv",
    "clientes_que_mais_compram",
    "buscar_fornecedor", "cadastrar_fornecedor", "cancelar_compra", "compras_do_fornecedor",
    "custo_medio", "listar_fornecedores", "receber_compra", "registrar_compra",
    "abrir_caixa", "caixa_aberto", "fechar_caixa", "registrar_sangria", "registrar_suprimento",
    "resumo_caixa", "gerar_recibo",
    "agendar_entrega", "atualizar_status_entrega", "entregas_do_dia", "proxima_data_livre",
    "taxa_entrega",
    "fazer_backup", "listar_backups", "verificar_backup", "exportar_estoque_csv",
    "historico_cliente", "buscar_produtos", "resumo_do_dia",
}


class Base(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="contrato-")
        self.caminho = os.path.join(self.pasta, "loja.db")
        self.conn = loja.conectar(self.caminho)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def arquivo(self, nome):
        return os.path.join(self.pasta, nome)

    # dados de apoio -------------------------------------------------------
    def cliente(self, nome="Maria Souza", cpf=CPF_MARIA, email="maria@email.com"):
        return loja.cadastrar_cliente(self.conn, nome, cpf, email)

    def produto(self, codigo="CAF-500", nome="Café 500g", preco=1890, estoque=40):
        return loja.cadastrar_produto(self.conn, codigo, nome, preco, estoque)

    def sessao(self, login, papel="vendedor"):
        loja.criar_usuario(self.conn, login, SENHA, papel)
        token = loja.fazer_login(self.conn, login, SENHA)
        return loja.usuario_da_sessao(self.conn, token)

    def pedido(self, cliente_id, vendedor, itens, cupom=None):
        return loja.criar_pedido(self.conn, cliente_id, itens, vendedor["id"], cupom)


class TestExportacoes(unittest.TestCase):
    def test_lista_de_exportacoes(self):
        self.assertEqual(set(loja.__all__), EXPORTS)
        for nome in loja.__all__:
            self.assertTrue(callable(getattr(loja, nome)), nome)

    def test_cada_exportacao_e_exercitada(self):
        with open(__file__, encoding="utf-8") as arq:
            fonte = arq.read()
        faltando = [n for n in EXPORTS if not re.search(r"loja\." + n + r"\(", fonte)]
        self.assertEqual(faltando, [])


class TestBanco(Base):
    def test_conectar_cria_e_reabre(self):
        cid = self.cliente()
        loja.inicializar_banco(self.conn)
        self.conn.close()
        self.conn = loja.conectar(self.caminho)
        self.assertEqual(loja.buscar_cliente(self.conn, cid)["nome"], "Maria Souza")


class TestUtil(unittest.TestCase):
    def test_moeda(self):
        self.assertEqual(loja.formatar_moeda(123456), "R$ 1.234,56")
        self.assertEqual(loja.formatar_moeda(1890), "R$ 18,90")
        self.assertEqual(loja.formatar_moeda(0), "R$ 0,00")
        self.assertEqual(loja.converter_moeda("R$ 1.234,56"), 123456)
        self.assertEqual(loja.converter_moeda("18,90"), 1890)

    def test_datas(self):
        self.assertEqual(loja.formatar_data("2024-03-05"), "05/03/2024")
        self.assertEqual(loja.formatar_data("2024-12-31 23:59:00"), "31/12/2024")
        self.assertEqual(loja.converter_data("05/03/2024"), "2024-03-05")
        with self.assertRaises(ValueError):
            loja.converter_data("31/02/2024")

    def test_documentos(self):
        self.assertEqual(loja.somente_digitos("529.982.247-25"), "52998224725")
        self.assertTrue(loja.validar_cpf(CPF_MARIA))
        self.assertFalse(loja.validar_cpf("529.982.247-24"))
        self.assertEqual(loja.formatar_cpf("52998224725"), "529.982.247-25")
        self.assertTrue(loja.validar_cnpj(CNPJ_FORNECEDOR))
        self.assertFalse(loja.validar_cnpj("11.222.333/0001-82"))
        self.assertEqual(loja.formatar_cnpj("11222333000181"), "11.222.333/0001-81")
        self.assertEqual(loja.formatar_cep("01310100"), "01310-100")

    def test_email_e_telefone(self):
        self.assertTrue(loja.validar_email("maria.silva@email.com"))
        self.assertFalse(loja.validar_email("maria.silva"))
        self.assertEqual(loja.formatar_telefone("11987654321"), "(11) 98765-4321")
        self.assertEqual(loja.formatar_telefone("1134567890"), "(11) 3456-7890")


class TestClientes(Base):
    def test_cadastrar_e_buscar(self):
        cid = loja.cadastrar_cliente(
            self.conn, "Maria Souza", CPF_MARIA, "maria@email.com", "11987654321", "01310100")
        c = loja.buscar_cliente(self.conn, cid)
        self.assertEqual((c["id"], c["nome"], c["cpf"], c["email"]),
                         (cid, "Maria Souza", "52998224725", "maria@email.com"))
        self.assertEqual(c["telefone"], "(11) 98765-4321")
        self.assertEqual(c["cep"], "01310-100")
        self.assertEqual(loja.buscar_cliente_por_cpf(self.conn, "52998224725")["id"], cid)
        self.assertIsNone(loja.buscar_cliente(self.conn, 999))

    def test_dados_invalidos(self):
        with self.assertRaises(ValueError):
            loja.cadastrar_cliente(self.conn, "Fulano", "123.456.789-00", "f@email.com")
        with self.assertRaises(ValueError):
            loja.cadastrar_cliente(self.conn, "Fulano", CPF_MARIA, "fulano")
        self.cliente()
        with self.assertRaises(ValueError):
            self.cliente(nome="Outra", email="outra@email.com")

    def test_listar_e_buscar_por_nome(self):
        self.cliente("Maria Souza")
        self.cliente("João Souza", CPF_JOAO, "joao@email.com")
        self.cliente("Ana Lima", CPF_ANA, "ana@email.com")
        nomes = [c["nome"] for c in loja.listar_clientes(self.conn)]
        self.assertEqual(nomes, ["Ana Lima", "João Souza", "Maria Souza"])
        achados = sorted(c["nome"] for c in loja.buscar_clientes_por_nome(self.conn, "Souza"))
        self.assertEqual(achados, ["João Souza", "Maria Souza"])

    def test_atualizar_e_remover(self):
        cid = self.cliente()
        self.assertTrue(loja.atualizar_cliente(self.conn, cid, nome="Maria S. Lima",
                                               email="nova@email.com"))
        c = loja.buscar_cliente(self.conn, cid)
        self.assertEqual((c["nome"], c["email"]), ("Maria S. Lima", "nova@email.com"))
        self.assertFalse(loja.atualizar_cliente(self.conn, 999, nome="X"))
        self.assertTrue(loja.remover_cliente(self.conn, cid))
        self.assertIsNone(loja.buscar_cliente(self.conn, cid))

    def test_cliente_com_pedido_nao_e_removido(self):
        cid = self.cliente()
        vendedor = self.sessao("bruno")
        pid = self.pedido(cid, vendedor, [{"produto_id": self.produto(), "quantidade": 1}])
        with self.assertRaises(ValueError):
            loja.remover_cliente(self.conn, cid)
        historico = loja.historico_cliente(self.conn, cid)
        self.assertEqual([(h["pedido_id"], h["total"], h["status"]) for h in historico],
                         [(pid, 1890, "aberto")])


class TestProdutos(Base):
    def test_cadastrar_e_buscar(self):
        pid = self.produto(codigo="caf-500")
        p = loja.buscar_produto(self.conn, pid)
        self.assertEqual((p["codigo"], p["nome"], p["preco"], p["estoque"]),
                         ("CAF-500", "Café 500g", 1890, 40))
        self.assertTrue(p["ativo"])
        self.assertEqual(loja.buscar_produto_por_codigo(self.conn, "CAF-500")["id"], pid)
        self.produto(codigo="ARZ-5", nome="Arroz 5kg", preco=2490)
        self.assertEqual([p["codigo"] for p in loja.buscar_produtos(self.conn, "café")], ["CAF-500"])
        self.assertEqual([p["codigo"] for p in loja.buscar_produtos(self.conn, "ARZ")], ["ARZ-5"])

    def test_atualizar_desativar_reativar(self):
        pid = self.produto()
        self.assertTrue(loja.atualizar_produto(self.conn, pid, nome="Café Torrado 500g", preco=2100))
        p = loja.buscar_produto(self.conn, pid)
        self.assertEqual((p["nome"], p["preco"]), ("Café Torrado 500g", 2100))
        self.assertTrue(loja.desativar_produto(self.conn, pid))
        self.assertEqual(loja.listar_produtos(self.conn), [])
        self.assertEqual(len(loja.listar_produtos(self.conn, apenas_ativos=False)), 1)
        self.assertTrue(loja.reativar_produto(self.conn, pid))
        self.assertEqual([p["id"] for p in loja.listar_produtos(self.conn)], [pid])

    def test_reajustar_precos(self):
        a = self.produto(codigo="A-1", preco=1000)
        b = self.produto(codigo="B-1", preco=2500)
        self.assertEqual(loja.reajustar_precos(self.conn, 10), 2)
        self.assertEqual(loja.buscar_produto(self.conn, a)["preco"], 1100)
        self.assertEqual(loja.buscar_produto(self.conn, b)["preco"], 2750)


class TestEstoque(Base):
    def test_entrada_saida_historico(self):
        pid = self.produto(estoque=10)
        self.assertEqual(loja.registrar_entrada(self.conn, pid, 5), 15)
        self.assertEqual(loja.registrar_saida(self.conn, pid, 3, "quebra"), 12)
        with self.assertRaises(ValueError):
            loja.registrar_saida(self.conn, pid, 100)
        tipos = [m["tipo"] for m in loja.historico_estoque(self.conn, pid)]
        self.assertEqual(tipos, ["saida", "entrada", "entrada"])

    def test_atualizar_estoque(self):
        pid = self.produto(estoque=10)
        self.assertTrue(loja.atualizar_estoque(self.conn, pid, 30))
        self.assertEqual(loja.buscar_produto(self.conn, pid)["estoque"], 30)

    def test_estoque_baixo_e_valor(self):
        self.produto(codigo="A-1", nome="Pouco", preco=1000, estoque=2)
        self.produto(codigo="B-1", nome="Bastante", preco=500, estoque=50)
        self.assertEqual([p["codigo"] for p in loja.produtos_estoque_baixo(self.conn)], ["A-1"])
        self.assertEqual(loja.valor_em_estoque(self.conn), 2 * 1000 + 50 * 500)


class TestPedidos(Base):
    def setUp(self):
        super().setUp()
        self.cid = self.cliente()
        self.vendedor = self.sessao("bruno")
        self.admin = self.sessao("ana", "admin")
        self.cafe = self.produto()

    def test_calcular_desconto(self):
        self.assertEqual(loja.calcular_desconto(10000), 0)
        self.assertEqual(loja.calcular_desconto(100000), 10000)
        self.assertEqual(loja.calcular_desconto(10000, "BAIRRO10"), 1000)
        self.assertEqual(loja.calcular_desconto(100000, "BAIRRO10"), 20000)

    def test_pedido_pequeno(self):
        pid = self.pedido(self.cid, self.vendedor, [{"produto_id": self.cafe, "quantidade": 2}])
        p = loja.buscar_pedido(self.conn, pid, self.vendedor)
        self.assertEqual((p["subtotal"], p["desconto"], p["total"]), (3780, 0, 3780))
        self.assertEqual((p["cliente_id"], p["vendedor_id"], p["status"]),
                         (self.cid, self.vendedor["id"], "aberto"))
        self.assertEqual(len(p["itens"]), 1)
        item = p["itens"][0]
        self.assertEqual((item["produto_id"], item["quantidade"], item["preco_unitario"],
                          item["total"]), (self.cafe, 2, 1890, 3780))
        self.assertEqual(loja.buscar_produto(self.conn, self.cafe)["estoque"], 38)

    def test_pedido_grande_tem_desconto(self):
        tv = self.produto(codigo="TV-32", nome="TV 32", preco=120000, estoque=5)
        pid = self.pedido(self.cid, self.vendedor, [{"produto_id": tv, "quantidade": 1}])
        p = loja.buscar_pedido(self.conn, pid, self.admin)
        self.assertEqual((p["subtotal"], p["desconto"], p["total"]), (120000, 12000, 108000))

    def test_cupom_bairro10(self):
        pid = self.pedido(self.cid, self.vendedor,
                          [{"produto_id": self.cafe, "quantidade": 10}], "BAIRRO10")
        p = loja.buscar_pedido(self.conn, pid, self.vendedor)
        self.assertEqual((p["subtotal"], p["desconto"], p["total"]), (18900, 1890, 17010))

    def test_itens_repetidos_somam(self):
        pid = self.pedido(self.cid, self.vendedor, [
            {"produto_id": self.cafe, "quantidade": 1},
            {"produto_id": self.cafe, "quantidade": 2},
        ])
        p = loja.buscar_pedido(self.conn, pid, self.vendedor)
        self.assertEqual(p["total"], 3 * 1890)
        self.assertEqual(sum(i["quantidade"] for i in p["itens"]), 3)

    def test_pedido_invalido_nao_grava(self):
        with self.assertRaises(ValueError):
            self.pedido(self.cid, self.vendedor, [{"produto_id": self.cafe, "quantidade": 41}])
        with self.assertRaises(ValueError):
            self.pedido(self.cid, self.vendedor, [])
        with self.assertRaises(ValueError):
            self.pedido(999, self.vendedor, [{"produto_id": self.cafe, "quantidade": 1}])
        self.assertEqual(loja.buscar_produto(self.conn, self.cafe)["estoque"], 40)
        self.assertEqual(loja.listar_pedidos(self.conn, self.admin), [])

    def test_listar_pedidos_por_papel(self):
        outro = self.sessao("carla")
        p1 = self.pedido(self.cid, self.vendedor, [{"produto_id": self.cafe, "quantidade": 1}])
        p2 = self.pedido(self.cid, outro, [{"produto_id": self.cafe, "quantidade": 1}])
        self.assertEqual([p["id"] for p in loja.listar_pedidos(self.conn, self.vendedor)], [p1])
        self.assertEqual(sorted(p["id"] for p in loja.listar_pedidos(self.conn, self.admin)),
                         [p1, p2])
        loja.registrar_pagamento(self.conn, p2, "pix")
        self.assertEqual([p["id"] for p in loja.listar_pedidos(self.conn, self.admin, "pago")],
                         [p2])

    def test_cancelar_e_pagar(self):
        p1 = self.pedido(self.cid, self.vendedor, [{"produto_id": self.cafe, "quantidade": 5}])
        p2 = self.pedido(self.cid, self.vendedor, [{"produto_id": self.cafe, "quantidade": 1}])
        self.assertTrue(loja.cancelar_pedido(self.conn, p1, self.admin))
        self.assertEqual(loja.buscar_pedido(self.conn, p1, self.admin)["status"], "cancelado")
        self.assertEqual(loja.buscar_produto(self.conn, self.cafe)["estoque"], 39)
        with self.assertRaises(ValueError):
            loja.registrar_pagamento(self.conn, p1, "pix")
        self.assertTrue(loja.registrar_pagamento(self.conn, p2, "dinheiro"))
        p = loja.buscar_pedido(self.conn, p2, self.vendedor)
        self.assertEqual((p["status"], p["forma_pagamento"]), ("pago", "dinheiro"))

    def test_previa_nao_grava(self):
        tv = self.produto(codigo="TV-32", nome="TV 32", preco=120000, estoque=5)
        self.assertEqual(loja.previa_pedido(self.conn, [{"produto_id": self.cafe, "quantidade": 2}]),
                         {"subtotal": 3780, "desconto": 0, "total": 3780})
        self.assertEqual(loja.previa_pedido(self.conn, [{"produto_id": tv, "quantidade": 1}]),
                         {"subtotal": 120000, "desconto": 12000, "total": 108000})
        self.assertEqual(loja.buscar_produto(self.conn, tv)["estoque"], 5)

    def test_recibo(self):
        pid = self.pedido(self.cid, self.vendedor, [{"produto_id": self.cafe, "quantidade": 2}])
        loja.registrar_pagamento(self.conn, pid, "pix")
        texto = loja.gerar_recibo(self.conn, pid)
        self.assertIn("Pedido: %d" % pid, texto)
        self.assertIn("Café 500g", texto)
        self.assertIn("R$ 37,80", texto)


class TestUsuarios(Base):
    def test_criar_buscar_listar(self):
        uid = loja.criar_usuario(self.conn, "Carla", SENHA, "admin", "Carla Dias")
        u = loja.buscar_usuario(self.conn, "carla")
        self.assertEqual((u["id"], u["login"], u["papel"], u["nome"]),
                         (uid, "carla", "admin", "Carla Dias"))
        loja.criar_usuario(self.conn, "bruno", SENHA)
        usuarios = loja.listar_usuarios(self.conn)
        self.assertEqual([x["login"] for x in usuarios], ["bruno", "carla"])
        self.assertEqual(usuarios[0]["papel"], "vendedor")
        with self.assertRaises(ValueError):
            loja.criar_usuario(self.conn, "dono", SENHA, "gerente")
        with self.assertRaises(ValueError):
            loja.criar_usuario(self.conn, "dono", "abc")

    def test_senhas(self):
        loja.criar_usuario(self.conn, "bruno", SENHA)
        self.assertTrue(loja.verificar_senha(self.conn, "bruno", SENHA))
        self.assertFalse(loja.verificar_senha(self.conn, "bruno", "laranja1"))
        self.assertFalse(loja.alterar_senha(self.conn, "bruno", "laranja1", "uvaverde"))
        self.assertTrue(loja.alterar_senha(self.conn, "bruno", SENHA, "uvaverde"))
        self.assertTrue(loja.verificar_senha(self.conn, "bruno", "uvaverde"))
        self.assertTrue(loja.desativar_usuario(self.conn, "bruno"))
        self.assertFalse(loja.verificar_senha(self.conn, "bruno", "uvaverde"))

    def test_sessao(self):
        uid = loja.criar_usuario(self.conn, "bruno", SENHA)
        token = loja.fazer_login(self.conn, "bruno", SENHA)
        self.assertIsInstance(token, str)
        u = loja.usuario_da_sessao(self.conn, token)
        self.assertEqual((u["id"], u["login"], u["papel"]), (uid, "bruno", "vendedor"))
        self.assertIsNone(loja.fazer_login(self.conn, "bruno", "laranja1"))
        self.assertIsNone(loja.usuario_da_sessao(self.conn, "token-que-nao-existe"))
        self.assertEqual(loja.limpar_sessoes_vencidas(self.conn), 0)
        self.assertTrue(loja.encerrar_sessao(self.conn, token))
        self.assertIsNone(loja.usuario_da_sessao(self.conn, token))


class TestRelatorios(Base):
    def setUp(self):
        super().setUp()
        self.maria = self.cliente()
        self.joao = self.cliente("João Souza", CPF_JOAO, "joao@email.com")
        self.vendedor = self.sessao("bruno")
        self.admin = self.sessao("ana", "admin")
        self.cafe = self.produto()
        self.arroz = self.produto(codigo="ARZ-5", nome="Arroz 5kg", preco=2490, estoque=30)
        self.p1 = self.pedido(self.maria, self.vendedor, [{"produto_id": self.cafe, "quantidade": 3}])
        self.p2 = self.pedido(self.joao, self.admin, [{"produto_id": self.arroz, "quantidade": 1}])
        self.p3 = self.pedido(self.joao, self.vendedor, [{"produto_id": self.arroz, "quantidade": 2}])
        loja.cancelar_pedido(self.conn, self.p3, self.admin)

    def test_vendas(self):
        hoje = date.today()
        inicio = (hoje - timedelta(days=1)).strftime("%d/%m/%Y")
        fim = (hoje + timedelta(days=1)).strftime("%d/%m/%Y")
        r = loja.vendas_por_periodo(self.conn, inicio, fim)
        self.assertEqual((r["quantidade_pedidos"], r["total"]), (2, 3 * 1890 + 2490))
        por_vendedor = {v["login"]: v["total"] for v in loja.vendas_por_vendedor(self.conn, inicio, fim)}
        self.assertEqual(por_vendedor, {"bruno": 3 * 1890, "ana": 2490})
        resumo = loja.resumo_do_dia(self.conn)
        self.assertEqual((resumo["pedidos"], resumo["cancelados"], resumo["total"]),
                         (2, 1, 3 * 1890 + 2490))
        self.assertEqual(resumo["ticket_medio"], (3 * 1890 + 2490) // 2)

    def test_rankings(self):
        mais = loja.produtos_mais_vendidos(self.conn, 5)
        self.assertEqual([(p["codigo"], p["quantidade"]) for p in mais], [("CAF-500", 3), ("ARZ-5", 1)])
        clientes = loja.clientes_que_mais_compram(self.conn, 10)
        self.assertEqual([(c["nome"], c["total"]) for c in clientes],
                         [("Maria Souza", 5670), ("João Souza", 2490)])

    def test_relatorio_pedidos_ordenado(self):
        linhas = loja.relatorio_pedidos(self.conn, "total")
        self.assertEqual([l["id"] for l in linhas], [self.p2, self.p3, self.p1])
        linhas = loja.relatorio_pedidos(self.conn, "total", decrescente=True)
        self.assertEqual([l["id"] for l in linhas], [self.p1, self.p3, self.p2])
        self.assertEqual((linhas[0]["cliente"], linhas[0]["vendedor"]), ("Maria Souza", "bruno"))
        self.assertEqual(len(loja.relatorio_pedidos(self.conn)), 3)

    def _ler_csv(self, caminho):
        with open(caminho, newline="", encoding="utf-8-sig") as arq:
            return list(csv.reader(arq, delimiter=";"))

    def test_exportar_clientes(self):
        caminho = self.arquivo("clientes.csv")
        self.assertEqual(loja.exportar_clientes_csv(self.conn, caminho), 2)
        linhas = self._ler_csv(caminho)
        self.assertEqual(linhas[0][:4], ["id", "nome", "cpf", "email"])
        self.assertEqual(linhas[1][1], "Maria Souza")
        self.assertEqual(linhas[2][3], "joao@email.com")

    def test_exportar_pedidos_e_estoque(self):
        caminho = self.arquivo("pedidos.csv")
        self.assertEqual(loja.exportar_pedidos_csv(self.conn, caminho), 3)
        linhas = self._ler_csv(caminho)
        self.assertEqual(len(linhas), 4)
        self.assertEqual(linhas[1][1], "Maria Souza")
        caminho = self.arquivo("estoque.csv")
        self.assertEqual(loja.exportar_estoque_csv(self.conn, caminho), 2)
        self.assertEqual([l[0] for l in self._ler_csv(caminho)[1:]], ["ARZ-5", "CAF-500"])

    def test_importar_clientes(self):
        caminho = self.arquivo("importar.csv")
        with open(caminho, "w", newline="", encoding="utf-8") as arq:
            arq.write("nome;cpf;email;telefone\n")
            arq.write("Ana Lima;123.456.789-09;ana@email.com;11987654321\n")
            arq.write("Maria Souza;529.982.247-25;maria@email.com;\n")
            arq.write("Sem Documento;000;sem@email.com;\n")
        r = loja.importar_clientes_csv(self.conn, caminho)
        self.assertEqual((r["importados"], r["ignorados"], len(r["erros"])), (1, 1, 1))
        ana = loja.buscar_cliente_por_cpf(self.conn, CPF_ANA)
        self.assertEqual((ana["nome"], ana["email"]), ("Ana Lima", "ana@email.com"))


class TestFornecedores(Base):
    def test_cadastro(self):
        fid = loja.cadastrar_fornecedor(self.conn, "Distribuidora Paulista", CNPJ_FORNECEDOR,
                                        "vendas@distpaulista.com.br", "1133334444", 5)
        f = loja.buscar_fornecedor(self.conn, fid)
        self.assertEqual((f["nome"], f["cnpj"], f["prazo_entrega_dias"]),
                         ("Distribuidora Paulista", "11222333000181", 5))
        self.assertEqual([x["id"] for x in loja.listar_fornecedores(self.conn)], [fid])
        with self.assertRaises(ValueError):
            loja.cadastrar_fornecedor(self.conn, "Outra", "11.222.333/0001-82")

    def test_compras(self):
        fid = loja.cadastrar_fornecedor(self.conn, "Distribuidora Paulista", CNPJ_FORNECEDOR)
        pid = self.produto(estoque=10)
        c1 = loja.registrar_compra(self.conn, fid, [
            {"produto_id": pid, "quantidade": 20, "custo_unitario": 1000}])
        c2 = loja.registrar_compra(self.conn, fid, [
            {"produto_id": pid, "quantidade": 10, "custo_unitario": 1300}])
        self.assertIsNone(loja.custo_medio(self.conn, pid))
        self.assertEqual(loja.receber_compra(self.conn, c1), 1)
        self.assertEqual(loja.receber_compra(self.conn, c2), 1)
        self.assertEqual(loja.buscar_produto(self.conn, pid)["estoque"], 40)
        self.assertEqual(loja.custo_medio(self.conn, pid), (20 * 1000 + 10 * 1300) // 30)
        c3 = loja.registrar_compra(self.conn, fid, [
            {"produto_id": pid, "quantidade": 1, "custo_unitario": 900}])
        self.assertTrue(loja.cancelar_compra(self.conn, c3))
        compras = loja.compras_do_fornecedor(self.conn, fid)
        self.assertEqual([(c["id"], c["status"]) for c in compras],
                         [(c3, "cancelada"), (c2, "recebida"), (c1, "recebida")])
        self.assertEqual(compras[2]["total"], 20000)


class TestCaixa(Base):
    def test_ciclo_do_caixa(self):
        vendedor = self.sessao("bruno")
        cid = self.cliente()
        cafe = self.produto()
        self.assertIsNone(loja.caixa_aberto(self.conn))
        caixa_id = loja.abrir_caixa(self.conn, vendedor["id"], 10000)
        self.assertEqual(loja.caixa_aberto(self.conn)["id"], caixa_id)
        pid = self.pedido(cid, vendedor, [{"produto_id": cafe, "quantidade": 2}])
        loja.registrar_pagamento(self.conn, pid, "dinheiro")
        loja.registrar_sangria(self.conn, 5000, "banco")
        loja.registrar_suprimento(self.conn, 1000, "troco")
        r = loja.resumo_caixa(self.conn)
        self.assertEqual(r["esperado_em_dinheiro"], 10000 + 3780 - 5000 + 1000)
        self.assertEqual(r["vendas_por_forma"]["dinheiro"], 3780)
        fechado = loja.fechar_caixa(self.conn, 9700)
        self.assertEqual(fechado["diferenca"], 9700 - 9780)
        self.assertIsNone(loja.caixa_aberto(self.conn))


class TestEntregasEBackup(Base):
    def test_entregas(self):
        self.assertEqual(loja.taxa_entrega("01310-100"), 500)
        self.assertEqual(loja.taxa_entrega("01310-100", 30000), 0)
        with self.assertRaises(ValueError):
            loja.taxa_entrega("99999-999")
        vendedor = self.sessao("bruno")
        pid = self.pedido(self.cliente(), vendedor, [{"produto_id": self.produto(), "quantidade": 1}])
        data = loja.proxima_data_livre(self.conn)
        eid = loja.agendar_entrega(self.conn, pid, "01310100", data, "Rua A, 10")
        dia = loja.entregas_do_dia(self.conn, data)
        self.assertEqual([(e["id"], e["pedido_id"], e["status"]) for e in dia],
                         [(eid, pid, "agendada")])
        self.assertTrue(loja.atualizar_status_entrega(self.conn, eid, "entregue"))
        self.assertEqual(loja.entregas_do_dia(self.conn, data)[0]["status"], "entregue")

    def test_backup(self):
        cid = self.cliente()
        pasta = self.arquivo("backups")
        destino = loja.fazer_backup(self.conn, pasta)
        self.assertTrue(os.path.exists(destino))
        self.assertTrue(loja.verificar_backup(destino))
        self.assertEqual(loja.listar_backups(pasta), [destino])
        copia = loja.conectar(destino)
        try:
            self.assertEqual(loja.buscar_cliente(copia, cid)["nome"], "Maria Souza")
        finally:
            copia.close()


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="contrato-cli-")
        self.db = os.path.join(self.pasta, "loja.db")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def cli(self, *args, ok=True):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        env.pop("LOJA_DB", None)
        proc = subprocess.run(
            [sys.executable, "-B", os.path.join(ROOT, "cli.py"), "--db", self.db] + list(args),
            capture_output=True, encoding="utf-8", errors="replace", env=env, cwd=self.pasta,
            timeout=120,
        )
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def linhas(self, *args):
        return self.cli(*args).stdout.splitlines()

    def preparar(self):
        self.cli("init")
        self.cli("usuario-add", "ana", "--senha", SENHA, "--papel", "admin")
        self.cli("cliente-add", "--nome", "Maria Souza", "--cpf", CPF_MARIA,
                 "--email", "maria@email.com")
        self.cli("produto-add", "--codigo", "CAF-500", "--nome", "Café 500g",
                 "--preco", "18,90", "--estoque", "40")

    def test_cadastros(self):
        self.assertEqual(self.linhas("init"), ["Banco pronto: %s" % self.db])
        self.assertEqual(self.linhas("usuario-add", "ana", "--senha", SENHA, "--papel", "admin"),
                         ["Usuario ana criado (id 1, papel admin)"])
        self.assertEqual(self.linhas("cliente-add", "--nome", "Maria Souza", "--cpf", "52998224725",
                                     "--email", "maria@email.com"), ["Cliente cadastrado: 1"])
        self.assertEqual(self.linhas("clientes"),
                         ["1 | Maria Souza | 529.982.247-25 | maria@email.com"])
        self.assertEqual(self.linhas("clientes", "--busca", "Souza"),
                         ["1 | Maria Souza | 529.982.247-25 | maria@email.com"])
        self.assertEqual(self.linhas("fornecedor-add", "--nome", "Distribuidora", "--cnpj",
                                     CNPJ_FORNECEDOR), ["Fornecedor cadastrado: 1"])
        self.assertEqual(self.linhas("fornecedores"),
                         ["1 | Distribuidora | 11.222.333/0001-81 | prazo 7 dia(s)"])

    def test_produtos_e_estoque(self):
        self.cli("init")
        self.assertEqual(self.linhas("produto-add", "--codigo", "CAF-500", "--nome", "Café 500g",
                                     "--preco", "18,90", "--estoque", "40"),
                         ["Produto cadastrado: 1"])
        self.assertEqual(self.linhas("produto-add", "--codigo", "ARZ-5", "--nome", "Arroz 5kg",
                                     "--preco", "24,90", "--estoque", "3"),
                         ["Produto cadastrado: 2"])
        self.assertEqual(self.linhas("produtos"), [
            "2 | ARZ-5 | Arroz 5kg | R$ 24,90 | estoque 3",
            "1 | CAF-500 | Café 500g | R$ 18,90 | estoque 40",
        ])
        self.assertEqual(self.linhas("estoque-baixo"), ["ARZ-5 | Arroz 5kg | estoque 3 (minimo 5)"])
        self.assertEqual(self.linhas("entrada", "2", "10"), ["Estoque de ARZ-5: 13"])
        self.assertEqual(self.linhas("estoque-baixo"), ["Nenhum produto com estoque baixo."])

    def test_pedido(self):
        self.preparar()
        self.assertEqual(self.linhas("pedido-add", "--usuario", "ana", "--senha", SENHA,
                                     "--cliente", "1", "--item", "1:2"),
                         ["Pedido 1 criado: total R$ 37,80"])
        self.assertEqual(self.linhas("pedido-ver", "1", "--usuario", "ana", "--senha", SENHA), [
            "Pedido 1 - aberto",
            "  2 x Café 500g (R$ 18,90) = R$ 37,80",
            "Subtotal: R$ 37,80",
            "Desconto: R$ 0,00",
            "Total: R$ 37,80",
        ])
        self.assertEqual(self.linhas("pagar", "1", "--forma", "pix"), ["Pedido 1 pago (pix)."])
        self.assertEqual(self.linhas("pedidos", "--usuario", "ana", "--senha", SENHA),
                         ["1 | pago | R$ 37,80"])
        self.assertEqual(self.linhas("mais-vendidos"), ["1. Café 500g | 2 un. | R$ 37,80"])
        self.assertEqual(self.linhas("resumo"), [
            "Resumo de %s" % date.today().strftime("%d/%m/%Y"),
            "Pedidos: 1 (cancelados: 0)",
            "Total: R$ 37,80",
            "Ticket medio: R$ 37,80",
            "  pix: R$ 37,80",
        ])
        hoje = date.today()
        self.assertEqual(self.linhas("vendas", "--inicio", (hoje - timedelta(days=1)).isoformat(),
                                     "--fim", (hoje + timedelta(days=1)).isoformat()),
                         ["Pedidos: 1", "Total: R$ 37,80"])

    def test_cancelar_pedido(self):
        self.preparar()
        self.cli("pedido-add", "--usuario", "ana", "--senha", SENHA, "--cliente", "1",
                 "--item", "1:5")
        self.assertEqual(self.linhas("pedido-cancelar", "1", "--usuario", "ana", "--senha", SENHA),
                         ["Pedido 1 cancelado."])
        self.assertIn("1 | CAF-500 | Café 500g | R$ 18,90 | estoque 40", self.linhas("produtos"))

    def test_csv(self):
        self.preparar()
        destino = os.path.join(self.pasta, "clientes.csv")
        self.assertEqual(self.linhas("exportar-clientes", destino),
                         ["1 cliente(s) exportado(s) para %s" % destino])
        origem = os.path.join(self.pasta, "novos.csv")
        with open(origem, "w", newline="", encoding="utf-8") as arq:
            arq.write("nome;cpf;email\nAna Lima;123.456.789-09;ana@email.com\n")
        self.assertEqual(self.linhas("importar-clientes", origem),
                         ["Importados: 1 | Ignorados: 0 | Erros: 0"])

    def test_erros_saem_com_codigo_1(self):
        self.preparar()
        proc = self.cli("pedido-add", "--usuario", "ana", "--senha", "errada1", "--cliente", "1",
                        "--item", "1:1", ok=False)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        proc = self.cli("cliente-add", "--nome", "X", "--cpf", "123", "--email", "x@email.com",
                        ok=False)
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
