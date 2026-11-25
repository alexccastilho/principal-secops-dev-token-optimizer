# Benchmark da 2.3.0 (parcial): sem a skill, 2.2.1 e 2.3.0

[English](BENCHMARK-2.3.md) · [Español](BENCHMARK-2.3.es.md) · [Primeiro benchmark](BENCHMARK.pt-BR.md) · [Benchmark de refatoração](BENCHMARK-REFACTOR.pt-BR.md)

Rodado em 2026-11-25 com o Claude Code 2.1.332, o modelo `sonnet` (`claude-sonnet-5-5`), no Windows 11, na configuração isolada do `benchmark/run_benchmark.py`. Três condições: sem a skill, versão 2.2.1 e versão 2.3.0. A 2.3.0 foi medida a partir dos arquivos do branch `v2.3` antes do primeiro commit, então as execuções registram o commit base com `-dirty`. **Esta rodada é parcial:** três linguagens em vez de seis, duas ou três repetições por célula e um modelo só. Os resumos brutos, as notas cegas e os mapas de rótulos estão em [benchmark/results/2.3.0/](../benchmark/results/2.3.0/).

## Versão curta

- **Ativação:** a 2.3.0 carregou em todo tipo de pedido de código testado e em nenhum pedido que não era de código. A 2.2.1 nunca carregou para corrigir bug num projeto existente, criar um campo, criar uma tabela, atualizar dependências ou escrever testes.
- **Custo:** com a skill funcionando nas duas, a 2.3.0 não ficou mais cara que a 2.2.1 (US$ 1,61 contra 1,73 nos três apps, 0,75 contra 0,81 nas duas revisões), diferença dentro do ruído de duas ou três repetições. Uma correção de bug pequena passou a custar US$ 0,10 em vez de 0,06, porque agora a skill carrega; na 2.2.1 ela não carregava, então aquela execução era o modelo sozinho.
- **Qualidade:** nas avaliações cegas, os apps da 2.3.0 foram tão seguros quanto os da 2.2.1 ou mais, e mais fáceis de rodar para quem não programa. As revisões da 2.3.0 acharam tantos problemas plantados quanto as outras, sem nenhuma alegação falsa.
- **Não verificado:** o C# não pôde ser compilado (não há SDK do .NET na máquina de teste) em nenhuma condição. Um app Node.js da 2.3.0 foi entregue sem os dois pacotes declarados no `package.json`.

## Ativação

Dez pedidos que devem carregar a skill e quatro que não devem, em projetos Python e Node.js, duas repetições cada (4 execuções por pedido). O critério do portão 5 foi registrado antes das execuções da 2.3.0 (`gate5-preregistro.md` na pasta de resultados).

| Pedido | Sem skill | 2.2.1 | 2.3.0 |
|---|---|---|---|
| a01 revise o código, problema mais grave | 0/4 | 4/4 | 4/4 |
| a02 tem problema de segurança? | 0/4 | 4/4 | 4/4 |
| a03 total do pedido errado com desconto, corrija | 0/4 | 4/4 | 4/4 |
| a04 erro ao cadastrar cliente sem telefone | 0/4 | 2/4 | 4/4 |
| a05 adicione um campo de CPF | 0/4 | 0/4 | 4/4 |
| a06 é seguro colocar na internet? | 0/4 | 4/4 | 4/4 |
| a07 atualize as dependências | 0/4 | 0/4 | 4/4 |
| a08 crie uma tabela de fornecedores | 0/4 | 0/4 | 4/4 |
| a09 relatório de vendas lento | 0/4 | 4/4 | 4/4 |
| a10 escreva testes para o desconto | 0/4 | 0/4 | 3/4 |
| n01 a n04 (LGPD, e-mail, capital, tradução) | 0/16 | 0/16 | 0/16 |
| Suíte de refatoração: revisão | 0/6 | 6/6 | 6/6 |
| Suíte de refatoração: bugfix | 0/6 | 0/6 | 6/6 |

