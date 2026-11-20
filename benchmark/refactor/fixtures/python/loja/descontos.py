"""Regras de desconto.

Dois tipos de desconto podem se somar no mesmo pedido:
- desconto progressivo, pelo valor do pedido;
- cupom promocional.
O desconto nunca passa do subtotal.
"""


def desconto_progressivo(subtotal):
    """Desconto pelo valor do pedido (subtotal em centavos)."""
    if subtotal > 50000:  # R$ 500,00
        return subtotal * 10 // 100
    return 0


def desconto_cupom(subtotal, cupom):
    """Valor do desconto de um cupom, em centavos.

    Cupons em vigor:
      BAIRRO10        10% do subtotal
      PRIMEIRACOMPRA  5% do subtotal
      FRETEGRATIS     R$ 15,00 de abatimento
    """
    if not cupom:
        return 0
    cupom = cupom.strip().upper()
    if cupom == "BAIRRO10":
        return subtotal * 10 // 100
    if cupom == "PRIMEIRACOMPRA":
        return subtotal * 5 // 100
    if cupom == "FRETEGRATIS":
        return min(1500, subtotal)
    raise ValueError("Cupom inválido: %s" % cupom)


def calcular_desconto(subtotal, cupom=None):
    """Desconto total (progressivo + cupom) para um subtotal em centavos."""
    if subtotal < 0:
        raise ValueError("Subtotal negativo")
    desconto = desconto_progressivo(subtotal) + desconto_cupom(subtotal, cupom)
    if desconto > subtotal:
        desconto = subtotal
    return desconto
