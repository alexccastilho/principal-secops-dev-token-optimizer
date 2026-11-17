# Análise e melhoria da skill principal-secops-dev-token-optimizer

Data: 16/11/2026. Escopo: `skills/principal-secops-dev-token-optimizer/` (SKILL.md, 19 referências, scanner, evals). As referências de linha (`arquivo:linha`) apontam para a versão original commitada (`git show HEAD:...`).

## (a) Resumo executivo

A skill é boa no conteúdo: prioridades claras, regras de integridade fortes, referências técnicas corretas na maior parte. Os problemas reais estavam em três lugares.

1. **O scanner, que é o portão de entrega, errava para os dois lados.** Marcava HIGH em código correto (por exemplo `sprintf` em PHP, que o próprio `php.md` recomenda, e `prepare(...)->execute([$a, $id])`), e deixava passar o que mais importa para o público da skill (senha em `'password' => '...'`, `define('DB_PASSWORD', ...)`, `new PDO(..., "root", "senha")`, chave privada PEM, `mongodb+srv://`). Com a regra "só entregue com HIGH zerado", um falso positivo empurra o Claude a reescrever código que funciona, o que fere a prioridade 2 (integridade). Em um corpus de 74 linhas, o scanner original errou 43 e vazou 2 segredos na saída. O novo passa nesse corpus e na versão ampliada de 84 linhas, sem vazar nenhum.
2. **Contradições no SKILL.md.** O teto de 2 referências não comportava o caso mais comum (login em PHP + MySQL pede `php.md`, `mysql.md` e `security-baseline.md`), então economia de tokens vencia segurança. O portão mandava "corrigir todo HIGH" enquanto a seção 6 mandava não corrigir nada fora do pedido sem permissão.
3. **Portabilidade.** O caminho do scanner estava fixo em `~/.claude/skills/...`, que não existe em instalação por plugin nem no claude.ai.

Tudo isso foi corrigido. Também entraram lacunas relevantes para o público brasileiro não programador: WordPress, pagamentos e Pix, Supabase e Firebase, CPF e CNPJ como texto, pasta pública fixa do cPanel, e um bloqueio de `.git/` no `.htaccess` que a versão original prometia e não fazia. O SKILL.md ficou 6,5% menor (16.376 para 15.315 bytes) mesmo com as regras novas.

## (b) Achados por severidade

### Crítico

| # | Onde | Problema | Por que importa | Corrigido |
|---|---|---|---|---|
| C1 | `scripts/revisar_codigo.py:355` | Vazamento de segredo: a omissão do trecho era por regra, não por linha. Uma linha com segredo que também casasse com outra regra (eval, SQL) saía inteira na saída. Reproduzido: `x = eval(tok); password = "hunter2hunter2"` imprimia a senha no achado `eval-js-py`. | O segredo vai para o histórico da conversa. Fere a prioridade 1. | Sim. A omissão agora é propriedade da linha: se qualquer padrão de segredo casa, ou se a linha tem um nome com cara de segredo recebendo um valor (heurística `_HIDE`, mais larga que a detecção: pega senha curta, com espaço ou sem aspas), todos os achados da linha saem com `[trecho omitido]`. Em `.env` e `wp-config.php` nenhum trecho é impresso. Teste no corpus (texto e `--json`). |
| C2 | `scripts/revisar_codigo.py:286,344` | `--` estava na lista de prefixos de comentário para qualquer linguagem. `-----BEGIN RSA PRIVATE KEY-----` começa com `--`, então a regra `chave-privada` nunca casava com uma chave em linha própria. `.pem` e `.key` nem eram lidos. | Falso negativo no pior tipo de segredo. | Sim. `--` só é comentário em `.sql`; `#` só nas linguagens em que é comentário. Regras de formato exato (chave privada, AWS, tokens de serviço, string de conexão) rodam também em comentário e em linha longa. `.pem`, `.key`, `id_rsa` entram na varredura. |
| C3 | `scripts/revisar_codigo.py:208-210, 98-105` | Falsos positivos HIGH em código correto: `sprintf` em PHP e JS (regra de C sem escopo de linguagem); `"Selected: " . $name` e `"Profile updated" . $x` (palavra sem `\b` nem forma de SQL); `prepare("UPDATE t SET a = ? WHERE id = ?")->execute([$a, $id])` (a variável estava fora da string); `{$wpdb->prefix}` do WordPress; `f"postgresql://{user}:{pwd}@{host}"`; `` jQuery(`<li>${x}</li>`) ``; `set_text(f"...")`; `yaml.load` em JS. | Com "HIGH zerado para entregar", cada um desses leva a reescrever código que funciona. | Sim. Cada regra tem escopo por tipo de arquivo, as de SQL exigem a forma do comando e a variável dentro da string, template com tag (`` sql`...` ``) é aceito. |
| C4 | `references/php.md:69-72` | O comentário diz "Block dotfiles (.env, .git)", mas `<FilesMatch>` só enxerga o nome do arquivo. `/.git/config` e `/.git/HEAD` continuavam servidos. | Repositório exposto em hospedagem compartilhada é vazamento de código e de credenciais. O usuário cola o bloco achando que está protegido. | Sim. Acrescentado `RedirectMatch 404 "/\.(?!well-known/)"` dentro de `<IfModule mod_alias.c>`. |

