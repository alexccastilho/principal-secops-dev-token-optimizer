"""Entregas em domicílio.

A loja entrega no bairro e arredores. A taxa depende da faixa de CEP;
fora das faixas atendidas a entrega não é aceita. Pedidos acima do
valor de frete grátis não pagam taxa.
"""
import logging
from datetime import datetime, timedelta

from ..comum.formatacao import converter_data, formatar_cep, hoje_iso
from ..comum.validacao import somente_digitos
from ..infra import banco, config

log = logging.getLogger(__name__)

# (cep inicial, cep final, taxa em centavos)
FAIXAS_ENTREGA = [
    ("01300000", "01399999", 500),
    ("01400000", "01499999", 800),
    ("04000000", "04099999", 1200),
    ("05400000", "05499999", 1200),
]
FRETE_GRATIS_A_PARTIR_DE = 20000
ENTREGAS_POR_DIA = 20

STATUS_ENTREGA = ("agendada", "saiu", "entregue", "devolvida")


def taxa_entrega(cep, valor_pedido=0):
    """Taxa de entrega para o CEP, em centavos. ValueError se a região não é atendida."""
    numeros = somente_digitos(cep)
    if len(numeros) != 8:
        raise ValueError("CEP deve ter 8 dígitos")
    for inicio, fim, taxa in FAIXAS_ENTREGA:
        if inicio <= numeros <= fim:
            if valor_pedido >= FRETE_GRATIS_A_PARTIR_DE:
                return 0
            return taxa
    raise ValueError("Não entregamos no CEP %s" % formatar_cep(numeros))


def agendar_entrega(conn, pedido_id, cep, data, endereco=""):
    """Agenda a entrega do pedido para a data (dd/mm/aaaa ou ISO). Devolve o id."""
    pedido = conn.execute(
        "SELECT id, total, status FROM pedidos WHERE id = ?", (pedido_id,)
    ).fetchone()
    if pedido is None:
        raise ValueError("Pedido %s não encontrado" % pedido_id)
    if pedido["status"] == config.STATUS_CANCELADO:
        raise ValueError("Pedido cancelado não pode ser entregue")
    data = converter_data(data)
    if data < hoje_iso():
        raise ValueError("Data de entrega no passado")
    if conn.execute("SELECT 1 FROM entregas WHERE pedido_id = ?", (pedido_id,)).fetchone():
        raise ValueError("Pedido %s já tem entrega agendada" % pedido_id)
    no_dia = conn.execute(
        "SELECT COUNT(*) FROM entregas WHERE data = ? AND status != 'devolvida'", (data,)
    ).fetchone()[0]
    if no_dia >= ENTREGAS_POR_DIA:
        raise ValueError("Agenda de entregas lotada nesse dia")
    taxa = taxa_entrega(cep, pedido["total"])
    cur = conn.execute(
        "INSERT INTO entregas (pedido_id, cep, endereco, data, taxa, status, criado_em)"
        " VALUES (?, ?, ?, ?, ?, 'agendada', ?)",
        (pedido_id, formatar_cep(cep), (endereco or "").strip(), data, taxa, banco.agora()),
    )
    conn.commit()
    log.info("entrega do pedido %s agendada para %s", pedido_id, data)
    return cur.lastrowid


def atualizar_status_entrega(conn, entrega_id, status):
    if status not in STATUS_ENTREGA:
        raise ValueError("Status de entrega inválido: %s" % status)
    cur = conn.execute(
        "UPDATE entregas SET status = ? WHERE id = ?", (status, entrega_id)
    )
    conn.commit()
    return cur.rowcount > 0


def entregas_do_dia(conn, data=None):
    """Entregas agendadas para a data (hoje se não informada), em ordem de CEP."""
    data = hoje_iso() if data is None else converter_data(data)
    linhas = conn.execute(
        "SELECT e.id, e.pedido_id, c.nome AS cliente, c.telefone, e.cep, e.endereco,"
        " e.taxa, e.status"
        " FROM entregas e JOIN pedidos p ON p.id = e.pedido_id"
        " JOIN clientes c ON c.id = p.cliente_id"
        " WHERE e.data = ? ORDER BY e.cep, e.id",
        (data,),
    ).fetchall()
    return banco.linhas_para_dicts(linhas)


def proxima_data_livre(conn, a_partir_de=None):
    """Primeiro dia (a partir de amanhã) com vaga na agenda, pulando domingos."""
    dia = datetime.now().date() + timedelta(days=1)
    if a_partir_de:
        dia = datetime.strptime(converter_data(a_partir_de), config.FORMATO_DATA).date()
    for _ in range(60):
        if dia.weekday() != 6:
            ocupadas = conn.execute(
                "SELECT COUNT(*) FROM entregas WHERE data = ? AND status != 'devolvida'",
                (dia.strftime(config.FORMATO_DATA),),
            ).fetchone()[0]
            if ocupadas < ENTREGAS_POR_DIA:
                return dia.strftime(config.FORMATO_DATA)
        dia += timedelta(days=1)
    raise ValueError("Agenda lotada nos próximos 60 dias")
