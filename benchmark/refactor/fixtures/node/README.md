# Loja do Bairro

Sistema de retaguarda da Loja do Bairro: cadastro de clientes e produtos, controle de estoque, pedidos de venda, usuários e relatórios. É uma biblioteca em Node.js com uma linha de comando simples. Os dados ficam num arquivo SQLite.

## Requisitos

- Node.js 22.5 ou mais novo (usa o módulo `node:sqlite`, que já vem com o Node).
- Nenhuma dependência externa. Não precisa de `npm install`.

## Como rodar os testes

```
npm test
```

ou, sem npm:

```
node --test tests/
```

Os testes usam banco em memória ou um arquivo temporário; não mexem no `loja.db`.

## Linha de comando

```
node cli.js [--db arquivo.db] <comando> [argumentos]
```

Sem `--db`, usa a variável de ambiente `LOJA_DB` ou o arquivo `loja.db` na pasta atual. `node cli.js ajuda` lista os comandos. Em caso de erro, a mensagem sai no stderr como `Erro: <mensagem>` e o código de saída é 1.

Principais comandos e o que eles imprimem:

| Comando | Saída |
|---|---|
| `init` | `Banco pronto.` |
| `cliente:novo <nome> <cpf> [email] [telefone]` | `Cliente #<id> cadastrado: <nome>` |
| `clientes [busca]` | uma linha por cliente: `#<id> \| <nome> \| <cpf> \| <email ou -> \| <telefone ou ->`; sem resultado: `Nenhum cliente encontrado.` |
| `produto:novo <sku> <nome> <preco> [estoque]` | `Produto #<id> cadastrado: <SKU> <nome> R$ <preco>` |
| `produtos [busca]` | uma linha por produto: `#<id> \| <SKU> \| <nome> \| R$ <preco> \| estoque <n>` |
| `estoque:entrada <produtoId ou sku> <qtd>` | `Estoque de <SKU>: <n>` |
| `usuario:novo <login> <nome> <senha> <papel>` | `Usuario <login> criado (<papel>).` |
| `pedido:novo <usuarioId> <clienteId> <produtoId:qtd>... [--cupom CODIGO]` | `Pedido #<id> criado. Subtotal: R$ x \| Desconto: R$ y \| Total: R$ z` |
| `pedido:pagar <pedidoId> <forma>` | `Pedido #<id> pago (<forma>).` |
| `vendas <inicio> <fim>` | cinco linhas: `Periodo: <inicio> a <fim>`, `Pedidos: <n>`, `Descontos: R$ ...`, `Total: R$ ...`, `Ticket medio: R$ ...` |
| `exportar:clientes` | CSV dos clientes (sem BOM) |

Há também comandos para ver a ficha do cliente, recibo, cancelamento, orçamento, resumo do mês, curva ABC e outros; veja `node cli.js ajuda`.

Preço na linha de comando é em reais (`12,50`, `12.50` ou `12`). Datas em `DD/MM/AAAA`.

## Uso como biblioteca

```js
const loja = require('./index');
const db = loja.abrirBanco('loja.db');
const cli = loja.criarCliente(db, { nome: 'Maria da Silva', cpf: '529.982.247-25' });
```

Tudo que é público sai do `index.js`. As funções recebem o banco aberto como primeiro argumento e devolvem objetos simples. Valores em dinheiro são sempre **inteiros em centavos** (R$ 12,50 = `1250`).

## Regras de negócio

### Clientes
- CPF obrigatório e válido (dígitos verificadores). Não pode haver dois clientes com o mesmo CPF.
- E-mail, telefone e CEP são opcionais; quando informados, precisam ser válidos.
- Cliente com pedido não pode ser removido.

### Produtos e estoque
- SKU único, gravado em maiúsculas. Preço maior que zero.
- O estoque nunca fica negativo.
- Toda alteração de quantidade (entrada, saída, venda, devolução, ajuste de inventário) fica registrada nos movimentos de estoque.
- Produto removido é apenas desativado, para não perder o histórico.
- Estoque baixo: produto ativo com quantidade igual ou menor que o estoque mínimo dele (padrão 5).

### Pedidos
- O pedido precisa de cliente, usuário ativo e pelo menos um item. Itens repetidos do mesmo produto são somados.
- Não é possível vender mais do que há em estoque. Ao criar o pedido, o estoque é baixado.
- Pedidos a partir de R$ 500,00 têm 10% de desconto.
- Cupons:
  - `BAIRRO10`: 10% de desconto.
  - `PRIMEIRA`: 15% de desconto, só na primeira compra do cliente.
- Cupom e desconto por valor não se acumulam: vale o maior.
- O orçamento (`calcularOrcamento`) usa as mesmas regras de desconto, mas não grava nada nem mexe no estoque.
- Status do pedido: `aberto`, `pago` ou `cancelado`. Formas de pagamento: `dinheiro`, `pix`, `cartao_credito`, `cartao_debito`.
- Ao cancelar, os itens voltam para o estoque. Pedido pago também pode ser cancelado (o estorno é feito no caixa).

### Usuários e acesso
- Papéis: `admin` (dono e gerente) e `vendedor`.
- Senha com pelo menos 6 caracteres.
- A sessão dura 8 horas. Trocar a senha encerra as sessões abertas.
- Vendedores só veem os próprios pedidos; o admin vê os pedidos da loja inteira e é quem cancela pedidos de outros vendedores.

### Relatórios
- Pedidos cancelados não entram nos totais de venda.
- Períodos são inclusivos (do primeiro dia 00:00 ao último dia 23:59).
- A lista de pedidos (`relatorioPedidos`) pode ser ordenada por `criado_em`, `total`, `cliente`, `vendedor` ou `status`, em ordem `asc` ou `desc`.
- Os CSV usam `;` como separador e CRLF, para abrir direto no Excel em português.

## Estrutura

```
index.js        exportações públicas
cli.js          linha de comando
src/            módulos (clientes, produtos, estoque, pedidos, usuários, relatórios...)
src/util/       datas, dinheiro, documentos, CSV
tests/          testes (node:test)
```