### Alto

| # | Onde | Problema | Por que importa | Corrigido |
|---|---|---|---|---|
| A1 | `SKILL.md:145-147` | Caminho do scanner fixo em `~/.claude/skills/...`. | Quebra em plugin e no claude.ai (`/mnt/skills/user/...`). | Sim. O caminho é montado a partir da pasta de onde o SKILL.md foi carregado (`SKILL_DIR`), com variante `py -3`. O Claude fica na pasta do projeto, sem `cd` para a skill. Mantido o caminho "sem scanner". |
| A2 | `SKILL.md:97` contra `:78`, `:130` | Teto de 2 arquivos, mas login em PHP exige 3 (`php.md`, `mysql.md` pela regra de banco, `security-baseline.md` pela seção 5). A ordem de descarte mandava soltar "o arquivo geral", ou seja, o de segurança. Havia ainda três limites (2, 3, 5) e uma exceção espalhada. | Economia de tokens vencendo segurança, contra a ordem de prioridade. | Sim. Orçamento único: 3 arquivos, 5 para nativo ou GUI; arquivos de fluxo não contam. Ordem de descarte explícita, com o modelo de ameaça em primeiro lugar. |
| A3 | `SKILL.md:152` contra `:138` e `:68` | "Fix every HIGH finding" contra "do not fix it without permission" e "minimal scope". Em projeto legado o scanner sempre acha HIGH antigo. | O Claude sairia corrigindo código fora do pedido, ou travaria a entrega. | Sim. O portão vale para o que foi escrito ou alterado na tarefa. HIGH antigo vira o aviso de uma linha (regra 9 da seção 4). Falso positivo conferido não é "consertado". |
| A4 | `scripts/revisar_codigo.py:81` | Segredos comuns em PHP e JSON não detectados: `'password' => 'x'`, `"password": "x"`, `define('DB_PASSWORD','x')`, `new PDO(dsn, "root", "x")`, `mysqli_connect(...)`, `#define API_KEY "x"`, `mongodb+srv://`, tokens de GitHub, Stripe, Google, Mercado Pago. | É o erro mais frequente do público da skill. | Sim. Regras `secret-atribuido` ampliada, `conexao-php-literal`, `token-de-servico` e `segredo-em-config` (MEDIUM, valores sem aspas em YAML, INI, properties). Filtro de rótulo e de exemplo para não marcar `"password": "Senha"` nem `your_token_here`. |
| A5 | `scripts/revisar_codigo.py:316` | `SKIP_DIRS` era testado contra todas as partes do caminho absoluto. Projeto dentro de uma pasta chamada `build`, `dist`, `target` ou `vendor` resultava em "nenhum arquivo" (saída 2). | Portão inutilizável sem motivo aparente. | Sim. `os.walk` com poda só abaixo da pasta pedida (também deixa de percorrer `node_modules` inteiro). |
| A6 | `scripts/revisar_codigo.py:320, 33-39` | `.env` era marcado HIGH por conter segredo, que é onde a skill manda guardar. `.env.local` e `.env.production` não eram lidos. Arquivo passado pelo nome com extensão fora da lista era ignorado em silêncio. Faltavam `.vue`, `.svelte`, `.phtml`, `.twig`, `.kt`, `.swift`, `.ps1`, `.properties`, `.xml`, `Dockerfile`, `.htaccess`. | Falso positivo permanente e falsos negativos. | Sim. `.env*` e `wp-config.php` são tratados como casa de segredo (regras de segredo não rodam; exemplo `.env.example` continua verificado). Arquivo explícito é sempre lido. Extensões acrescentadas. |
| A7 | `scripts/revisar_codigo.py:378-381` | No console do Windows em cp1252, imprimir um trecho com caractere fora da página de código derrubava o scanner com `UnicodeEncodeError`. Reproduzido no original com `PYTHONIOENCODING=cp1252`. | O portão quebra exatamente na plataforma do público. | Sim. `stdout` e `stderr` reconfigurados para UTF-8 com `errors="replace"`. |
| A8 | `scripts/revisar_codigo.py:334` | Arquivo em UTF-16 (Bloco de Notas, PowerShell antigo) era lido como UTF-8, virava lixo e o resultado era "OK". Linhas acima de 500 caracteres e arquivos acima de 1 MB eram pulados sem aviso. Caminho digitado errado junto com um válido dava saída 0. | "OK" falso. | Sim. BOM UTF-16 tratado, Latin-1 como reserva, binário detectado por NUL. A saída informa o que não foi analisado. Linha longa passa pelas regras de segredo exatas. Caminho ausente sem HIGH devolve 2. |
| A9 | `scripts/revisar_codigo.py:171` | `ini_set('display_errors', '1')` não casava (a aspa ficava entre o nome e a vírgula). `echo $_GET` era só MEDIUM e `<?= $_POST` não era visto. `include($_GET[...])` não tinha regra. SQL com `+` (JS, Python, Java fora de `executeQuery`) e com `%` ou `.format` não tinha regra. | Falsos negativos em falhas clássicas. | Sim. Regras corrigidas ou criadas: `debug-ligado`, `echo-sem-escape` (HIGH), `include-dinamico`, `sql-concat`, `sql-fstring-py` ampliada, linha de continuação de SQL (`WHERE x = '$v'`). |

