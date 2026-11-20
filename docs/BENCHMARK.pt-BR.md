# Benchmark: com e sem a skill

[English](BENCHMARK.md) · [Español](BENCHMARK.es.md)

Medido em 20/11/2026 com a versão 2.2.0 da skill, Claude Code 2.1.329, modelo `sonnet`, no Windows 11. São 6 linguagens × 2 condições × 3 repetições = 36 execuções.

## Resumo

- **Segurança:** numa revisão às cegas, o app feito com a skill foi o mais seguro nas 6 linguagens. Nenhuma das condições gerou vulnerabilidade de gravidade alta, e todos os apps usaram SQL parametrizado. A diferença está na segunda camada: hash de senha com custo atual, bloqueio de login que sobrevive a reiniciar o programa, mensagens de erro genéricas e instruções de backup e recuperação.
- **Custo:** com a skill, cada pedido ficou cerca de 3 vezes mais caro e 2,5 vezes mais lento. As médias foram US$ 0,58 contra 0,20 por app, e 176 s contra 69 s. A skill também escreveu cerca do dobro de código.
- **Funcionar como entregue:** sem a skill, 18 de 18 apps compilaram. Com a skill, 16 de 18 compilaram, e um app em PHP não conseguia criar o primeiro usuário.

Para um app pequeno feito do zero, a skill troca tokens e tempo por um resultado mais seguro e mais bem documentado. A economia de tokens do nome da skill vem das regras de leitura, resposta e refatoração: não repetir, não colar arquivos inteiros, ler uma seção em vez do arquivo todo. Este benchmark não mede essa economia; ele mede um app completo por execução.

## O pedido

O mesmo texto em todas as execuções. `{lang}` foi PHP, Python, JavaScript com Node.js, Java, C# com .NET ou Go:

> Preciso de um sistema simples em {lang} para cadastrar meus contatos (nome, e-mail e telefone), com login de usuário e senha, salvando num banco SQLite. Vai rodar só no meu computador com Windows, é tudo do zero, só eu vou usar, e guarda dado pessoal (nome, e-mail e telefone). Crie os arquivos nesta pasta e me diga como rodar. Não sou programador.

As perguntas que a skill normalmente faz antes de um projeto novo já estão respondidas no texto. Assim, as duas condições conseguem entregar numa única rodada, sem interação.

## Resultados por linguagem

Médias de 3 execuções. "Linhas de código" conta as linhas de código-fonte sem linhas em branco nem comentários.

| Linguagem | Tempo (s) sem / com | Tokens de saída sem / com | Custo (US$) sem / com | Linhas de código sem / com | Compilou sem / com |
|---|---|---|---|---|---|
| PHP | 62 / 155 | 10.195 / 22.218 | 0,18 / 0,48 | 303 / 483 | 3/3 / 3/3 |
| Python | 44 / 171 | 6.575 / 23.962 | 0,13 / 0,56 | 198 / 544 | 3/3 / 3/3 |
| Node.js | 63 / 172 | 9.778 / 25.715 | 0,18 / 0,56 | 209 / 597 | 3/3 / 3/3 |
| Java | 93 / 165 | 14.920 / 24.824 | 0,25 / 0,56 | 404 / 624 | 3/3 / 2/3 |
| C# | 60 / 201 | 10.620 / 29.748 | 0,19 / 0,65 | 249 / 678 | 3/3 / 3/3 |
| Go | 93 / 193 | 15.052 / 30.584 | 0,25 / 0,64 | 490 / 767 | 3/3 / 2/3 |
| **Média** | **69 / 176** | **11.190 / 26.175** | **0,20 / 0,58** | **309 / 616** | **18/18 / 16/18** |

O total de tokens de entrada (contando leituras de cache) ficou em média em 141 mil sem a skill e 734 mil com ela; as rodadas de conversa, em 10 e 34. A skill lê o arquivo de roteamento e de três a cinco referências antes de escrever, e grava mais arquivos (15 em média, contra 5).

As duas falhas de compilação com a skill: uma execução em Go não criou o `go.mod`, e uma em Java usou uma classe do driver do SQLite sem importá-la.

## Segurança

**Checagens estáticas.** O scanner da própria skill (`revisar_codigo.py`) só encontrou achados HIGH em Node.js: em média 0,7 por app sem a skill e 0,3 com ela. O Semgrep (`p/default`, versão 1.186) encontrou quantidades parecidas nas duas condições, quase todas avisos em handlers web de Go.

**Revisão às cegas.** Na repetição 1 de cada linguagem, dois agentes revisores receberam o par como `A` e `B`, em ordem sorteada, e deram nota de 0 a 2 em 10 critérios lendo o código. As notas completas, com os defeitos encontrados em cada lado, estão em [benchmark/results/blind_review.md](../benchmark/results/blind_review.md).

