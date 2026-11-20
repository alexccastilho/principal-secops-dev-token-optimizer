# Benchmark: with and without the skill

[Português](BENCHMARK.pt-BR.md) · [Español](BENCHMARK.es.md)

Measured on 2026-11-20 with skill version 2.2.0, Claude Code 2.1.329, the `sonnet` model, on Windows 11. 6 languages × 2 conditions × 3 repetitions = 36 runs.

## Short version

- **Security:** in a blind review, the app built with the skill was the more secure one in all 6 languages. Neither condition produced a HIGH-severity vulnerability, and all apps used parameterized SQL. The difference is in the second layer: password hashing at current costs, login lockout that survives a restart, generic error messages, and backup and recovery instructions.
- **Cost:** the skill made each request about 3 times as expensive and 2.5 times as slow. The averages are USD 0.58 against 0.20 per app, and 176 s against 69 s. It also wrote about twice the code.
- **Working as delivered:** without the skill, 18 of 18 apps compiled. With the skill, 16 of 18 compiled, and one PHP app could not create its first user.

For a small app built from scratch, the skill trades tokens and time for a safer, better-documented result. The token savings in the skill's name come from its rules on reading, answering and refactoring: no restating, no pasting whole files, reading a section rather than a whole file. This benchmark does not measure those savings; it measures one full app per run.

## What the skill adds

Neither condition left a severe flaw: the model without the skill also used parameterized SQL and a strong password hash in every app. What the skill added, in the blind review and the delivery checks:

**A second layer of protection.**

| Point | Without skill | With skill |
|---|---|---|
| Login lockout | In Java, C# and Python it resets when the program restarts, so guessing is unlimited | Stored in the database; survives a restart |
| Password hash cost | Python and Node.js used scrypt below the OWASP cost | Argon2id, or scrypt and PBKDF2 at current cost |
| Minimum password length | 8 characters | 12 to 15 characters (current NIST guidance) |
| Error messages | PHP showed internal details (its README points to the development php.ini); C# crashed with the full error; Java showed the exception text | Generic message for the user, details in a log file |
| Login session | Token stored as issued | Token stored as a hash; in Go, changing the password ends every session |
| Dependencies | Not checked | Java verifies the library's SHA-256; C# locks versions and runs NuGet audit |

**An app a non-programmer can run and keep.** Run instructions in 18 of 18 apps, against 6 of 18; a `.gitignore` that keeps the database with personal data out of Git in 17 of 18, against none; automated tests in 3 of 18, against none. The skill's apps also came with a launcher, first-user setup, and backup and password-recovery steps. Without the skill, the C# app was two source files with no way for a non-programmer to run it, and the Python app had no instructions.

**Care with personal data.** Data kept in `%LOCALAPPDATA%` (or outside the web folder, in PHP), and logs that record identifiers, not names or e-mail addresses.

**When it pays off.** For about USD 0.38 and 2 minutes more per app, the result resists password guessing better, does not leak error details, is documented for its user and is ready to hold personal data. It is worth it for an app that will be used and holds data about people; for a throwaway prototype it is not.

**Not measured here.** Reviewing and refactoring existing code, maintaining legacy systems, and answering without restating, where the skill's token-saving rules apply. That needs a second benchmark.

## The request

The same text, in Portuguese, for every run. `{lang}` was PHP, Python, JavaScript com Node.js, Java, C# with .NET or Go:

> Preciso de um sistema simples em {lang} para cadastrar meus contatos (nome, e-mail e telefone), com login de usuário e senha, salvando num banco SQLite. Vai rodar só no meu computador com Windows, é tudo do zero, só eu vou usar, e guarda dado pessoal (nome, e-mail e telefone). Crie os arquivos nesta pasta e me diga como rodar. Não sou programador.

The questions the skill normally asks before a new project are answered in the text, so both conditions can deliver in one non-interactive turn.

## Results by language

Averages of 3 runs. "Code lines" counts source lines without blanks or comments.

| Language | Time (s) without / with | Output tokens without / with | Cost (USD) without / with | Code lines without / with | Compiled without / with |
|---|---|---|---|---|---|
| PHP | 62 / 155 | 10,195 / 22,218 | 0.18 / 0.48 | 303 / 483 | 3/3 / 3/3 |
| Python | 44 / 171 | 6,575 / 23,962 | 0.13 / 0.56 | 198 / 544 | 3/3 / 3/3 |
| Node.js | 63 / 172 | 9,778 / 25,715 | 0.18 / 0.56 | 209 / 597 | 3/3 / 3/3 |
| Java | 93 / 165 | 14,920 / 24,824 | 0.25 / 0.56 | 404 / 624 | 3/3 / 2/3 |
| C# | 60 / 201 | 10,620 / 29,748 | 0.19 / 0.65 | 249 / 678 | 3/3 / 3/3 |
| Go | 93 / 193 | 15,052 / 30,584 | 0.25 / 0.64 | 490 / 767 | 3/3 / 2/3 |
| **Average** | **69 / 176** | **11,190 / 26,175** | **0.20 / 0.58** | **309 / 616** | **18/18 / 16/18** |