### Médio

| # | Onde | Problema | Corrigido |
|---|---|---|---|
| M1 | `references/security-baseline.md:4-18` | O sumário lista três seções que não existem (Supply chain hardening, Authentication and session recipes, Logging, alerting and error handling). O Claude procura e não acha. | Sim. Sumário reflete o arquivo. |
| M2 | `references/security-baseline.md:28` | SSRF: só faixas IPv4 e só o IP `169.254.169.254`. Sem IPv6, sem DNS rebinding. | Sim. Uma linha: resolver uma vez e conectar no endereço conferido; faixas IPv4 e IPv6. |
| M3 | `references/security-baseline.md` | Nada sobre pagamento além de "nunca logar cartão". Loja com Pix e cartão é pedido típico do público. | Sim. Seção Payments (4 itens): não tocar em dado de cartão, confirmar só por webhook ou API, assinatura e idempotência, total recalculado no servidor. |
| M4 | `references/php.md` | WordPress só aparecia como uma linha em `projeto-do-zero.md`. | Sim. Seção WordPress (7 itens): tema filho ou plugin, `$wpdb->prepare`, escape, nonce mais `current_user_can`, `permission_callback`, `wp-config.php`, plugins desatualizados. |
| M5 | `references/bancos-outros.md` | Supabase e Firebase ausentes. São o caminho comum de quem monta app sem programar, e o erro típico (tabela sem RLS, regra `if true`, chave `service_role` no navegador) é crítico. | Sim. Uma linha em PostgreSQL e seção Firebase curta. |
| M6 | `references/mysql.md:15-16` | `TIMESTAMP` recomendado sem avisar do limite de 2038. CPF, CNPJ e telefone sem orientação de tipo. O CNPJ alfanumérico começou a ser emitido em 31/07/2026. | Sim, em `mysql.md` e `bancos-outros.md`. |
| M7 | `references/projeto-do-zero.md:80` | O esqueleto presume que dá para apontar a raiz do site para `public/`. Em cPanel comum a pasta é `public_html` e não muda. | Sim. Instrução de onde pôr cada pasta. |
| M8 | `SKILL.md:83, 128, 163` e duas referências | Protocolo de versão repetido em cinco lugares. Ponteiros para `projeto-do-zero.md` e `diagnostico.md` três vezes cada. | Sim. Um bullet curto na seção 5, uma linha na tabela, uma regra de pareamento. |
| M9 | `SKILL.md:167-191` | Checklists de nativo e de GUI no SKILL.md, carregados em toda tarefa web. | Sim. Movidos para o fim de `native-app-security.md` e `gui-desktop.md`, com ponteiro de uma linha. |
| M10 | `SKILL.md:123` e `references/outras-linguagens.md:1, 30-34, 62-63` | A linha da tabela omitia Kotlin, PowerShell e shell, que o arquivo cobre. O arquivo tinha três seções que só apontavam para outro arquivo. | Sim. |
| M11 | `evals/evals.json` | Sem eval para a regra de confiança (instrução injetada em arquivo), para o aviso de crítico fora do escopo, nem para falso positivo. A asserção com `-march=native` fazia o scanner marcar HIGH no próprio `evals.json`. | Sim. Evals 18 a 23. Asserção reescrita. |
| M12 | `scripts/revisar_codigo.py:363-382` | Saída de 5 linhas por achado, repetindo explicação e correção. Achados duplicados na mesma linha (`hash-fraco` com `hash-fraco-senha`). | Sim. Saída agrupada por regra e supressão de regra redundante. |

