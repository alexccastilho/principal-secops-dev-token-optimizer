*Read this in other languages: [Português (Brasil)](docs/CHANGELOG.pt-BR.md) · [Español](docs/CHANGELOG.es.md)*

# Changelog

All notable changes to this project. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [SemVer](https://semver.org/).

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
- SKILL.md grew from 15,665 to 19,240 bytes because of sections 9 and 10. The details live in the references, loaded only when a task needs them.
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