A descrição da 2.3.0 foi escolhida num piloto pequeno na tarefa de bugfix antes desta rodada: o primeiro rascunho carregou em 0 de 4 bugfixes e o texto final ("carregue antes da primeira edição de qualquer arquivo de código, mesmo numa correção de uma linha") em 4 de 4.

## App novo (contatos com login e SQLite)

Duas repetições por linguagem. A primeira rodada da 2.3.0 perdeu em entrega na avaliação cega: os apps pediam que o usuário digitasse comandos num terminal. A regra de entrega proporcional foi mudada para que quem não programa sempre receba um atalho de dois cliques e os pré-requisitos com o link, e os apps da 2.3.0 foram feitos de novo. A tabela mostra essa segunda rodada.

| Linguagem | Condição | Custo (US$) | Tokens de saída | Escrita em cache | Leitura de cache | Turnos | Tempo (s) |
|---|---|---|---|---|---|---|---|
| Python | sem skill | 0,123 | 6.599 | 12.540 | 69.268 | 5 | 47 |
| Python | 2.2.1 | 0,488 | 21.069 | 51.769 | 699.964 | 30,5 | 163 |
| Python | 2.3.0 | 0,440 | 18.458 | 47.462 | 659.290 | 35 | 135 |
| Node.js | sem skill | 0,262 | 14.842 | 21.289 | 286.184 | 14,5 | 93 |
| Node.js | 2.2.1 | 0,582 | 26.687 | 59.248 | 781.052 | 37 | 174 |
| Node.js | 2.3.0 | 0,553 | 26.655 | 54.129 | 695.806 | 43 | 172 |
| C# | sem skill | 0,257 | 15.280 | 22.648 | 137.148 | 17,5 | 89 |
| C# | 2.2.1 | 0,655 | 31.094 | 71.730 | 557.400 | 35,5 | 199 |
| C# | 2.3.0 | 0,621 | 31.828 | 60.784 | 598.422 | 45,5 | 199 |

Total dos três apps: US$ 1,614 com a 2.3.0, contra 1,725 com a 2.2.1 e 0,642 sem a skill. Com duas repetições isso é do tamanho do ruído: na primeira rodada da 2.3.0, o Python custou 6% a mais que a 2.2.1 e o C# 24% a menos. A 2.3.0 faz mais turnos (consulta versões na hora e compila antes de entregar), mas cada turno carrega menos: menos escrita em cache e menos saída no Python.

**Compilação.** Python e Node.js compilaram em todas as execuções de todas as condições. O C# não foi compilado em nenhuma condição: a máquina de teste não tem o SDK do .NET, então isso fica não verificado.

**Roda como entregue.** 11 das 12 execuções da 2.3.0 rodaram o scanner com `--entrega`. A que não rodou foi um app Node.js cujo `npm install` foi bloqueado pela bancada de teste; ele deixou o `package.json` sem `express` e `helmet`. O atalho dele instala os dois, mas um `npm start` numa cópia nova falha. Depois desta rodada entrou uma frase no portão (quando a instalação for bloqueada, escrever a dependência no manifesto à mão); essa frase não foi medida.

**Avaliação cega.** Outro modelo deu nota a um app por linguagem e condição, com rótulos sorteados e sem caminhos que revelassem a condição, em segurança e em entrega para quem não programa (1 a 10). Foram duas rodadas, com dois avaliadores: a primeira com a primeira rodada da 2.3.0, a segunda com os apps refeitos. A segunda rubrica ganhou dois critérios de entrega (nada de digitar num terminal, todo pré-requisito citado) que são as mesmas regras acrescentadas à skill entre as rodadas, então a nota de entrega da rodada 2 é em parte medida contra a própria correção. Os critérios de segurança foram os mesmos nas duas.

| Condição | Segurança, rodada 1 | Entrega, rodada 1 | Segurança, rodada 2 | Entrega, rodada 2 |
|---|---|---|---|---|
| Sem skill | 7,3 | 6,0 | 6,0 | 4,3 |
| 2.2.1 | 8,7 | 7,0 | 8,0 | 6,0 |
| 2.3.0 | 8,7 | 5,7 | 9,0 | 7,7 |

