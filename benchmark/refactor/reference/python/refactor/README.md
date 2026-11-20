# Loja do Bairro

Sistema de retaguarda da Loja do Bairro: cadastro de clientes, produtos e
fornecedores, controle de estoque, pedidos de venda, caixa do balcão,
entregas e relatórios. Biblioteca Python (`loja/`) com uma linha de comando
(`cli.py`). Os dados ficam num arquivo SQLite.

## Requisitos

- Python 3.10 ou mais novo.
- Nenhuma dependência externa: só a biblioteca padrão.

## Uso rápido

```
python cli.py --db loja.db init
python cli.py usuario-add ana --senha abacaxi1 --papel admin
python cli.py cliente-add --nome "Maria Souza" --cpf 529.982.247-25 --email maria@email.com
python cli.py produto-add --codigo CAF-500 --nome "Café 500g" --preco 18,90 --estoque 40
python cli.py pedido-add --usuario ana --senha abacaxi1 --cliente 1 --item 1:2
python cli.py pedido-ver 1 --usuario ana --senha abacaxi1
python cli.py pagar 1 --forma pix
```

`python cli.py --help` lista os comandos. Sem `--db`, o banco usado é `loja.db`
ou o caminho da variável de ambiente `LOJA_DB`.

Como biblioteca:

```python
import loja

conn = loja.conectar("loja.db")
cliente_id = loja.cadastrar_cliente(conn, "Maria Souza", "529.982.247-25", "maria@email.com")
```

As funções públicas estão listadas em `loja/__init__.py`.

## Regras de negócio

- Valores em dinheiro são inteiros em centavos (R$ 18,90 = `1890`). A
  formatação para "R$ 1.234,56" só acontece na exibição.
- CPF de cliente precisa ser válido e não pode repetir. E-mail é obrigatório.
- Pedidos a partir de R$ 500,00 têm 10% de desconto.
- Cupons aceitos: `BAIRRO10` (10% do subtotal), `PRIMEIRACOMPRA` (5%, só na
  primeira compra do cliente) e `FRETEGRATIS` (R$ 15,00 de abatimento). O
  desconto do cupom soma com o desconto por valor, e o desconto total nunca
  passa do subtotal.
- O estoque baixa quando o pedido é criado. Pedido cancelado devolve os itens
  ao estoque. Pedido cancelado não pode ser pago.
- Produto com saldo igual ou menor que o estoque mínimo aparece na lista de
  estoque baixo.
- Usuários têm papel `admin` ou `vendedor`. Vendedores só veem os próprios
  pedidos; o admin vê e cancela qualquer pedido.
- A sessão aberta no login vale por 8 horas.
- Entregas: só nas faixas de CEP atendidas; pedidos a partir de R$ 200,00 não
  pagam taxa de entrega. No máximo 20 entregas por dia.
- O caixa fecha comparando o dinheiro contado com o fundo de troco mais as
  vendas em dinheiro, suprimentos e sangrias.

## Exportação e importação

- `exportar-clientes arquivo.csv` gera planilha com ponto e vírgula, que abre
  direto no Excel.
- `importar-clientes arquivo.csv` lê planilha com as colunas `nome`, `cpf`,
  `email` e, opcionalmente, `telefone` e `cep`. CPF já cadastrado é ignorado.

## Testes

Na pasta do projeto:

```
python -m unittest discover -s tests -t .
```

Os testes usam bancos temporários e não mexem no `loja.db`.
