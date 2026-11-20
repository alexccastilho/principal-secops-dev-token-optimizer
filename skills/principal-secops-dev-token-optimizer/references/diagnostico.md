# Diagnóstico: when something broke

## Contents
- The rule
- Diagnostic sequence
- What to ask the user, by symptom
- Common causes by symptom
- Reading a stack trace for someone who cannot read one
- Fix the cause, not the case
- After the fix

## The rule

Diagnose first, fix second. A fix applied to the wrong cause creates a second bug on top of the first, and the user cannot tell them apart.

Never rewrite beyond the fault. "Já que estou aqui, aproveitei e melhorei" is how a working system becomes a broken one.

## Diagnostic sequence

```
- [ ] 1. Reproduce: what exactly does the user do, and what appears on screen?
- [ ] 2. Locate: which file and line, from the log or the trace
- [ ] 3. Read that file before touching it
- [ ] 4. Identify the cause, state it in one pt-BR sentence
- [ ] 5. Smallest possible fix at the cause, not at the symptom
- [ ] 6. Test instruction covering the failure case AND the case that used to work
```

If step 4 cannot be stated in one sentence, the cause is not identified yet. Ask for more information instead of guessing.

## What to ask the user, by symptom

Ask for ONE thing at a time, and say exactly where to find it.

| Symptom | Ask for |
|---|---|
| Tela branca (PHP) | "Me manda as últimas 20 linhas do arquivo `storage/logs/app.log`" |
| Erro 500 | log do servidor; no cPanel fica em "Errors" ou "Logs de erro" |
| "Não salva" | o formulário e o arquivo que recebe o envio |
| "Ficou lento" | quantos registros tem a tabela, e o que exatamente demora |
| Erro em tela com texto | print da tela inteira, incluindo a barra de endereço |
| "Parou depois que mexi" | o que foi alterado e quando funcionava pela última vez |
| Erro só em produção | diferenças entre local e produção: versão da linguagem, extensões, permissões |

Never ask the user to "abrir o console do navegador" without telling them how: "Aperte F12, clique na aba Console, tire um print."

## Common causes by symptom

**Tela branca**
Fatal error with display off. Almost always: missing file, syntax error, missing extension, out of memory. The log has it.

**Erro 500**
Server-level. Check `.htaccess`, file permissions (files 644, folders 755, never 777), wrong PHP version, missing module.

**Erro 403**
Permissions or a rule blocking the path. Check ownership and the web server config, not the code.

**"Não conecta no banco"**
Credentials, host (`localhost` vs an IP the host gave), user permissions, database not created, port blocked.

**Funciona local, quebra em produção**
Case-sensitive filesystem (Linux server, Windows dev machine), different language version, path separators, missing extension, `.env` not deployed, timezone.

**Funcionava e parou sozinho**
Certificate expired, disk full, dependency auto-updated, a cron job, password rotated, hosting plan limit reached.

**Ficou lento**
Query without index, query inside a loop (N+1), table that grew, missing `LIMIT`, external API call in the request path. Measure before changing anything: `EXPLAIN` for SQL, timing for code.

**Erro intermitente**
Race condition, connection pool exhausted, cache, load balancer with servers in different states. Reproduce before fixing.

## Reading a stack trace for someone who cannot read one

Translate it. Do not paste it back.

Instead of showing the trace, say:
"O erro está no arquivo `enviar.php`, linha 42: o código tenta usar o e-mail do cliente, mas o formulário não mandou esse campo. Vou corrigir de dois lados: o formulário passa a exigir o e-mail, e o `enviar.php` passa a recusar o envio se ele vier vazio."

Pattern: which file, which line, what it tried to do, why it failed, what the fix does.

## Fix the cause, not the case

"Smallest fix" means the fewest lines at the cause, not a patch over the symptom. These look small and make the next bug harder to find:

* an `if` for the one value that failed (`if ($pedido_id == 1834)`);
* a `sleep` or a retry so a race "usually" wins;
* an empty `catch`, an `@` before the call, `except: pass`;
* skipping or disabling the test that caught it.

Each one says the design is missing a rule. State the rule in the step 4 sentence and fix it there: "O desconto é aplicado duas vezes quando o cupom é reutilizado" leads to fixing the coupon rule, not to an `if` for that coupon.

If the cause lives outside the files of the request, apply the minimal fix, then say in one line where the cause is and offer to fix it. This is the same boundary as "never rewrite beyond the fault": you name the cause, you do not chase it unasked. Patterns and examples: `estrutura.md`, section "Special cases: fix the cause".

## After the fix

* State in one line what caused it, so the user recognizes it next time.
* Give the test instruction covering both the broken case and a case that already worked, to prove nothing regressed.
* If the same class of bug can recur elsewhere in the project, say so in one line and offer to check. Do not check unasked: that is scope creep.