Total input tokens (including cache reads) averaged 141,000 without the skill and 734,000 with it, and conversation turns 10 and 34. The skill reads its routing file and three to five references before writing, and writes more files (15 on average, against 5).

The two compile failures with the skill: one Go run left out `go.mod`, and one Java run referenced an SQLite driver class without importing it.

## Security

**Static checks.** The skill's own scanner (`revisar_codigo.py`) found HIGH findings only in Node.js: on average 0.7 per app without the skill and 0.3 with it. Semgrep (`p/default`, version 1.186) found similar counts in both conditions, mostly warnings in Go web handlers.

**Blind review.** For repetition 1 of each language, two reviewer agents received the pair as `A` and `B` in a random order and scored 10 criteria from 0 to 2 by reading the code. The full scores, with the defects found on each side, are in [benchmark/results/blind_review.md](../benchmark/results/blind_review.md).

| Language | Without skill | With skill |
|---|---|---|
| PHP | 18/20 (security 14/16) | 16/20 (security 16/16) |
| Python | 10/14 | 14/14 |
| Node.js | 17/20 | 18/20 |
| Java | 12/14 | 14/14 |
| C# | 10/14 | 13/14 |
| Go | 19/20 | 20/20 |

Desktop and console apps are scored out of 14, because sessions, CSRF and XSS do not apply to them. PHP with the skill scored lower overall because it does not work as delivered: its launcher calls a script that was never written.

**Delivery checks** across all 18 apps of each condition (file and keyword checks, not a review):

| Check | Without skill | With skill |
|---|---|---|
| README or run instructions | 6/18 | 18/18 |
| `.gitignore` | 0/18 | 17/18 |
| Automated tests | 0/18 | 3/18 |
| Strong password hash (Argon2id, bcrypt, scrypt or PBKDF2) | 18/18 | 18/18 |
| Login attempt limit | 18/18 | 18/18 |

## Method

- **Isolation.** Each run uses its own `CLAUDE_CONFIG_DIR` holding only a copy of the login, with `--strict-mcp-config` and no plugins except, in the skill condition, `--plugin-dir` pointing at this repository. `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` stops skills uploaded to claude.ai from syncing into the run. Without it, an older copy of this skill from the account was loaded into the "without skill" condition. The first full run was contaminated this way and was discarded. `run.json` records the skills seen and called, and `analyze.py` flags any baseline run that called the skill. None did in the published run.
- **Windows short paths.** Claude Code asks for approval before writing to a path containing `~` (for example `C:\Users\NAME~1`), which a non-interactive run can never give. The script expands short names; a run before this fix left the skill's Node.js folders empty.
- **Permissions.** Both conditions had the same tool list: file tools, web search, web fetch, the Python interpreter, and the toolchain's version and syntax checks. Package installation was not allowed, so the build check stays comparable. The numbers above were measured at commit `b723084`, whose list also allowed `curl` and unrestricted web fetch. The current script narrows network access to version sources and passes a filtered environment.
- **Build check.** Run after the session on the files it left: `php -l`, `python -m compileall`, `node --check`, `mvn package` (or `javac` when there is no `pom.xml`), `dotnet build`, and `go mod tidy && go build`. The analysis step downloads the declared dependencies; the session itself could not. Toolchains: PHP 8.5.12, Go 1.27.4, .NET SDK 10.0.404, Temurin JDK 25.0.5, Maven 3.9.16.
- **Limits.** Three repetitions per cell is a small sample: time and tokens vary by up to 2× between repetitions of the same cell. One request, one model, one machine. The blind review covers one repetition per language, by model reviewers, not people. Lines of code are a size measure, not a quality measure.

## Reproduce

Running the benchmark spends real tokens on the account whose login you copy: about USD 14 for 36 runs at the prices of the date above. Run it in a VM or sandbox: the interpreters stay allowed so the generated apps can be tested, and they can open network connections.

```
# 1. clean configuration with only the login
mkdir cfg && cp ~/.claude/.credentials.json cfg/

# 2. runs (outside the repository; on Windows, a path without "~")
python benchmark/run_benchmark.py --config-dir cfg --out ../bench --reps 3 --jobs 3

# 3. analysis (needs the toolchains of the languages measured, and semgrep, on PATH)
python benchmark/analyze.py --runs ../bench --results benchmark/results

# 4. delete the login copy
rm cfg/.credentials.json
```

`benchmark/results/` holds the published run: `runs.json` (one entry per run), `summary.json` (averages per language and condition), `quality.json` (delivery checks) and `blind_review.md`.
