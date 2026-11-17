# Principal SecOps Dev & Token Optimizer

Skill para **Claude Code** e **claude.ai** que faz o Claude trabalhar como um desenvolvedor sênior de segurança (SecOps) atendendo uma pessoa que **não programa**. Ele entrega código seguro, padronizado e funcionando, explica em português simples e gasta o mínimo de tokens.

**Autor:** Alex Camacho Castilho ([@alexccastilho](https://github.com/alexccastilho))
**Licença:** [MIT](LICENSE)

## O que a skill faz

- **Segurança por padrão.** Aplica sem precisar pedir uma linha de base alinhada ao OWASP Top 10:2025, ao ASVS 5.0 e à LGPD: consultas parametrizadas, senhas com Argon2id ou bcrypt, segredos fora do código, controle de acesso no servidor e erros que não vazam detalhes.
- **Não quebra o que já funciona.** Lê os arquivos antes de editar, mexe só no necessário, preserva contratos (rotas, colunas, formatos JSON) e pede confirmação antes de qualquer ação destrutiva.
- **Fala a língua de quem não programa.** As respostas vêm em pt-BR claro: onde colocar o arquivo, qual comando rodar e como testar o caso certo e o caso de erro.
- **Economiza tokens.** Manda só os trechos que mudaram, carrega as referências por demanda e respeita um limite de arquivos por resposta.
- **Pesquisa versões em vez de chutar.** Lê a versão que o projeto usa e consulta o status de suporte atual, em vez de confiar na memória do modelo.
- **Verifica antes de entregar.** Traz o scanner `scripts/revisar_codigo.py` (Python 3.8+, só biblioteca padrão), que procura segredos no código, SQL concatenado, hash fraco, saída sem escape, `eval`/`exec`, chamadas de shell e armadilhas de memória em C, C++ e Rust.

### Cobertura

| Área | Referências |
|---|---|
| Web | PHP, Java, Node.js/JavaScript, Python, HTML/CSS |
| Bancos de dados | MySQL/MariaDB, PostgreSQL, SQLite, SQL Server, Oracle, MongoDB, Redis |
| Código nativo | C, C++, Rust, CMake, flags de hardening, sanitizers, fuzzing |
| Desktop e GUI | escolha do toolkit, Qt 6, Slint, Avalonia, GTK, Flutter, Tauri, Electron, design visual |
| Processo | projeto do zero, diagnóstico de erros, versões e fontes, conformidade (GPL, SBOM, CRA) |
| Outras linguagens | Go, C#, Ruby, mobile |

## Instalação

### Claude Code: via marketplace de plugins (recomendado)

Dentro de uma sessão do Claude Code:

```
/plugin marketplace add alexccastilho/principal-secops-dev-token-optimizer
/plugin install principal-secops-dev-token-optimizer@alexccastilho-skills
```

Ou pelo terminal:

```bash
claude plugin marketplace add alexccastilho/principal-secops-dev-token-optimizer
claude plugin install principal-secops-dev-token-optimizer@alexccastilho-skills --scope user
```

A skill entra em ação sozinha quando o pedido combina com ela. Para chamá-la manualmente, use `/principal-secops-dev-token-optimizer:principal-secops-dev-token-optimizer`.

Para atualizar: `/plugin marketplace update alexccastilho-skills`.

### Claude Code: cópia manual

```bash
git clone https://github.com/alexccastilho/principal-secops-dev-token-optimizer.git
# Linux ou macOS
cp -r principal-secops-dev-token-optimizer/skills/principal-secops-dev-token-optimizer ~/.claude/skills/
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse principal-secops-dev-token-optimizer\skills\principal-secops-dev-token-optimizer "$env:USERPROFILE\.claude\skills\"
```

Reinicie o Claude Code depois de copiar.

### claude.ai (web, desktop e app)

1. Baixe o arquivo `principal-secops-dev-token-optimizer-vX.Y.Z.zip` na página de [Releases](https://github.com/alexccastilho/principal-secops-dev-token-optimizer/releases/latest).
2. No claude.ai, abra **Customize > Skills** e envie o ZIP sem descompactar.
3. Ative a skill. A execução de código precisa estar ligada nas configurações para o scanner rodar. Sem ela, a skill faz a mesma verificação lendo o código.

Para gerar o ZIP você mesmo: `python tools/build_zip.py` (o arquivo sai em `dist/`).

## Estrutura do repositório

```
.claude-plugin/
  marketplace.json      # catálogo do marketplace (Claude Code)
  plugin.json           # manifesto do plugin, com versão e autoria
skills/principal-secops-dev-token-optimizer/
  SKILL.md              # instruções principais
  references/           # guias por stack, carregados sob demanda
  scripts/revisar_codigo.py  # scanner usado antes da entrega
  evals/evals.json      # cenários de avaliação
tools/build_zip.py      # gera o ZIP para o claude.ai
```

## Uso do scanner fora da skill

```bash
python3 skills/principal-secops-dev-token-optimizer/scripts/revisar_codigo.py <arquivo-ou-pasta>
```

O scanner mascara o valor de qualquer segredo encontrado e retorna código de saída diferente de zero quando há achado HIGH. Isso permite usá-lo em CI.

## Versionamento

O projeto segue o [SemVer](https://semver.org/lang/pt-BR/). As mudanças de cada versão estão no [CHANGELOG](CHANGELOG.md).

## Créditos

Criado e mantido por **Alex Camacho Castilho**. Se você usar, adaptar ou redistribuir, mantenha o aviso de copyright do arquivo [LICENSE](LICENSE).
