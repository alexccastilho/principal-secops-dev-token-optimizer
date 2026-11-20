import unittest

import loja

from tests.apoio import CPF_JOAO, TesteComBanco


class TestClientes(TesteComBanco):
    def test_cadastrar_e_buscar(self):
        cid = loja.cadastrar_cliente(
            self.conn, "Maria Souza", "529.982.247-25", "Maria@Email.com", "11987654321"
        )
        cliente = loja.buscar_cliente(self.conn, cid)
        self.assertEqual(cliente["nome"], "Maria Souza")
        self.assertEqual(cliente["cpf"], "52998224725")
        self.assertEqual(cliente["email"], "maria@email.com")
        self.assertEqual(cliente["telefone"], "(11) 98765-4321")

    def test_cpf_invalido_nao_cadastra(self):
        with self.assertRaises(ValueError):
            loja.cadastrar_cliente(self.conn, "Fulano", "123.456.789-00", "f@email.com")

    def test_cpf_repetido(self):
        self.novo_cliente()
        with self.assertRaises(ValueError):
            self.novo_cliente(nome="Outra Maria", email="outra@email.com")

    def test_listar_em_ordem_alfabetica(self):
        self.novo_cliente(nome="Zélia Prado")
        self.novo_cliente(nome="Ana Lima", cpf=CPF_JOAO, email="ana@email.com")
        nomes = [c["nome"] for c in loja.listar_clientes(self.conn)]
        self.assertEqual(nomes, ["Ana Lima", "Zélia Prado"])

    def test_atualizar(self):
        cid = self.novo_cliente()
        self.assertTrue(loja.atualizar_cliente(self.conn, cid, telefone="1134567890"))
        self.assertEqual(loja.buscar_cliente(self.conn, cid)["telefone"], "(11) 3456-7890")

    def test_remover_sem_pedidos(self):
        cid = self.novo_cliente()
        self.assertTrue(loja.remover_cliente(self.conn, cid))
        self.assertIsNone(loja.buscar_cliente(self.conn, cid))


if __name__ == "__main__":
    unittest.main()
