## What does this change?

A short description of what this pull request does and why.

## Related issue

Closes #

## How was this tested?

- [ ] The test suite passes: `python -B -m unittest discover -s tests`
- [ ] If I changed `SKILL.md` or a reference, I tried at least one affected scenario from `evals/evals.json` in Claude Code or claude.ai
- [ ] If I changed the scanner, I added a test with a snippet that must be flagged and one that must not

## Checklist

- [ ] The change follows [CONTRIBUTING.md](../CONTRIBUTING.md): security first, never break working code, minimal scope, stdlib-only Python
- [ ] `SKILL.md` description stays at or under 1024 characters, and every reference file is routed from `SKILL.md`
- [ ] User-facing documentation I touched is updated in the three languages (English, Português, Español)
- [ ] The version is bumped in `plugin.json` and `SKILL.md`, with an entry in the three changelogs, if this is a release
- [ ] No dash asides, ellipsis characters or curly quotes in the docs (the test suite checks it)