### Baixo

| # | Onde | Problema | Corrigido |
|---|---|---|---|
| B1 | `SKILL.md:8` | "meu site esta..." sem acento na descrição. | Sim. |
| B2 | `references/security-baseline.md:50` | bcrypt lê só 72 bytes, e a mesma página pede aceitar senhas de 64+ caracteres. | Sim, meia linha. |
| B3 | `references/security-baseline.md:114` | CSP de exemplo sem `form-action`. | Sim. |
| B4 | `references/security-baseline.md:201` | NIST SP 800-63B foi substituída pela 800-63B-4 em julho de 2025. | Sim. |
| B5 | `references/python.md:16` | "passwords resets". | Sim. |
| B6 | `references/versoes-e-fontes.md:10` | Só o endpoint antigo do endoflife.date. Os dois respondem hoje. | Sim, o v1 foi citado como alternativa. |
| B7 | `scripts/revisar_codigo.py:215` | Texto de correção com `%%31s`. | Sim. |
| B8 | `scripts/revisar_codigo.py:85` | `PGP PRIVATE KEY BLOCK` e `ENCRYPTED PRIVATE KEY` não casavam. | Sim. |

## (c) Mudanças por arquivo

**SKILL.md**
- Descrição: acento corrigido, gatilhos em pt-BR ("tá lento", "é seguro publicar?"), WordPress, outros bancos e LGPD. 1.000 caracteres medidos.
- Seção 2: removidos dois ponteiros duplicados.
- Seção 4: o aviso de achado crítico fora do pedido virou a regra 9 (estava solto no fim da seção 6).
- Seção 5: bullet de versões reduzido a três frases.
- Seção 6: orçamento único (3, ou 5 para nativo ou GUI), ordem de descarte com segurança em primeiro, regras de pareamento em quatro bullets, tabela atualizada (WordPress, Supabase, Firebase, Kotlin, PowerShell, shell, linha de versões).
- Seção 7: invocação relativa à pasta da skill, códigos de saída, quatro regras de resultado (seu código, código antigo, falso positivo, scan limpo), checklists de nativo e GUI movidos para as referências.
- Última linha: "Autor: Alex Camacho Castilho".

**scripts/revisar_codigo.py** (reescrito em boa parte, 45 para 52 regras)
- Escopo por tipo de arquivo em cada regra; comentário por linguagem.
- Omissão de segredo por linha; casas de segredo (`.env*`, `wp-config.php`).
- Regras novas: `conexao-php-literal`, `token-de-servico`, `segredo-em-config`, `sql-concat`, `include-dinamico`, `os-system`, `yaml-load`. Regras de SQL, segredo, debug, TLS, JWT, chave privada e echo refeitas.
- Varredura com `os.walk` e poda; arquivo explícito sempre lido; UTF-16, Latin-1 e binário tratados.
- Saída agrupada por regra, UTF-8 forçado, relatório do que não foi analisado, saída 2 para caminho ausente.
- Compatível com Python 3.8: `typing.List/Dict/Optional`, formatação com `%`, sem `match`, sem `X | None`.

