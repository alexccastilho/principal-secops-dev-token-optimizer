import unittest

import loja

from tests.apoio import TesteComBanco


class TestProdutos(TesteComBanco):
    def test_cadastrar_produto(self):
        pid = self.novo_produto(codigo="caf-500")
        produto = loja.buscar_produto(self.conn, pid)
        self.assertEqual(produto["codigo"], "CAF-500")
        self.assertEqual(produto["preco"], 1890)
        self.assertEqual(produto["estoque"], 40)

    def test_preco_precisa_ser_inteiro(self):
        with self.assertRaises(ValueError):
            loja.cadastrar_produto(self.conn, "ARZ-5", "Arroz 5kg", 24.9)

    def test_desativar_some_da_lista(self):
        pid = self.novo_produto()
        loja.desativar_produto(self.conn, pid)
        self.assertEqual(loja.listar_produtos(self.conn), [])


class TestEstoque(TesteComBanco):
    def test_entrada_e_saida(self):
        pid = self.novo_produto(estoque=10)
        self.assertEqual(loja.registrar_entrada(self.conn, pid, 5), 15)
        self.assertEqual(loja.registrar_saida(self.conn, pid, 3, "quebra"), 12)
        self.assertEqual(loja.buscar_produto(self.conn, pid)["estoque"], 12)

    def test_saida_maior_que_saldo(self):
        pid = self.novo_produto(estoque=2)
        with self.assertRaises(ValueError):
            loja.registrar_saida(self.conn, pid, 3)

    def test_estoque_baixo(self):
        self.novo_produto(codigo="A-1", nome="Pouco", estoque=2)
        self.novo_produto(codigo="B-1", nome="Bastante", estoque=50)
        baixos = [p["codigo"] for p in loja.produtos_estoque_baixo(self.conn)]
        self.assertEqual(baixos, ["A-1"])

    def test_historico(self):
        pid = self.novo_produto(estoque=10)
        loja.registrar_entrada(self.conn, pid, 5)
        tipos = [m["tipo"] for m in loja.historico_estoque(self.conn, pid)]
        self.assertEqual(tipos, ["entrada", "entrada"])


if __name__ == "__main__":
    unittest.main()
