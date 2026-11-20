# Benchmark de refatoração (parcial): código existente, com e sem a skill

[English](BENCHMARK-REFACTOR.md) · [Español](BENCHMARK-REFACTOR.es.md) · [Primeiro benchmark: app novo](BENCHMARK.pt-BR.md)

Rodado em 20/11/2026 com a versão 2.2.0 da skill, Claude Code 2.1.329, modelo `sonnet`, no Windows 11. **Esta rodada é parcial:** 26 de 36 execuções são válidas, e em nenhuma das válidas a skill chegou a trabalhar. Abaixo está o que as execuções válidas mostram e por que o resto falta.

## Resumo

- **A skill nunca foi acionada nos pedidos de revisão e de correção.** Ela estava instalada na condição "com skill", e a descrição dela cita "bug fix" e "security review", mas nas 12 execuções o modelo respondeu sem chamá-la. Então essas duas tarefas comparam o modelo com ele mesmo, e as diferenças entre as condições são ruído.
- **As refatorações com a skill não são válidas.** O modo refatoração da skill para e pede "pode" antes de começar. O script deveria responder a isso, mas só reconhecia perguntas terminadas em "?", e a mensagem da skill pede sem ponto de interrogação. As 6 refatorações com a skill pararam na mensagem inicial. O script foi corrigido; as execuções não foram refeitas, por decisão do dono do projeto, para limitar o gasto.
- **Nenhuma das três hipóteses de [METRICS.md](../benchmark/refactor/METRICS.md) pôde ser testada.**

O achado que importa para quem usa a skill: **numa revisão ou numa correção pequena, instalar não basta; é preciso pedir a skill** (por exemplo: "use a skill principal-secops-dev-token-optimizer"). Um pedido de refatoração do projeto inteiro aciona a skill (6 de 6).

## Como foi montado

Um sistema de retaguarda de uma loja pequena ("Loja do Bairro"), escrito com pressa, com cerca de 2.700 linhas de código, em Python e em Node.js. Cada versão tem as mesmas 8 falhas de segurança, 4 problemas de qualidade e 1 bug, plantados sem comentário que aponte para eles. Três pedidos, escritos como um dono de loja escreveria:

1. **Revisão:** "Revise o código deste projeto e me diga quais problemas ele tem, do mais grave para o menos grave. Não altere nenhum arquivo."
2. **Correção:** "Um cliente fez um pedido de exatamente R$ 500,00 e não recebeu o desconto de 10% que a regra da loja promete. Corrija isso."
3. **Refatoração:** "Refatore este projeto inteiro para ficar mais fácil de manter, sem mudar o comportamento. O projeto já está no Git, com a árvore limpa."

Testes ocultos, que o agente nunca vê, conferem a correção e se a API pública continua igual. A skill é carregada de uma cópia que só contém o plugin, para nenhuma das condições alcançar o gabarito. Projetos, testes ocultos, gabarito e validador: [benchmark/refactor/](../benchmark/refactor/).

## Resultados válidos

Médias por célula. "Comportamento preservado" significa que os testes ocultos de contrato e os testes originais do projeto passam no código que o agente deixou.

| Tarefa | Linguagem | Condição (skill chamada?) | Execuções | Tempo (s) | Tokens de saída | Custo (US$) | Arquivos / linhas alterados | Correção certa | Comportamento preservado |
|---|---|---|---|---|---|---|---|---|---|
| Correção | Python | sem | 3 | 17 | 1.542 | 0,08 | 1,3 / 5 | 3/3 | 3/3 |
| Correção | Python | com (não chamada) | 2 | 19 | 2.000 | 0,08 | 2 / 11 | 2/2 | 2/2 |
| Correção | Node.js | sem | 3 | 11 | 867 | 0,07 | 1 / 2 | 3/3 | 3/3 |
| Correção | Node.js | com (não chamada) | 3 | 16 | 1.652 | 0,08 | 1,7 / 11 | 3/3 | 3/3 |
| Revisão | Python | sem | 2 | 91 | 11.879 | 0,41 | 0 | n/a | 2/2 |
| Revisão | Python | com (não chamada) | 2 | 83 | 10.348 | 0,38 | 0 | n/a | 2/2 |
| Revisão | Node.js | sem | 3 | 54 | 6.162 | 0,36 | 0 | n/a | 3/3 |
| Revisão | Node.js | com (não chamada) | 2 | 82 | 10.493 | 0,45 | 0 | n/a | 2/2 |
| Refatoração | Python | sem | 3 | 238 | 36.034 | 1,26 | 7,7 / 318 | n/a | 3/3 |
| Refatoração | Node.js | sem | 3 | 575 | 87.645 | 2,91 | 17,3 / 1.865 | n/a | 3/3 |

O que as execuções válidas mostram, independentemente da skill:

- **O bug é fácil de corrigir só com o modelo.** As 11 execuções de correção acertaram, em 10 a 20 segundos e por menos de US$ 0,10, mexendo em um ou dois arquivos.
- **A refatoração sem a skill preservou o comportamento em 6 de 6 execuções**, a US$ 1,26 (Python) e US$ 2,91 (Node.js) por execução. Numa das execuções em Node.js, ela também corrigiu o limite de R$ 500,00 sem que isso fosse pedido, o que muda um comportamento que o README diz estar errado.
- **As respostas de revisão não foram avaliadas.** Como a skill não foi chamada em nenhuma delas, uma avaliação às cegas compararia o modelo com ele mesmo.

## Execuções excluídas

Dez execuções ficaram separadas, sem ser apagadas:

- As 6 refatorações com a skill, paradas na mensagem inicial da skill (defeito do script, descrito acima).
- 4 execuções de revisão e correção em que o script respondeu "pode seguir" a uma oferta como "quer que eu corrija?". Numa revisão que pedia para não alterar arquivos, essa resposta autorizou alterações. Agora o script só responde na tarefa de refatoração.

## Custo

US$ 22,16 no total, contando as execuções excluídas.

## Próximo passo

Para medir a própria skill em código existente, ou o pedido cita a skill, nas duas condições, ou a descrição da skill muda para que uma revisão ou correção a acione sozinha. Nos dois casos, o script já lida com o "pode" do modo refatoração. Para reproduzir:

```
python benchmark/refactor/validate.py
python benchmark/run_benchmark.py --suite refactor --config-dir cfg --out ../bench-refactor --reps 3 --jobs 3 --timeout 2400
python benchmark/analyze_refactor.py --runs ../bench-refactor
```

Valem os mesmos avisos do [primeiro benchmark](BENCHMARK.pt-BR.md#como-reproduzir): gasta tokens no login copiado e deve rodar numa sandbox.
