import os
import shutil
import tempfile
import unittest

import loja

CPF_MARIA = "529.982.247-25"
CPF_JOAO = "111.444.777-35"


class TesteComBanco(unittest.TestCase):
    """Cada teste ganha um banco novo numa pasta temporária."""

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="loja-teste-")
        self.conn = loja.conectar(os.path.join(self.pasta, "teste.db"))

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def novo_cliente(self, nome="Maria Souza", cpf=CPF_MARIA, email="maria@email.com"):
        return loja.cadastrar_cliente(self.conn, nome, cpf, email)

    def novo_produto(self, codigo="CAF-500", nome="Café 500g", preco=1890, estoque=40):
        return loja.cadastrar_produto(self.conn, codigo, nome, preco, estoque)

    def novo_vendedor(self, login="bruno", papel="vendedor"):
        return loja.criar_usuario(self.conn, login, "abacaxi", papel)
