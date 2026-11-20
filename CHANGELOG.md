*Read this in other languages: [Português (Brasil)](docs/CHANGELOG.pt-BR.md) · [Español](docs/CHANGELOG.es.md)*

# Changelog

All notable changes to this project. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [SemVer](https://semver.org/).

## [2.2.1] - 2026-11-20

### Changed
- The skill's description now names reviewing and fixing existing code first, with the requests owners actually write ("revise o código", "tem algum problema?", "corrija isso", "não está calculando certo"). In the [refactor benchmark](docs/BENCHMARK-REFACTOR.md), the skill was installed but never called for a review or a bug fix (0 of 12 runs), while a whole-project refactor request called it every time. To fit the 1,024-character limit, the coverage list lost "archives", "drag and drop" and "visual design", which the references still cover. Whether the new description fixes the activation has not been measured yet.

### Added
- Refactor benchmark (`benchmark/refactor/`, `benchmark/analyze_refactor.py`, `--suite refactor`): a 2,700-line practice project in Python and Node.js with planted issues, hidden tests, an answer key and an offline validator. The first run is partial and published as it is in [docs/BENCHMARK-REFACTOR.md](docs/BENCHMARK-REFACTOR.md).

## [2.2.0] - 2026-11-20

Every language and database reference rewritten against current primary sources, five new references, legacy maintenance as a first-class case, and a scanner that reads 151 file types. Version-specific facts were checked against primary sources on 2026-11-20; what could not be verified was removed or written without a version. The evidence logs in [docs/research/](docs/research/) list each checked fact with its URL, and also what was carried over or written from general knowledge.

### Added
- `references/legado.md`: Delphi, Free Pascal/Lazarus, Pascal, Clipper/Harbour/xBase, Visual FoxPro, VB6, COBOL, RPG, OpenEdge, PowerBuilder and ABAP. The rule is "never rewrite a working legacy system": back up, make it safe where it stands, migrate in stages.
- `references/scripts-e-automacao.md`: Lua (5.5 and Luau sandboxing), Perl, VBA and Office/Access macros, Google Apps Script, PowerShell 7 and 5.1, Bash/shell, `.bat`/`.cmd`, AutoHotkey and Tcl, plus a shared section on running scripts safely on Windows.
- `references/dados-e-ciencia.md`: R, Julia, MATLAB/Octave, Fortran, SAS, Jupyter, pandas/Polars, CSV/Excel formula injection and LGPD in datasets.
- `references/sistemas-outros.md`: Zig, Ada/SPARK, Assembly, Objective-C, D and Nim.
- `references/bancos-nosql.md`: MongoDB, Redis/Valkey, Firebase, DynamoDB, Cassandra/ScyllaDB, Elasticsearch/OpenSearch, Neo4j, ClickHouse, InfluxDB/TimescaleDB and vector databases with RAG (OWASP LLM01 and LLM08).
- `references/outras-linguagens.md` now covers Swift, Dart/Flutter, Scala, Elixir/Erlang, Clojure, Haskell, OCaml, Groovy/Jenkins, Crystal, F# and VB.NET besides Go, .NET, Ruby, Kotlin and mobile (OWASP MASVS).
- `references/bancos-outros.md` now covers Firebird, Db2, DuckDB, CockroachDB, Access and DBF/Paradox besides PostgreSQL, SQLite, SQL Server and Oracle.
- Scanner: 25 new rules (52 to 77) and 80 new file types (71 to 151), each rule tested on an insecure line and on the safe line next to it. New: SQL built with `&`, `..`, `||`, interpolation or `Sprintf`/`format!`/`paste`; EF Core `FromSqlRaw`; Rails interpolation; dynamic SQL in COBOL/ABAP; MongoDB filter taken from `req.body`; shell commands built from data in 20 languages; `Invoke-Expression`, `curl | bash`, `eval "$x"`; Lua `load`, Clipper `&()`, Clojure `read-string`, Groovy `Eval.me`; BEAM atoms and `binary_to_term`; .NET `BinaryFormatter`; Perl two-argument `open`; Tcl `expr` without braces; Apps Script `<?!=`; PostgreSQL `trust` over the network; open Firebase rules; disabled TLS checks in a dozen stacks; Supabase `sb_secret_` keys; Zig/Ada safety checks turned off. Comment syntax is respected per language (`--`, `'`, `!`, `;`, `rem`, `&&`).
- `tests/test_scanner_languages.py`: 83 insecure/safe pairs and 8 commented-out cases.
- Evals: from 28 to 35 scenarios (Delphi with Firebird, Clipper on a network share, Lua mods, VBA with the pt-BR decimal comma, CSV for Excel, Redis and MongoDB on a VPS, PowerShell `irm | iex`).
- `benchmark/`: scripts that run the same app request through Claude Code with and without the skill, in a clean configuration, and measure tokens, time, cost, lines of code, build result and security findings (see [docs/BENCHMARK.md](docs/BENCHMARK.md)).

### Changed
- All web references updated: PER Coding Style, PHP 8.5/8.6 gates, Composer advisory blocking, Laravel and Symfony; Node permission model, type stripping, npm 12 install-script approval, Express 5, Next.js 16; Python 3.14/3.15 gates, `pip lock`, Django 6 CSP; Java 25, Spring Boot 4 and Spring Security 7; Trusted Types, strict CSP, WCAG 2.2 and the European Accessibility Act.
- `mysql.md`: LTS and Innovation tracks, MySQL 8.0 end of life (2026-04-30), `mysql_native_password` removed in 9.0, 8.4 removals that break scripts, MariaDB `unix_socket` and PARSEC.
- `security-baseline.md`: passwords follow NIST SP 800-63B-4 (15 characters when the password is the only factor, no composition rules, blocklist); OWASP Top 10 for Agentic Applications and CWE Top 25 2025 in the standards map; bcrypt cost 12 by default.
- `versoes-e-fontes.md`: 36 new rows in the sources table, each with its endoflife.date slug or the vendor page when there is none.
- `compliance-licencas.md`: CRA dates (11 June 2026, 11 September 2026, 11 December 2027) and the 24 h / 72 h / one month reporting chain.
- `qt.md`: open source Qt gets fixes only until the next minor release; the long LTS is commercial. QProcess rules rewritten for Qt 6.
- `gui-desktop.md`, `gui-outros.md`: GTK 4.10 deprecations, Tauri 2 capabilities, Electron defaults by version, Avalonia 12 drag and drop, egui accessibility.
- `c-cpp.md` and `rust.md` rewritten with current hardening flags, sanitizers and supply-chain tools.
- SKILL.md: routing for the new references, legacy and NoSQL pairing rules, and a description that names the new stacks (still under 1024 characters). The style test now covers SKILL.md and every reference.

## [2.1.0] - 2026-11-20

Preventive structure and refactor mode, with ideas adapted from [`untangle-codebase` and `prune-tests`](https://github.com/caldoai/skills) (MIT, © 2026 Maze). The repository now has automated tests, CI and documentation in English, Portuguese and Spanish.

### Added
- **Structure in normal mode.** SKILL.md section 9: before writing, the question "what has to change together with this?"; no copied logic or values, no reaching into another module's internals, no pass-through wrappers, no config for what never varies; "fix the cause, not the case" instead of an `if` for one value, a `sleep`, a retry or an empty `catch`. In existing code the rule is "do not make it worse": it governs what the skill writes, never the code around it. Security code is never treated as surplus.
- `references/estrutura.md`: the full rules with examples, and the rules for writing tests that guard behavior (literal expected values, assert what callers see, never mock the thing under test).
- **Refactor mode, on explicit request only.** SKILL.md section 10, `references/refatoracao-completa.md` and the plugin's `/secops-refatorar` command. It requires Git with a clean working tree and a branch of its own, freezes public contracts, upgrades no dependency, keeps a decision log, checks again until nothing worth fixing is left and ends with a report in pt-BR. Optional additions: comments and tests, with security and regression tests always kept.
- Two new items in the pre-delivery checklist: no copied logic or import of something more volatile, and no new special case where a fix at the cause fits.
- Evals: from 23 to 28 scenarios (shipping cost without duplication, double discount without an `if`, a vague request that does not start a refactor, `/secops-refatorar`, a test with literal values).
- Test suite (`tests/`, standard library only): scanner behavior, consistent versions, references routed from SKILL.md, evals, translations, docs style and ZIP contents.
- GitHub Actions: tests on Linux and Windows with Python 3.8 and current, the claude.ai ZIP attached to every run, CodeQL, and Dependabot for the actions.
- Documentation in three languages (README, CHANGELOG and CONTRIBUTING in English, Portuguese and Spanish), `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue and pull request templates.
- `THIRD_PARTY_NOTICES.md` inside the skill folder, with the credit and MIT license of caldoai/skills. It ships in the ZIP.

### Changed
- Conflict priority: Security > Integrity > Clarity > **Structure** > Token economy > Style.
- `projeto-do-zero.md`: the standard skeleton organizes `src/` by feature, with `comum/` only for what two or more features use.
- `diagnostico.md`: "smallest fix" means the fewest lines at the cause, not a patch over the symptom.
- Skill description: now mentions code structure, tests and "reorganize o projeto", within the 1024-character limit.
- SKILL.md grew from 15,665 to 19,634 bytes because of sections 9 and 10. The details live in the references, loaded only when a task needs them.
- `tools/build_zip.py` takes the output folder as an argument.
- The main README is now in English, with Portuguese and Spanish versions in `docs/`.

## [2.0.2] - 2026-11-16

### Added
- Plugin icon (`.claude-plugin/icon.png`, 1024x1024): a shield with the code symbol. The generator is `tools/make_icon.py`.

## [2.0.1] - 2026-11-16

### Changed
- SKILL.md section 7: the scanner path instruction still makes sense after Claude Code substitutes `${CLAUDE_SKILL_DIR}`. Tested in both scenarios (substituted path and literal placeholder in claude.ai).
- Review report updated with the packaging adjustments.

## [2.0.0] - 2026-11-16

Deep review of the skill. The full report, with findings by severity and the validation performed, is in [docs/ANALISE-v2.0.0.md](docs/ANALISE-v2.0.0.md) (in Portuguese).

### Fixed
- Scanner: a secret could leak in the output when the same line also triggered another rule. The excerpt is now hidden for the whole line.
- Scanner: PEM private keys were never detected, and `.pem` and `.key` files were not read.
- Scanner: false HIGH findings on correct code (`sprintf` in PHP, `prepare()->execute([...])`, `{$wpdb->prefix}`, ordinary string concatenation).
- Scanner: no longer crashes with `UnicodeEncodeError` on the Windows console, and reads UTF-16 files. A parent folder named `build` or `dist` no longer empties the scan, and a missing path returns exit code 2.
- `php.md`: the `.htaccess` now really blocks `/.git/`.
- SKILL.md: the reference budget no longer drops the threat model (`security-baseline.md`). Security comes before token economy.
- SKILL.md: removed the contradiction between "fix every HIGH" and "do not touch anything outside the request".

### Added
- The scanner detects more secrets: `'password' => '...'`, `define('DB_PASSWORD', ...)`, `new PDO(..., "root", "senha")`, `mongodb+srv://`, GitHub, Stripe, Google and Mercado Pago tokens.
- Coverage of WordPress, payments and Pix, Supabase and Firebase, CPF and CNPJ (including the alphanumeric CNPJ), cPanel/`public_html`, Kotlin, PowerShell and shell script.
- Evals: from 17 to 23 scenarios (instruction injection in a file, critical finding outside the scope, false positive, WordPress, Pix, Supabase).
- Packaging: Claude Code plugin and marketplace, ZIP for claude.ai, `license` and `metadata` (authorship and version) in the frontmatter.

### Changed
- The scanner path is built from the skill folder (`${CLAUDE_SKILL_DIR}` in Claude Code), with no fixed path.
- The native-code and GUI checklists moved from SKILL.md to `native-app-security.md` and `gui-desktop.md`. SKILL.md became about 6% smaller.
- The scanner runs on Python 3.8+ and uses only the standard library.

## [1.0.0]

Original version of the skill, created by Alex Camacho Castilho.
