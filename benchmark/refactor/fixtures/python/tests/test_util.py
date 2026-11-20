import unittest

import loja


class TestMoeda(unittest.TestCase):
    def test_formatar_moeda(self):
        self.assertEqual(loja.formatar_moeda(123456), "R$ 1.234,56")
        self.assertEqual(loja.formatar_moeda(5), "R$ 0,05")

    def test_converter_moeda(self):
        self.assertEqual(loja.converter_moeda("R$ 1.234,56"), 123456)
        self.assertEqual(loja.converter_moeda("18,90"), 1890)
        self.assertEqual(loja.converter_moeda("12.50"), 1250)

    def test_converter_moeda_invalida(self):
        with self.assertRaises(ValueError):
            loja.converter_moeda("doze reais")


class TestDocumentos(unittest.TestCase):
    def test_cpf_valido(self):
        self.assertTrue(loja.validar_cpf("529.982.247-25"))
        self.assertTrue(loja.validar_cpf("11144477735"))

    def test_cpf_invalido(self):
        self.assertFalse(loja.validar_cpf("529.982.247-26"))
        self.assertFalse(loja.validar_cpf("123"))

    def test_formatar_cpf_e_cnpj(self):
        self.assertEqual(loja.formatar_cpf("52998224725"), "529.982.247-25")
        self.assertEqual(loja.formatar_cnpj("11222333000181"), "11.222.333/0001-81")

    def test_cep(self):
        self.assertEqual(loja.formatar_cep("01310100"), "01310-100")


class TestDatas(unittest.TestCase):
    def test_formatar_data(self):
        self.assertEqual(loja.formatar_data("2024-03-05 10:00:00"), "05/03/2024")

    def test_converter_data(self):
        self.assertEqual(loja.converter_data("05/03/2024"), "2024-03-05")


if __name__ == "__main__":
    unittest.main()
