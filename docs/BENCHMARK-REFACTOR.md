# Refactor benchmark (partial): existing code, with and without the skill

[Português](BENCHMARK-REFACTOR.pt-BR.md) · [Español](BENCHMARK-REFACTOR.es.md) · [First benchmark: a new app](BENCHMARK.md)

Run on 2026-11-20 with skill version 2.2.0, Claude Code 2.1.329, the `sonnet` model, on Windows 11. **This run is partial:** 26 of 36 runs are valid, and none of the valid ones has the skill actually working. What follows is what the valid runs show, and why the rest is missing.

## Short version

- **The skill was never activated in the review and bug-fix requests.** It was installed in the "with skill" condition, and its description names "bug fix" and "security review", but in 12 of 12 runs the model answered without calling it. So those two tasks compare the model against itself; the differences between conditions are noise.
- **The skill's refactor runs are not valid.** The skill's refactor mode stops and asks for "pode" before it starts. The harness was meant to answer that, but it only recognized questions ending in "?", and the skill's message asks without one. All 6 skill refactor runs stopped at the start message. The harness is fixed; the runs were not repeated, by the owner's decision, to limit spending.
- **None of the three hypotheses in [METRICS.md](../benchmark/refactor/METRICS.md) could be tested.**

The finding that matters for whoever uses the skill: **for a review or a small fix, installing it is not enough; it has to be asked for** (for example, "use the principal-secops-dev-token-optimizer skill"). A whole-project refactor request does activate it (6 of 6).

## The setup

An existing back office for a small shop ("Loja do Bairro"), written in a hurry, about 2,700 source lines, in Python and in Node.js. Each version has the same 8 planted security issues, 4 quality problems and 1 bug, with no comment pointing at them. Three requests, written as a shop owner would:

1. **Review:** "Revise o código deste projeto e me diga quais problemas ele tem, do mais grave para o menos grave. Não altere nenhum arquivo."
2. **Bug fix:** "Um cliente fez um pedido de exatamente R$ 500,00 e não recebeu o desconto de 10% que a regra da loja promete. Corrija isso."
3. **Refactor:** "Refatore este projeto inteiro para ficar mais fácil de manter, sem mudar o comportamento. O projeto já está no Git, com a árvore limpa."

Hidden tests, which the agent never sees, check the fix and that the public API is unchanged. The skill is loaded from a copy that holds only the plugin, so neither condition can reach the answer key. Fixtures, hidden tests, answer key and validator: [benchmark/refactor/](../benchmark/refactor/).

## Valid results

Averages per cell. "Behavior preserved" means the hidden contract tests and the project's original tests both pass on the code the agent left.

| Task | Language | Condition (skill called?) | Runs | Time (s) | Output tokens | Cost (USD) | Files / lines changed | Correct fix | Behavior preserved |
|---|---|---|---|---|---|---|---|---|---|
| Bug fix | Python | without | 3 | 17 | 1,542 | 0.08 | 1.3 / 5 | 3/3 | 3/3 |
| Bug fix | Python | with (not called) | 2 | 19 | 2,000 | 0.08 | 2 / 11 | 2/2 | 2/2 |
| Bug fix | Node.js | without | 3 | 11 | 867 | 0.07 | 1 / 2 | 3/3 | 3/3 |
| Bug fix | Node.js | with (not called) | 3 | 16 | 1,652 | 0.08 | 1.7 / 11 | 3/3 | 3/3 |
| Review | Python | without | 2 | 91 | 11,879 | 0.41 | 0 | n/a | 2/2 |
| Review | Python | with (not called) | 2 | 83 | 10,348 | 0.38 | 0 | n/a | 2/2 |
| Review | Node.js | without | 3 | 54 | 6,162 | 0.36 | 0 | n/a | 3/3 |
| Review | Node.js | with (not called) | 2 | 82 | 10,493 | 0.45 | 0 | n/a | 2/2 |
| Refactor | Python | without | 3 | 238 | 36,034 | 1.26 | 7.7 / 318 | n/a | 3/3 |
| Refactor | Node.js | without | 3 | 575 | 87,645 | 2.91 | 17.3 / 1,865 | n/a | 3/3 |

What the valid runs do show, independent of the skill:

- **The bug is easy to fix for the model alone.** All 11 bug-fix runs fixed it, in 10 to 20 seconds and under USD 0.10, touching one or two files.
- **A refactor without the skill preserved behavior in 6 of 6 runs**, at USD 1.26 (Python) to 2.91 (Node.js) per run. In one Node.js run it also fixed the R$ 500,00 boundary without being asked, which changes behavior the README says is wrong.
- **The review answers were not graded.** Since the skill was not called in any of them, a blind grading would compare the model with itself.

## Excluded runs

Ten runs are kept apart, not deleted, and listed here:

- The 6 refactor runs with the skill, stopped at the skill's start message (harness defect above).
- 4 review and bug-fix runs where the harness answered "pode seguir" to an offer such as "quer que eu corrija?". In a review that told the agent not to change files, that reply authorized changes. The harness now replies only in the refactor task.

## Cost

USD 22.16 in total, including the excluded runs.

## Next step

To measure the skill itself on existing code, either the request names it, in both conditions, or the skill's description is changed so a review or a fix calls it on its own. Either way, the harness now handles the refactor mode's "pode". Reproduce with:

```
python benchmark/refactor/validate.py
python benchmark/run_benchmark.py --suite refactor --config-dir cfg --out ../bench-refactor --reps 3 --jobs 3 --timeout 2400
python benchmark/analyze_refactor.py --runs ../bench-refactor
```

The same warnings as the [first benchmark](BENCHMARK.md#reproduce) apply: it spends tokens on the copied login, and it should run in a sandbox.