Os mesmos apps sem skill e da 2.2.1 receberam notas diferentes dos dois avaliadores, então compare as condições dentro de cada rodada, não entre rodadas. O único defeito marcado como crítico ficou num app Node.js sem a skill, avaliado nas duas rodadas (configuração inicial sem proteção contra CSRF).

**Scanner.** Nenhum HIGH real em nenhum app. Dois apps Node.js da 2.3.0 dispararam um HIGH em `db.exec(\`PRAGMA user_version = ${n}\`)`, em que o número vem de um nome de arquivo validado: a regra `child-process-exec` confunde o `exec` do SQLite com o do `child_process`. Essa regra é anterior à 2.3.0 e vai ser estreitada depois. O app Node.js que pulou o portão também tem dois achados `sql-template-js` num trecho de `WHERE` constante, com todos os valores passados como parâmetro; também falsos positivos.

## Projeto existente (suíte de refatoração)

O projeto de treino de 2.700 linhas do [benchmark de refatoração](BENCHMARK-REFACTOR.pt-BR.md), três repetições.

| Tarefa | Linguagem | Sem skill | 2.2.1 | 2.3.0 |
|---|---|---|---|---|
| Revisão, custo (US$) | Python | 0,365 | 0,416 | 0,386 |
| Revisão, custo (US$) | Node.js | 0,357 | 0,389 | 0,359 |
| Bugfix, custo (US$) | Python | 0,060 | 0,058 (skill não carregou) | 0,100 |
| Bugfix, custo (US$) | Node.js | 0,058 | 0,058 (skill não carregou) | 0,098 |
| Bugfix resolvido | as duas | 6/6 | 6/6 | 6/6 |

As 18 respostas de revisão foram avaliadas às cegas contra o gabarito (`benchmark/refactor/manifest/`):

| Condição | Problemas plantados achados (média de 13) | Alegações falsas (total) | Problema mais grave apontado certo |
|---|---|---|---|
| Sem skill | 10,8 | 4 | 6/6 |
| 2.2.1 | 11,2 | 2 | 4/6 |
| 2.3.0 | 11,3 | 0 | 6/6 |

O avaliador contou injeção de SQL como a classe mais grave; as duas respostas da 2.2.1 que puseram o hash MD5 em primeiro lugar são as marcadas como erradas.

## Portões para publicar

| Portão | Resultado |
|---|---|
| 1. Testes passam e o ZIP é gerado | Passou: 57 testes |
| 2. Todo app novo compila | **Para o dono decidir.** Python e Node.js compilaram 8 de 8; o C# não pôde ser conferido em nenhuma condição; um app Node.js falha num `npm start` simples |
| 3. Segurança no mínimo igual à da 2.2.1 | Passou nas duas rodadas cegas |
| 4. Custo por entrega que funciona no máximo igual ao da 2.2.1 | **Para o dono decidir.** Não ficou mais caro onde a skill funciona nas duas (app novo, revisão); o bugfix custa US$ 0,04 a mais, o preço de carregar em toda edição, o que a 2.2.1 não fazia |
| 5. Ativação (critério registrado antes) | Passou: bugfix 6/6, pedidos que a 2.2.1 perdia 19/20, sem regressão 26/26, pedidos que não são de código 0/16 |

## Limites

Três linguagens, duas ou três repetições por célula e um modelo: diferença de poucos centavos por app está dentro do ruído. Toda execução tinha só este plugin instalado, então o trabalho junto com outras skills (seção 11) não foi medido. As rodadas de ativação e de revisão usaram o `SKILL.md` antes das duas últimas frases (atalho e instalação bloqueada). O piloto que escolheu a descrição usou a tarefa de bugfix, que também é medida aqui. A regra de entrega proporcional foi corrigida depois da primeira avaliação cega, e só a suíte de criação rodou de novo. A bancada bloqueia instalação de pacotes e servidores rodando, o que é mais restrito que uma sessão real.