| Linguagem | Sem skill | Com skill |
|---|---|---|
| PHP | 18/20 (segurança 14/16) | 16/20 (segurança 16/16) |
| Python | 10/14 | 14/14 |
| Node.js | 17/20 | 18/20 |
| Java | 12/14 | 14/14 |
| C# | 10/14 | 13/14 |
| Go | 19/20 | 20/20 |

Apps de desktop e de console valem 14 pontos, porque sessão, CSRF e XSS não se aplicam a eles. O PHP com a skill teve nota geral menor porque não funciona como entregue: o atalho de início chama um script que nunca foi gravado.

**Checagens de entrega** nos 18 apps de cada condição (checagem de arquivos e palavras-chave, não uma revisão):

| Checagem | Sem skill | Com skill |
|---|---|---|
| README ou instruções de uso | 6/18 | 18/18 |
| `.gitignore` | 0/18 | 17/18 |
| Testes automatizados | 0/18 | 3/18 |
| Hash de senha forte (Argon2id, bcrypt, scrypt ou PBKDF2) | 18/18 | 18/18 |
| Limite de tentativas de login | 18/18 | 18/18 |

## Método

- **Isolamento.** Cada execução usa um `CLAUDE_CONFIG_DIR` próprio, com só uma cópia do login, `--strict-mcp-config` e nenhum plugin. A exceção é a condição com skill, que recebe `--plugin-dir` apontando para este repositório. `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` impede que skills enviadas ao claude.ai sejam sincronizadas na execução. Sem isso, uma cópia antiga desta skill, vinda da conta, era carregada na condição "sem skill". A primeira rodada completa ficou contaminada assim e foi descartada. O `run.json` registra as skills vistas e chamadas, e o `analyze.py` marca qualquer execução sem skill que tenha chamado a skill. Nenhuma chamou na rodada publicada.
- **Caminhos curtos do Windows.** O Claude Code pede aprovação antes de gravar num caminho com `~` (por exemplo `C:\Users\NOME~1`), e uma execução sem interação nunca consegue aprovar. O script expande os nomes curtos; uma rodada anterior a essa correção deixou vazias as pastas de Node.js com a skill.
- **Permissões.** As duas condições tiveram a mesma lista de ferramentas: arquivos, busca na web, leitura de páginas, o interpretador Python e as checagens de versão e sintaxe de cada linguagem. Instalar pacotes não era permitido, para a checagem de compilação continuar comparável. Os números acima foram medidos no commit `b723084`, cuja lista também liberava `curl` e leitura de qualquer página. O script atual restringe a rede às fontes de versão e passa um ambiente filtrado.
- **Checagem de compilação.** Roda depois da sessão, sobre os arquivos que ela deixou: `php -l`, `python -m compileall`, `node --check`, `mvn package` (ou `javac` quando não há `pom.xml`), `dotnet build` e `go mod tidy && go build`. A etapa de análise baixa as dependências declaradas; a sessão não podia. Ferramentas: PHP 8.5.12, Go 1.27.4, .NET SDK 10.0.404, Temurin JDK 25.0.5 e Maven 3.9.16.
- **Limites.** Três repetições por célula é uma amostra pequena: tempo e tokens variam até 2 vezes entre repetições da mesma célula. É um pedido, um modelo e uma máquina. A revisão às cegas cobre uma repetição por linguagem e foi feita por modelos, não por pessoas. Linhas de código medem tamanho, não qualidade.

## Como reproduzir

Rodar o benchmark gasta tokens de verdade na conta cujo login você copiar: cerca de US$ 14 nas 36 execuções, pelos preços da data acima. Rode numa máquina virtual ou sandbox: os interpretadores continuam liberados para testar os apps gerados, e eles podem abrir conexões de rede.

```
# 1. configuração limpa, só com o login
mkdir cfg && cp ~/.claude/.credentials.json cfg/

# 2. execuções (fora do repositório; no Windows, num caminho sem "~")
python benchmark/run_benchmark.py --config-dir cfg --out ../bench --reps 3 --jobs 3

# 3. análise (precisa, no PATH, das ferramentas das linguagens medidas e do semgrep)
python benchmark/analyze.py --runs ../bench --results benchmark/results

# 4. apague a cópia do login
rm cfg/.credentials.json
```

`benchmark/results/` guarda a rodada publicada: `runs.json` (uma entrada por execução), `summary.json` (médias por linguagem e condição), `quality.json` (checagens de entrega) e `blind_review.md`.
