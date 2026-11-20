"""Loja do Bairro: back office da loja (clientes, estoque, pedidos e relatórios).

Uso básico:

    import loja
    conn = loja.conectar("loja.db")
    cliente_id = loja.cadastrar_cliente(conn, "Maria", "529.982.247-25", "maria@email.com")
"""
from .db import conectar, inicializar_banco
from .util import (
    converter_data,
    converter_moeda,
    formatar_cep,
    formatar_cnpj,
    formatar_cpf,
    formatar_data,
    formatar_moeda,
    somente_digitos,
    validar_cnpj,
    validar_cpf,
    validar_email,
)
from .clientes import (
    atualizar_cliente,
    buscar_cliente,
    buscar_cliente_por_cpf,
    buscar_clientes_por_nome,
    cadastrar_cliente,
    formatar_telefone,
    historico_cliente,
    listar_clientes,
    remover_cliente,
)
from .produtos import (
    atualizar_produto,
    buscar_produto,
    buscar_produto_por_codigo,
    buscar_produtos,
    cadastrar_produto,
    desativar_produto,
    listar_produtos,
    reajustar_precos,
    reativar_produto,
)
from .estoque import (
    atualizar_estoque,
    historico_estoque,
    produtos_estoque_baixo,
    registrar_entrada,
    registrar_saida,
    valor_em_estoque,
)
from .descontos import calcular_desconto
from .pedidos import (
    buscar_pedido,
    cancelar_pedido,
    criar_pedido,
    listar_pedidos,
    previa_pedido,
    registrar_pagamento,
)
from .usuarios import (
    alterar_senha,
    buscar_usuario,
    criar_usuario,
    desativar_usuario,
    listar_usuarios,
    verificar_senha,
)
from .autenticacao import encerrar_sessao, fazer_login, limpar_sessoes_vencidas, usuario_da_sessao
from .relatorios import (
    clientes_que_mais_compram,
    exportar_clientes_csv,
    exportar_estoque_csv,
    exportar_pedidos_csv,
    produtos_mais_vendidos,
    relatorio_pedidos,
    resumo_do_dia,
    vendas_por_periodo,
    vendas_por_vendedor,
)
from .importacao import importar_clientes_csv
from .fornecedores import (
    buscar_fornecedor,
    cadastrar_fornecedor,
    cancelar_compra,
    compras_do_fornecedor,
    custo_medio,
    listar_fornecedores,
    receber_compra,
    registrar_compra,
)
from .caixa import (
    abrir_caixa,
    caixa_aberto,
    fechar_caixa,
    registrar_sangria,
    registrar_suprimento,
    resumo_caixa,
)
from .recibo import gerar_recibo
from .entregas import (
    agendar_entrega,
    atualizar_status_entrega,
    entregas_do_dia,
    proxima_data_livre,
    taxa_entrega,
)
from .backup import fazer_backup, listar_backups, verificar_backup

__version__ = "1.4.2"

__all__ = [
    # banco
    "conectar",
    "inicializar_banco",
    # utilidades
    "converter_data",
    "converter_moeda",
    "formatar_cep",
    "formatar_cnpj",
    "formatar_cpf",
    "formatar_data",
    "formatar_moeda",
    "somente_digitos",
    "validar_cnpj",
    "validar_cpf",
    "validar_email",
    # clientes
    "atualizar_cliente",
    "buscar_cliente",
    "buscar_cliente_por_cpf",
    "buscar_clientes_por_nome",
    "cadastrar_cliente",
    "formatar_telefone",
    "historico_cliente",
    "listar_clientes",
    "remover_cliente",
    # produtos e estoque
    "atualizar_produto",
    "buscar_produto",
    "buscar_produto_por_codigo",
    "buscar_produtos",
    "cadastrar_produto",
    "desativar_produto",
    "listar_produtos",
    "reajustar_precos",
    "reativar_produto",
    "atualizar_estoque",
    "historico_estoque",
    "produtos_estoque_baixo",
    "registrar_entrada",
    "registrar_saida",
    "valor_em_estoque",
    # pedidos
    "calcular_desconto",
    "buscar_pedido",
    "cancelar_pedido",
    "criar_pedido",
    "listar_pedidos",
    "previa_pedido",
    "registrar_pagamento",
    # usuários e sessão
    "alterar_senha",
    "buscar_usuario",
    "criar_usuario",
    "desativar_usuario",
    "listar_usuarios",
    "verificar_senha",
    "encerrar_sessao",
    "fazer_login",
    "limpar_sessoes_vencidas",
    "usuario_da_sessao",
    # relatórios
    "exportar_clientes_csv",
    "exportar_pedidos_csv",
    "produtos_mais_vendidos",
    "relatorio_pedidos",
    "resumo_do_dia",
    "vendas_por_periodo",
    "vendas_por_vendedor",
    "importar_clientes_csv",
    "clientes_que_mais_compram",
    # fornecedores e compras
    "buscar_fornecedor",
    "cadastrar_fornecedor",
    "cancelar_compra",
    "compras_do_fornecedor",
    "custo_medio",
    "listar_fornecedores",
    "receber_compra",
    "registrar_compra",
    # caixa
    "abrir_caixa",
    "caixa_aberto",
    "fechar_caixa",
    "registrar_sangria",
    "registrar_suprimento",
    "resumo_caixa",
    "gerar_recibo",
    # entregas
    "agendar_entrega",
    "atualizar_status_entrega",
    "entregas_do_dia",
    "proxima_data_livre",
    "taxa_entrega",
    # backup
    "fazer_backup",
    "listar_backups",
    "verificar_backup",
    "exportar_estoque_csv",
]
