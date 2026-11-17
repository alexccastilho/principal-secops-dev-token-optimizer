# Changelog

Todas as mudanças relevantes deste projeto. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), versões em [SemVer](https://semver.org/lang/pt-BR/).

## [2.0.2] - 2026-11-16

### Adicionado
- Ícone do plugin (`.claude-plugin/icon.png`, 1024x1024): escudo com o símbolo de código. O gerador está em `tools/make_icon.py`.

## [2.0.1] - 2026-11-16

### Alterado
- Seção 7 do SKILL.md: a instrução do caminho do scanner continua fazendo sentido depois que o Claude Code substitui `${CLAUDE_SKILL_DIR}`. Testado nos dois cenários (caminho substituído e marcador literal no claude.ai).
- Relatório de análise atualizado com os ajustes feitos no empacotamento.

## [2.0.0] - 2026-11-16

Revisão profunda da skill. O relatório completo, com achados por severidade e a validação feita, está em [docs/ANALISE-v2.0.0.md](docs/ANALISE-v2.0.0.md).

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
