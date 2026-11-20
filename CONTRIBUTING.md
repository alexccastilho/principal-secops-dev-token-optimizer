*Read this in other languages: [Português (Brasil)](docs/CONTRIBUTING.pt-BR.md) · [Español](docs/CONTRIBUTING.es.md)*

# Contributing

Thank you for considering a contribution. This document covers what is in scope, how to test a change and the conventions the skill relies on. The user-facing documentation is the [README](README.md).

## What this project is

A skill, not an application: `skills/principal-secops-dev-token-optimizer/SKILL.md` and the files it routes to are instructions that Claude reads. Most contributions are changes to text, and a change to text changes behavior. Treat a sentence in `SKILL.md` the way you would treat a line of code.

The audience is fixed: a person who **does not program**, answered in plain Brazilian Portuguese. Contributions that make answers longer, more technical or less safe for that person are out of scope, even when they are correct.

## Priorities

Every change is judged by the same order the skill uses for conflicts:

1. **Security.** Never weaken the baseline, the threat model or the pre-delivery gate.
2. **System integrity.** The skill must never break working code: minimal scope, preserved contracts, explicit permission for destructive actions.
3. **User clarity.** Plain pt-BR, one apply-and-test instruction, no jargon without a translation.
4. **Structure.** Code that stays easy to change (section 9 of `SKILL.md`).
5. **Token economy.** `SKILL.md` is loaded every time the skill triggers. Detail belongs in a reference, loaded on demand.
6. **Style.**

## Setting up

You need Git and Python 3.8 or newer. Nothing else: the scanner, the tests and the tools use only the standard library, on purpose. The skill runs in claude.ai sandboxes and on machines of people who do not program, where installing a package is a step that fails.

```bash
git clone https://github.com/alexccastilho/principal-secops-dev-token-optimizer.git
cd principal-secops-dev-token-optimizer
python -B -m unittest discover -s tests -v
```

`tools/make_icon.py` is the only exception: it needs Pillow, and only to redraw the icon.

## Testing a change

- **The test suite** must pass before and after your change. GitHub Actions runs it on Linux and Windows, with Python 3.8 and the current version.
- **Scanner changes** need a test in `tests/test_scanner.py` with a snippet that must be flagged and one that must not. A false positive is as serious as a false negative: with "deliver only with zero HIGH", a false positive makes Claude rewrite working code.
- **Changes to `SKILL.md` or a reference** need a manual check: try at least one affected scenario from `evals/evals.json` in Claude Code (`claude --plugin-dir .`) or by uploading the ZIP to claude.ai, and compare the answer with its assertions. If the behavior is new, add a scenario.
- **Never paste a real secret** in a test, an eval or an issue. Use obviously fake values.

## Conventions

### Wiring the skill

- Every file in `references/` must be routed from the table in section 6 of `SKILL.md`. A reference nobody routes to is dead text, and a route to a missing file is a broken promise. The test suite checks both.
- The `SKILL.md` description stays at or under 1024 characters, the limit of the skill format.
- Section numbers in `SKILL.md` are referenced from other files ("section 4, rule 9"). Add new sections at the end instead of renumbering.
- Reference files are written in English, like `SKILL.md`. Text the skill shows the user (sample answers, questions, file names like `LEIA-ME.md`) is in pt-BR.

### Versions and releases

- The version lives in two places, `.claude-plugin/plugin.json` and `metadata.version` in `SKILL.md`, and must match the first entry of the three changelogs. The test suite checks it.
- A release: bump both, add the entry to `CHANGELOG.md`, `docs/CHANGELOG.pt-BR.md` and `docs/CHANGELOG.es.md`, run `python tools/build_zip.py`, and attach the ZIP from `dist/` to the GitHub release.

### Documentation in three languages

README, CHANGELOG and CONTRIBUTING exist in English (root), Portuguese and Spanish (`docs/`). A change to one is made to the three in the same pull request, and the READMEs keep the same sections.

The docs read like a person wrote them: no em or en dash as an aside, straight quotes, three dots instead of the ellipsis character, no inflated vocabulary. The test suite fails on the first forbidden character.

### Third-party work

Parts of the skill adapt [caldoai/skills](https://github.com/caldoai/skills) (MIT). If you adapt more third-party work, its license must allow it, and the credit and license text go into `skills/principal-secops-dev-token-optimizer/THIRD_PARTY_NOTICES.md`, which ships inside the ZIP.

### Commits

One self-contained change per commit, with a message that says what and why. Do not mix a mass rename or reformatting with a behavior change.

## Reporting

Bugs and ideas: open an issue with the templates. Security vulnerabilities: never in a public issue; see [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contribution is licensed under the MIT License, the same license as the rest of the project (see [LICENSE](LICENSE)).
