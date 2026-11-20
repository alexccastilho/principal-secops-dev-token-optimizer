import unittest

import loja

from tests.apoio import TesteComBanco


class TestPedidos(TesteComBanco):
    def setUp(self):
        super().setUp()
        self.cliente = self.novo_cliente()
        self.vendedor = self.novo_vendedor()
        self.cafe = self.novo_produto()

    def test_pedido_simples(self):
        pid = loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 2}], self.vendedor
        )
        pedido = loja.buscar_pedido(self.conn, pid)
        self.assertEqual(pedido["subtotal"], 3780)
        self.assertEqual(pedido["desconto"], 0)
        self.assertEqual(pedido["total"], 3780)
        self.assertEqual(pedido["status"], "aberto")

    def test_baixa_estoque(self):
        loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 3}], self.vendedor
        )
        self.assertEqual(loja.buscar_produto(self.conn, self.cafe)["estoque"], 37)

    def test_desconto_pedido_grande(self):
        tv = self.novo_produto(codigo="TV-32", nome="TV 32", preco=120000, estoque=5)
        pid = loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": tv, "quantidade": 1}], self.vendedor
        )
        pedido = loja.buscar_pedido(self.conn, pid)
        self.assertEqual(pedido["desconto"], 12000)
        self.assertEqual(pedido["total"], 108000)

    def test_cupom_bairro10(self):
        pid = loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 10}],
            self.vendedor, cupom="BAIRRO10",
        )
        self.assertEqual(loja.buscar_pedido(self.conn, pid)["total"], 17010)

    def test_estoque_insuficiente(self):
        with self.assertRaises(ValueError):
            loja.criar_pedido(
                self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 41}],
                self.vendedor,
            )
        self.assertEqual(loja.buscar_produto(self.conn, self.cafe)["estoque"], 40)

    def test_pedido_sem_itens(self):
        with self.assertRaises(ValueError):
            loja.criar_pedido(self.conn, self.cliente, [], self.vendedor)

    def test_cancelar_devolve_estoque(self):
        admin_id = self.novo_vendedor("ana", "admin")
        pid = loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 5}], self.vendedor
        )
        admin = {"id": admin_id, "login": "ana", "papel": "admin", "nome": ""}
        loja.cancelar_pedido(self.conn, pid, admin)
        self.assertEqual(loja.buscar_pedido(self.conn, pid, admin)["status"], "cancelado")
        self.assertEqual(loja.buscar_produto(self.conn, self.cafe)["estoque"], 40)

    def test_pagamento(self):
        pid = loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 1}], self.vendedor
        )
        loja.registrar_pagamento(self.conn, pid, "pix")
        pedido = loja.buscar_pedido(self.conn, pid)
        self.assertEqual(pedido["status"], "pago")
        self.assertEqual(pedido["forma_pagamento"], "pix")

    def test_vendas_por_periodo(self):
        loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": self.cafe, "quantidade": 2}], self.vendedor
        )
        r = loja.vendas_por_periodo(self.conn, "01/01/2000", "31/12/2099")
        self.assertEqual(r["quantidade_pedidos"], 1)
        self.assertEqual(r["total"], 3780)


if __name__ == "__main__":
    unittest.main()
