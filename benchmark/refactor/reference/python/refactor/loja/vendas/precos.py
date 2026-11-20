"""Regras de preço e desconto, num lugar só.

Dois tipos de desconto podem se somar no mesmo pedido:
- desconto progressivo, pelo valor do pedido;
- cupom promocional.
O desconto nunca passa do subtotal.
"""
from ..infra import config

LIMITE_DESCONTO_PROGRESSIVO = 50000  # R$ 500,00
PERCENTUAL_PROGRESSIVO = 10

# código -> (tipo, valor). "percentual" é % do subtotal; "fixo" é centavos.
CUPONS = {
    "BAIRRO10": ("percentual", 10),
    "PRIMEIRACOMPRA": ("percentual", 5),
    "FRETEGRATIS": ("fixo", 1500),
}
CUPOM_PRIMEIRA_COMPRA = "PRIMEIRACOMPRA"


def normalizar_cupom(cupom):
    """Código do cupom em maiúsculas, ou None. ValueError se não existir."""
    if not cupom:
        return None
    codigo = cupom.strip().upper()
    if codigo not in CUPONS:
        raise ValueError("Cupom inválido: %s" % cupom)
    return codigo


def desconto_progressivo(subtotal):
    """Desconto pelo valor do pedido (subtotal em centavos)."""
    if subtotal > LIMITE_DESCONTO_PROGRESSIVO:
        return subtotal * PERCENTUAL_PROGRESSIVO // 100
    return 0


def desconto_cupom(subtotal, cupom):
    codigo = normalizar_cupom(cupom)
    if codigo is None:
        return 0
    tipo, valor = CUPONS[codigo]
    if tipo == "percentual":
        return subtotal * valor // 100
    return min(valor, subtotal)


def calcular_desconto(subtotal, cupom=None):
    """Desconto total (progressivo + cupom) para um subtotal em centavos."""
    if subtotal < 0:
        raise ValueError("Subtotal negativo")
    return min(desconto_progressivo(subtotal) + desconto_cupom(subtotal, cupom), subtotal)


def conferir_cupom_do_cliente(conn, cliente_id, cupom):
    """Regras de cupom que dependem do histórico do cliente."""
    if normalizar_cupom(cupom) != CUPOM_PRIMEIRA_COMPRA:
        return
    anteriores = conn.execute(
        "SELECT COUNT(*) FROM pedidos WHERE cliente_id = ? AND status != ?",
        (cliente_id, config.STATUS_CANCELADO),
    ).fetchone()[0]
    if anteriores:
        raise ValueError("Cupom PRIMEIRACOMPRA vale só na primeira compra")
