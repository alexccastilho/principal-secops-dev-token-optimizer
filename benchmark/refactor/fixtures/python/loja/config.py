"""Configurações gerais da Loja do Bairro.

Valores que mudam pouco ficam aqui. O caminho do banco pode ser trocado
pela variável de ambiente LOJA_DB.
"""
import os

NOME_LOJA = "Loja do Bairro"
CNPJ_LOJA = "11222333000181"
CIDADE_LOJA = "São Paulo"
UF_LOJA = "SP"

BANCO_PADRAO = os.environ.get("LOJA_DB", "loja.db")

# usado para assinar os tokens de sessão
SEGREDO_TOKEN = "loja-bairro-2019"
DURACAO_SESSAO_HORAS = 8
TAMANHO_TOKEN = 32

ESTOQUE_MINIMO_PADRAO = 5
MAX_ITENS_POR_PEDIDO = 50
MAX_QUANTIDADE_ITEM = 999

PAPEIS = ("admin", "vendedor")
PAPEL_PADRAO = "vendedor"
TAMANHO_MINIMO_SENHA = 6

FORMAS_PAGAMENTO = ("dinheiro", "pix", "cartao", "boleto")

STATUS_ABERTO = "aberto"
STATUS_PAGO = "pago"
STATUS_CANCELADO = "cancelado"

FORMATO_DATA_HORA = "%Y-%m-%d %H:%M:%S"
FORMATO_DATA = "%Y-%m-%d"
FORMATO_DATA_BR = "%d/%m/%Y"

# separador dos arquivos CSV (Excel em português usa ponto e vírgula)
SEPARADOR_CSV = ";"
