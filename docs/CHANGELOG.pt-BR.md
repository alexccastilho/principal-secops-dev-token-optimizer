*Leia em outros idiomas: [English](../CHANGELOG.md) · [Español](CHANGELOG.es.md)*

# Registro de mudanças

Todas as mudanças relevantes deste projeto. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), versões em [SemVer](https://semver.org/lang/pt-BR/).

## [2.2.0] - 2026-11-20

Todas as referências de linguagem e banco de dados reescritas a partir de fontes primárias atuais, cinco referências novas, manutenção de sistema legado como caso principal e um scanner que lê 151 tipos de arquivo. Os fatos que dependem de versão foram conferidos em fontes primárias em 2026-11-20; o que não pôde ser verificado foi retirado ou escrito sem versão. Os registros de evidência em [docs/research/](research/) listam cada fato conferido com a URL, e também o que veio do texto anterior ou de conhecimento geral.

### Adicionado
- `references/legado.md`: Delphi, Free Pascal/Lazarus, Pascal, Clipper/Harbour/xBase, Visual FoxPro, VB6, COBOL, RPG, OpenEdge, PowerBuilder e ABAP. A regra é "nunca reescreva um sistema legado que funciona": backup, segurança onde ele está, migração em etapas.
- `references/scripts-e-automacao.md`: Lua (sandbox no 5.5 e no Luau), Perl, VBA e macros do Office/Access, Google Apps Script, PowerShell 7 e 5.1, Bash/shell, `.bat`/`.cmd`, AutoHotkey e Tcl, com uma seção comum sobre rodar scripts com segurança no Windows.
- `references/dados-e-ciencia.md`: R, Julia, MATLAB/Octave, Fortran, SAS, Jupyter, pandas/Polars, injeção de fórmula em CSV/Excel e LGPD em bases de dados.
- `references/sistemas-outros.md`: Zig, Ada/SPARK, Assembly, Objective-C, D e Nim.
- `references/bancos-nosql.md`: MongoDB, Redis/Valkey, Firebase, DynamoDB, Cassandra/ScyllaDB, Elasticsearch/OpenSearch, Neo4j, ClickHouse, InfluxDB/TimescaleDB e bancos vetoriais com RAG (OWASP LLM01 e LLM08).
- `references/outras-linguagens.md` passou a cobrir Swift, Dart/Flutter, Scala, Elixir/Erlang, Clojure, Haskell, OCaml, Groovy/Jenkins, Crystal, F# e VB.NET, além de Go, .NET, Ruby, Kotlin e mobile (OWASP MASVS).
- `references/bancos-outros.md` passou a cobrir Firebird, Db2, DuckDB, CockroachDB, Access e DBF/Paradox, além de PostgreSQL, SQLite, SQL Server e Oracle.
- Scanner: 25 regras novas (de 52 para 77) e 80 tipos de arquivo novos (de 71 para 151), cada regra testada numa linha insegura e na linha segura correspondente. Novidades: SQL montado com `&`, `..`, `||`, interpolação ou `Sprintf`/`format!`/`paste`; `FromSqlRaw` do EF Core; interpolação no Rails; SQL dinâmico em COBOL/ABAP; filtro do MongoDB vindo de `req.body`; comando de sistema montado com dado em 20 linguagens; `Invoke-Expression`, `curl | bash`, `eval "$x"`; `load` do Lua, `&()` do Clipper, `read-string` do Clojure, `Eval.me` do Groovy; átomos e `binary_to_term` no BEAM; `BinaryFormatter` do .NET; `open` de dois argumentos no Perl; `expr` sem chaves no Tcl; `<?!=` no Apps Script; `trust` do PostgreSQL pela rede; regras abertas do Firebase; verificação TLS desligada em uma dúzia de stacks; chaves `sb_secret_` do Supabase; verificações de segurança do Zig/Ada desligadas. A sintaxe de comentário de cada linguagem é respeitada (`--`, `'`, `!`, `;`, `rem`, `&&`).
- `tests/test_scanner_languages.py`: 83 pares inseguro/seguro e 8 casos comentados.
- Evals: de 28 para 35 cenários (Delphi com Firebird, Clipper em pasta compartilhada, mods em Lua, VBA com a vírgula decimal do pt-BR, CSV para Excel, Redis e MongoDB numa VPS, `irm | iex` no PowerShell).
- `benchmark/`: scripts que rodam o mesmo pedido de app no Claude Code com e sem a skill, numa configuração limpa, e medem tokens, tempo, custo, linhas de código, compilação e achados de segurança (veja [BENCHMARK.pt-BR.md](BENCHMARK.pt-BR.md)).

### Alterado
- Todas as referências web atualizadas: PER Coding Style, recursos do PHP 8.5/8.6, bloqueio de pacotes com alerta no Composer, Laravel e Symfony; modelo de permissões do Node, type stripping, aprovação de install scripts no npm 12, Express 5, Next.js 16; recursos do Python 3.14/3.15, `pip lock`, CSP do Django 6; Java 25, Spring Boot 4 e Spring Security 7; Trusted Types, CSP estrita, WCAG 2.2 e a Lei Europeia de Acessibilidade.
- `mysql.md`: trilhas LTS e Innovation, fim do MySQL 8.0 (2026-04-30), `mysql_native_password` removido no 9.0, remoções do 8.4 que quebram scripts, `unix_socket` e PARSEC no MariaDB.
- `security-baseline.md`: senhas seguem a NIST SP 800-63B-4 (15 caracteres quando a senha é o único fator, sem regra de composição, lista de bloqueio); OWASP Top 10 for Agentic Applications e CWE Top 25 2025 no mapa de normas; bcrypt com custo 12 por padrão.
- `versoes-e-fontes.md`: 36 linhas novas na tabela de fontes, cada uma com o identificador do endoflife.date ou a página do fabricante quando não há.
- `compliance-licencas.md`: datas do CRA (11 de junho de 2026, 11 de setembro de 2026, 11 de dezembro de 2027) e a cadeia de notificação de 24 h / 72 h / um mês.
- `qt.md`: o Qt open source recebe correções só até a próxima versão menor; o LTS longo é comercial. Regras do QProcess reescritas para o Qt 6.
- `gui-desktop.md`, `gui-outros.md`: depreciações do GTK 4.10, capabilities do Tauri 2, padrões do Electron por versão, arrastar e soltar no Avalonia 12, acessibilidade no egui.
- `c-cpp.md` e `rust.md` reescritos com flags de hardening, sanitizers e ferramentas de cadeia de suprimentos atuais.
- SKILL.md: roteamento das referências novas, regras de pareamento para legado e NoSQL, e uma descrição que cita as stacks novas (ainda abaixo de 1024 caracteres). O teste de estilo agora cobre o SKILL.md e todas as referências.

## [2.1.0] - 2026-11-20

Estrutura preventiva e modo refatoração, com ideias adaptadas de [`untangle-codebase` e `prune-tests`](https://github.com/caldoai/skills) (MIT, © 2026 Maze). O repositório passou a ter testes automatizados, CI e documentação em inglês, português e espanhol.

### Adicionado
- **Estrutura no modo normal.** Seção 9 do SKILL.md: antes de escrever, a pergunta "o que muda junto com isto?"; nada de cópia de lógica ou valor, ligação com detalhes internos de outro módulo, wrapper inútil ou configuração para o que nunca varia; "corrija a causa, não o caso" no lugar de `if` para um valor, `sleep`, retry ou `catch` vazio. Em código existente a regra é "não piore": vale para o que a skill escreve, nunca para o código em volta. Código de segurança nunca é tratado como excesso.
- `references/estrutura.md`: as regras completas com exemplos e as regras para escrever testes que protegem comportamento (valor esperado literal, testar o que quem usa enxerga, nunca mockar a coisa testada).
- **Modo refatoração, só com pedido explícito.** Seção 10 do SKILL.md, `references/refatoracao-completa.md` e o comando `/secops-refatorar` do plugin. Exige Git com tudo salvo e um branch próprio, congela os contratos públicos, não atualiza dependências, mantém um log de decisões, verifica de novo até não sobrar nada que valha corrigir e termina com um relatório em pt-BR. Extras opcionais: comentários e testes, com testes de segurança e de regressão sempre preservados.
- Dois itens novos no checklist de entrega: nenhuma lógica copiada ou import de algo mais instável, e nenhum caso especial novo onde cabe uma correção na causa.
- Evals: de 23 para 28 cenários (frete sem duplicar, desconto em dobro sem `if`, pedido vago que não inicia refatoração, `/secops-refatorar`, teste com valor literal).
- Suíte de testes (`tests/`, só biblioteca padrão): comportamento do scanner, versões coerentes, referências ligadas ao SKILL.md, evals, traduções, estilo da documentação e conteúdo do ZIP.
- GitHub Actions: testes no Linux e no Windows com Python 3.8 e atual, ZIP do claude.ai anexado a cada execução, CodeQL e Dependabot para as actions.
- Documentação em três idiomas (README, CHANGELOG e CONTRIBUTING em inglês, português e espanhol), `SECURITY.md`, `CODE_OF_CONDUCT.md`, modelos de issue e de pull request.
- `THIRD_PARTY_NOTICES.md` dentro da pasta da skill, com o crédito e a licença MIT de caldoai/skills. Vai junto no ZIP.

### Alterado
- Prioridade de conflito: Segurança > Integridade > Clareza > **Estrutura** > Economia de tokens > Estilo.
- `projeto-do-zero.md`: o esqueleto padrão organiza `src/` por funcionalidade, com `comum/` só para o que duas ou mais funcionalidades usam.
- `diagnostico.md`: "menor correção" quer dizer menos linhas na causa, não um remendo no sintoma.
- Descrição da skill: passa a citar estrutura de código, testes e "reorganize o projeto", dentro do limite de 1024 caracteres.
- O SKILL.md cresceu de 15.665 para 19.634 bytes, por causa das seções 9 e 10. Os detalhes ficam nas referências, carregadas só quando a tarefa pede.
- `tools/build_zip.py` aceita a pasta de saída como argumento.
- O README principal passou a ser em inglês, com versões em português e espanhol em `docs/`.

## [2.0.2] - 2026-11-16

### Adicionado
- Ícone do plugin (`.claude-plugin/icon.png`, 1024x1024): escudo com o símbolo de código. O gerador está em `tools/make_icon.py`.

## [2.0.1] - 2026-11-16

### Alterado
- Seção 7 do SKILL.md: a instrução do caminho do scanner continua fazendo sentido depois que o Claude Code substitui `${CLAUDE_SKILL_DIR}`. Testado nos dois cenários (caminho substituído e marcador literal no claude.ai).
- Relatório de análise atualizado com os ajustes feitos no empacotamento.

## [2.0.0] - 2026-11-16

Revisão profunda da skill. O relatório completo, com achados por severidade e a validação feita, está em [docs/ANALISE-v2.0.0.md](ANALISE-v2.0.0.md).

### Corrigido
- Scanner: um segredo podia vazar na saída quando a mesma linha também disparava outra regra. Agora o trecho é omitido na linha inteira.
- Scanner: chaves privadas PEM nunca eram detectadas, e `.pem` e `.key` não eram lidos.
- Scanner: falsos HIGH em código correto (`sprintf` em PHP, `prepare()->execute([...])`, `{$wpdb->prefix}`, concatenação de texto comum).
- Scanner: deixou de travar com `UnicodeEncodeError` no console do Windows e passou a ler arquivos UTF-16. Uma pasta-mãe chamada `build` ou `dist` não zera mais a varredura, e caminho inexistente devolve saída 2.
- `php.md`: o `.htaccess` agora bloqueia `/.git/` de verdade.
- SKILL.md: o limite de referências não descarta mais o modelo de ameaça (`security-baseline.md`). A segurança vem antes da economia de tokens.
- SKILL.md: acabou a contradição entre "corrija todo HIGH" e "não mexa fora do pedido".

### Adicionado
- Scanner detecta mais segredos: `'password' => '...'`, `define('DB_PASSWORD', ...)`, `new PDO(..., "root", "senha")`, `mongodb+srv://`, tokens de GitHub, Stripe, Google e Mercado Pago.
- Cobertura de WordPress, pagamentos e Pix, Supabase e Firebase, CPF e CNPJ (inclusive alfanumérico), cPanel/`public_html`, Kotlin, PowerShell e shell script.
- Evals: de 17 para 23 cenários (injeção de instrução em arquivo, achado crítico fora do escopo, falso positivo, WordPress, Pix, Supabase).
- Empacotamento: plugin e marketplace do Claude Code, ZIP para o claude.ai, `license` e `metadata` (autoria e versão) no frontmatter.

### Alterado
- O caminho do scanner é montado a partir da pasta da skill (`${CLAUDE_SKILL_DIR}` no Claude Code), sem caminho fixo.
- Os checklists de código nativo e de GUI saíram do SKILL.md para `native-app-security.md` e `gui-desktop.md`. O SKILL.md ficou cerca de 6% menor.
- O scanner roda em Python 3.8+ e só usa a biblioteca padrão.

## [1.0.0]

Versão original da skill, criada por Alex Camacho Castilho.
