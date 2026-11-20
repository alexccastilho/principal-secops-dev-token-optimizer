import unittest

import loja

from tests.apoio import TesteComBanco


class TestUsuarios(TesteComBanco):
    def test_criar_e_verificar_senha(self):
        loja.criar_usuario(self.conn, "Carla", "abacaxi", "admin")
        self.assertTrue(loja.verificar_senha(self.conn, "carla", "abacaxi"))
        self.assertFalse(loja.verificar_senha(self.conn, "carla", "laranja"))

    def test_papel_invalido(self):
        with self.assertRaises(ValueError):
            loja.criar_usuario(self.conn, "dono", "abacaxi", "gerente")

    def test_senha_curta(self):
        with self.assertRaises(ValueError):
            loja.criar_usuario(self.conn, "dono", "abc")

    def test_alterar_senha(self):
        self.novo_vendedor()
        self.assertTrue(loja.alterar_senha(self.conn, "bruno", "abacaxi", "laranja"))
        self.assertTrue(loja.verificar_senha(self.conn, "bruno", "laranja"))

    def test_login_com_senha_errada(self):
        self.novo_vendedor()
        self.assertIsNone(loja.fazer_login(self.conn, "bruno", "laranja"))


if __name__ == "__main__":
    unittest.main()
