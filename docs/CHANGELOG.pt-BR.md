*Leia em outros idiomas: [English](../CHANGELOG.md) · [Español](CHANGELOG.es.md)*

# Registro de mudanças

Todas as mudanças relevantes deste projeto. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), versões em [SemVer](https://semver.org/lang/pt-BR/).

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
- O SKILL.md cresceu de 15.665 para 19.240 bytes, por causa das seções 9 e 10. Os detalhes ficam nas referências, carregadas só quando a tarefa pede.
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