**references/**
- `security-baseline.md`: sumário, SSRF, bcrypt 72 bytes, `form-action`, seção Payments, NIST 800-63B-4.
- `php.md`: `.htaccess` bloqueia pastas ocultas; seção WordPress.
- `mysql.md`: limite de 2038 do `TIMESTAMP`; CPF, CNPJ, CEP e telefone como texto.
- `bancos-outros.md`: mesma regra de CPF; Supabase (RLS, `service_role`); seção Firebase.
- `node-js.md`: uma linha sobre Next.js (checagem em Server Action e Route Handler, prefixo `NEXT_PUBLIC_`).
- `native-app-security.md` e `gui-desktop.md`: receberam os checklists que saíram do SKILL.md.
- `outras-linguagens.md`: título corrigido, três seções-ponteiro removidas.
- `projeto-do-zero.md`: nota sobre `public_html` fixo.
- `versoes-e-fontes.md`: "cap" virou "budget"; endpoint v1.
- `python.md`: erro de digitação.

**evals/evals.json**
- 17 para 23 evals. Novos: 18 (instrução injetada em arquivo), 19 (crítico fora do escopo), 20 (falso positivo do scanner), 21 (WordPress), 22 (Pix e webhook), 23 (Supabase).
- Acentuação corrigida em `expected_output` e `assertions`. Os prompts ficaram como estavam, porque imitam a digitação do usuário.
- Eval 1 aceita `PASSWORD_DEFAULT` como reserva (é o que `php.md` manda). Eval 8 exige o sanitizer dentro do CMake (é o que `c-cpp.md` manda). Eval 16 ganhou a asserção de CPF como texto.

## (d) Validação feita

Ambiente: Windows 11, Python 3.12 e 3.15 (`py -3.12`, `py -3`). Não havia Python 3.8 instalado. Os arquivos de teste (corpus e `run_corpus.py`) ficaram em `_scratch/`, apagada no fim como pedido, porque continha segredos falsos.

| Verificação | Comando | Resultado |
|---|---|---|
| Corpus com regra esperada por linha (PHP, Python, JS, JSON, C, YAML, shell, `.env*`, `wp-config.php`, Vue, CMake, SQL) | `py -3.12 run_corpus.py <scanner> py -3.12` | Primeira versão, 74 linhas. Original: 43 falhas e 2 vazamentos (`LEAK Zx9Kq2Lm8`, `LEAK hunter2`). Novo: `fail=0`. Depois de uma revisão ampliei para 84 linhas (senha curta, com espaço, sem aspas em shell, `SECRET_KEY` do Django, senha terminada em `!`, senha só de dígitos); a primeira versão do scanner novo vazava 4 desses valores e deixava de acusar 3 senhas, o que foi corrigido. Final: `cases=84 fail=0 leaks=[]` em texto e em `--json`, em 3.12 e 3.15. |
| Redação por linha (pedido do coordenador) | linhas `x = eval(tok); password = "hunter2hunter2"` e `$x = eval($code); $token = "..."` no corpus | Os dois achados de cada linha saem com `[trecho omitido]`; a busca pelo segredo na saída completa não encontra nada. |
| Sintaxe 3.8 | `ast.parse(fonte, feature_version=(3,8))` | `ast 3.8 ok`. Busca por `removeprefix`, `is_relative_to`, `match`, `:=`, `X \| None`, `list[` em tempo de execução: nada. Isso confere sintaxe e uma lista de APIs, não é execução em 3.8 real. |
| Console cp1252 | `PYTHONIOENCODING=cp1252 PYTHONUTF8=0 py -3.12 <scanner> u.php` (linha com `→`) | Original: `UnicodeEncodeError`. Novo: saída normal, exit 1. |
| Binário, UTF-16, Latin-1, linha longa | arquivos gerados no `_scratch` | Binário: "1 arquivo(s) binario(s)" e exit 0. UTF-16: `echo-sem-escape` encontrado. Latin-1: `ação` impresso certo. Linha de 1.600 caracteres com chave AWS falsa: `aws-key` HIGH, trecho omitido. |
| Códigos de saída | caminho inexistente; inexistente + arquivo com HIGH; inexistente + arquivo limpo; arquivo limpo | 2; 1; 2; 0. |
| Poda e pasta-mãe chamada `build` | scanner rodado de dentro de `build/proj`; pasta só com `node_modules` | Achado encontrado; "nenhum arquivo", exit 2. |
| Código correto, escrito seguindo a skill | `login.php` de 65 linhas (PDO, `password_hash`, CSRF, `getenv`), plugin WordPress de 75 linhas (`$wpdb->prepare`, `insert`, nonce, `current_user_can`), e os 19 blocos de código das referências e do SKILL.md extraídos para arquivos | Nenhum achado nos dois arquivos PHP (exit 0). Nos blocos, nenhum achado em código; o único HIGH foi a frase do checklist em prosa "No -march=native in a build that ships", passada como `.txt`. |
| Linhas adversas | 900 linhas de até 486 caracteres (`select a,a,...`, `where where ...`, `update x set update x set ...`) | 1,09 s no total. Todos os quantificadores são limitados e a linha tem teto de 500. |
| Scanner na própria skill | `py -3.12 scripts/revisar_codigo.py skills/principal-secops-dev-token-optimizer` | `OK. 1 arquivo(s)`, exit 0. No original dava HIGH em `evals.json:101`. |
| Frontmatter | script Python lendo o YAML | `name` 36 caracteres, só minúsculas e hífens. `description` 1.000 caracteres (1.003 bytes), conferido também com PyYAML. Sem `<` ou `>`. Chaves: só `name` e `description`. |
| Referências | regex sobre SKILL.md e sobre cada referência | 19 arquivos citados, 19 existentes, nenhum órfão, nenhuma citação quebrada entre referências. |
| Evals | `json.load` | 23 evals, ids 1 a 23, mesmo esquema de chaves. |
| Fatos com data | WebFetch e WebSearch em 16/11/2026 | Nomes A01 a A10 do OWASP Top 10:2025 conferem (top10.owasp.org/2025). CRA: 10/12/2024, 11/09/2026, 11/12/2027 conferem (Comissão Europeia). ASVS 5.0.0 é a versão estável. PCI DSS 4.0.1 vigente. NIST SP 800-63B-4 final em julho de 2025. CNPJ alfanumérico emitido desde 31/07/2026. `endoflife.date/api/php.json` e `/api/v1/products/php/` respondem 200. |
| Leitura em contexto limpo | dois subagentes, um com o SKILL.md original e um com o novo, mesmas 7 perguntas | Ver o bloco abaixo. |

### Checagem com subagentes em contexto limpo

Dois subagentes (modelo Sonnet, contexto limpo) leram só o SKILL.md, um o original e outro o novo, e responderam às mesmas 7 perguntas.

| Pergunta | SKILL.md original | SKILL.md novo |
|---|---|---|
| Login em PHP com cPanel: quais referências? | Carregou `php.md` e `mysql.md` e **descartou `security-baseline.md`** por causa do teto de 2. Apontou a contradição com a seção 5. | Carregou as três. "Cabe no limite." |
| Qt + 300 mil arquivos + arrastar + bonito | 5 arquivos, mas apontou ambiguidade na ordem. | Os mesmos 5, sem ambiguidade. |
| Comando do scanner em `/mnt/skills/user/...` e em plugin no Windows | Só os caminhos fixos em `~/.claude/skills`, que "provavelmente não existem". Disse que adaptar o caminho não era autorizado pelo texto. | Montou os dois caminhos corretos a partir da pasta do SKILL.md. |
| HIGH antigo em linha fora do pedido | Apontou a contradição entre "Fix every HIGH" e "do not fix without permission". | Não corrige, avisa em uma linha. Apontou uma ambiguidade restante (ver abaixo). |
| HIGH que é falso positivo | "Reescreveria a linha para o scanner parar de marcar." | Mantém o código. Apontou que faltava dizer que pode entregar. |
| Saída 2 do scanner | "Não definido no arquivo." | "Não passou." |
| Onde estão os checklists de nativo e GUI | No SKILL.md. | No fim de `native-app-security.md` e `gui-desktop.md`. |

O subagente do texto novo apontou três pontos, que corrigi depois da checagem (essa última redação não foi reexecutada com subagente):
1. A seção 7 mandava avisar de todo HIGH antigo "pela regra 9", mas a regra 9 só fala de crítico. Agora: avisa se for de um dos tipos críticos da regra 9; senão, silêncio.
2. "Deliver only when it is gone" conflitava com o falso positivo. Agora a primeira regra fala em "A real HIGH" e a do falso positivo diz "leave working code alone and deliver".
3. "Stay in the project folder" era vago. Agora: "Do not `cd` into the skill folder: run from where you are".

## (e) O que não mudei, e por quê

- **Mensagens do scanner sem acento.** Mantive em ASCII de propósito. A saída passa por terminais e ferramentas do Windows (PowerShell 5.1 decodifica pela página OEM) e viraria texto corrompido. Quem fala com o usuário é o Claude, com acento.
- **Comentários e identificadores de código em inglês** (seção 1). Para um usuário que não programa, comentário em português talvez ajudasse. É escolha de autor e não quis inverter sem perguntar.
- **`SameSite=Strict` como padrão.** Quebra a sessão em retorno de gateway de pagamento e em link de e-mail, mas a referência já prevê `Lax` nesses casos.
- **`| raw`, `| safe` e `{!!` como HIGH.** Há uso legítimo com HTML próprio. Deixei HIGH porque a regra nova de falso positivo no SKILL.md cobre o caso.
- **Filtro de rótulo no scanner.** `secret-atribuido` ignora de propósito valor só de letras com menos de 12 caracteres (`"password": "Senha"`, `"Esqueceu?"`), valor igual ao nome do campo e valor que começa com `your`, `seu`, `example`, `changeme` e parecidos. Uma senha real como `"minhasenha"` passa sem acusação. Troquei esse falso negativo por não marcar arquivos de tradução e formulários. Senha com espaço ou com menos de 6 caracteres também não é acusada (mas o trecho é escondido).
- **`RedirectMatch` no `.htaccess`** não foi testado em um Apache real, só revisado. A diretiva é válida em `.htaccess` e está dentro de `<IfModule mod_alias.c>`.
- **Segredo dentro de comentário** só é pego pelas regras de formato exato. `// password = "x"` em comentário continua ignorado para não marcar exemplos.
- **SQL em várias linhas** só é pego em parte (linhas de continuação que começam com `WHERE`, `AND`, `VALUES`). O scanner continua por linha, sem parser.
- **Números de tempo de abertura em `gui-desktop.md`** são ilustrativos e não medi. Ficaram.
- **Textos de `diagnostico.md`, `c-cpp.md`, `rust.md`, `qt.md`, `gui-design.md`, `gui-outros.md`, `java.md`, `frontend.md`, `compliance-licencas.md`.** Li todos e não achei erro que justificasse edição.
- **LGPD.** Prazo de 3 dias úteis e Resolução CD/ANPD nº 15/2024 conferem com o que eu sei, mas não consegui abrir a página da ANPD nesta sessão. Não mexi.
- **Qt 5 sem suporte open source** (`qt.md:3`): não verifiquei online. Não mexi.
- **`graphify update .`** (pedido no CLAUDE.md do diretório-pai): não rodei, porque grava fora da pasta do projeto e a instrução desta tarefa proíbe.
- **Skill `superpowers:writing-skills`**: não carreguei. As regras de frontmatter vieram do próprio enunciado e foram medidas por script.
- **`original/`, `README.md`, `LICENSE`, `.claude-plugin/`, `tools/`**: não toquei.

## (f) Impacto em tokens

Estimativa de tokens: bytes divididos por 4.

| Arquivo | Antes (bytes) | Depois (bytes) | Diferença | Tokens aprox. |
|---|---|---|---|---|
| SKILL.md (carregado em toda tarefa) | 16.376 | 15.315 | -1.061 (-6,5%) | 4.090 para 3.830 |
| Todas as referências somadas | 120.672 | 126.296 | +5.624 (+4,7%) | 30.170 para 31.570 |
| `php.md` | 6.405 | 8.026 | +1.621 | WordPress e `.htaccess` |
| `security-baseline.md` | 16.172 | 17.251 | +1.079 | Payments, SSRF |
| `bancos-outros.md` | 6.030 | 6.959 | +929 | Supabase, Firebase |
| `native-app-security.md` | 4.754 | 5.515 | +761 | checklist vindo do SKILL.md |
| `gui-desktop.md` | 9.631 | 10.344 | +713 | checklist vindo do SKILL.md |
| `outras-linguagens.md` | 4.707 | 4.189 | -518 | seções-ponteiro removidas |

As referências só são carregadas sob demanda, então o custo fixo por conversa caiu. Para uma tarefa web típica (login em PHP), o orçamento subiu de 2 para 3 arquivos, o que carrega `security-baseline.md` junto: cerca de 4.300 tokens a mais nessa tarefa, de propósito, porque antes a regra de segurança era a descartada. A saída do scanner em projeto com muitos achados caiu de 5 linhas por achado para 1 linha por achado mais 2 por regra.
