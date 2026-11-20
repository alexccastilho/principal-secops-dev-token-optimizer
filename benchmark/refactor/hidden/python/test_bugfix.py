"""Regra do README: "Pedidos a partir de R$ 500,00 têm 10% de desconto."

PROJECT_ROOT aponta para a raiz do projeto (onde ficam loja/ e cli.py).
"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.environ.get("PROJECT_ROOT", os.getcwd()))
sys.path.insert(0, ROOT)

import loja  # noqa: E402


class TestDescontoAPartirDe500(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="bugfix-")
        self.conn = loja.conectar(os.path.join(self.pasta, "loja.db"))
        self.cliente = loja.cadastrar_cliente(
            self.conn, "Maria Souza", "529.982.247-25", "maria@email.com")
        loja.criar_usuario(self.conn, "ana", "abacaxi1", "admin")
        token = loja.fazer_login(self.conn, "ana", "abacaxi1")
        self.admin = loja.usuario_da_sessao(self.conn, token)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def pedido_de(self, preco):
        pid = loja.cadastrar_produto(self.conn, "P-%d" % preco, "Produto %d" % preco, preco, 5)
        pedido_id = loja.criar_pedido(
            self.conn, self.cliente, [{"produto_id": pid, "quantidade": 1}], self.admin["id"])
        return loja.buscar_pedido(self.conn, pedido_id, self.admin)

    def test_exatamente_500_tem_desconto(self):
        p = self.pedido_de(50000)
        self.assertEqual((p["subtotal"], p["desconto"], p["total"]), (50000, 5000, 45000))

    def test_499_99_sem_desconto(self):
        p = self.pedido_de(49999)
        self.assertEqual((p["subtotal"], p["desconto"], p["total"]), (49999, 0, 49999))

    def test_500_01_tem_desconto(self):
        p = self.pedido_de(50001)
        self.assertEqual((p["subtotal"], p["desconto"], p["total"]), (50001, 5000, 45001))

    def test_calcular_desconto_no_limite(self):
        self.assertEqual(loja.calcular_desconto(50000), 5000)
        self.assertEqual(loja.calcular_desconto(49999), 0)

    def test_previa_no_limite(self):
        pid = loja.cadastrar_produto(self.conn, "PREVIA", "Produto prévia", 25000, 5)
        previa = loja.previa_pedido(self.conn, [{"produto_id": pid, "quantidade": 2}])
        self.assertEqual(previa, {"subtotal": 50000, "desconto": 5000, "total": 45000})


if __name__ == "__main__":
    unittest.main()
