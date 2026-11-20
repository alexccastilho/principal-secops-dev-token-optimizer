# Refactor benchmark: hypotheses and metrics, fixed before any run

Written on 2026-11-20, before the first paid run. The results are published whatever they show; a change to this file after the runs is listed at its end with the reason.

## Hypotheses

1. **Bug fix (`bugfix`).** With the skill, the agent reads less of the project, changes fewer lines and spends fewer output tokens, at the same or better rate of correct fixes. This is where the skill's reading and minimal-scope rules apply most directly.
2. **Review (`review`).** With the skill, the answer finds as many planted issues or more, with fewer false claims, in fewer words.
3. **Refactor (`refactor`).** With the skill, behavior is preserved more often (contract and original tests pass) and the public API stays identical; the run costs more, because of the skill's start message, plan and decision log.

Any of the three may come out false. That is a result, not a reason to rerun.

## Metrics, per run

| Metric | How it is measured | Tasks |
|---|---|---|
| Output tokens, total input tokens, cost, time, turns | from the Claude Code result events, summed over auto-replies | all |
| Project characters read, project read calls | size of Read, Grep and Glob results on paths inside the project | all |
| Skill characters read | the same, for paths inside the exported plugin | all |
| Correct fix | hidden `test_bugfix` passes | bugfix |
| Behavior preserved | hidden `test_contract` passes **and** the fixture's original visible tests pass against the agent's code | bugfix, refactor |
| Tests as left | the project's tests in the state the agent left them | bugfix, refactor |
| Size of the change | files touched, lines added and removed, against the pristine fixture | bugfix, refactor |
| Scanner HIGH findings after the run | `revisar_codigo.py` on the result (before: the fixture's count) | bugfix, refactor |
| Answer words | words in all final answers of the run | all |
| Planted issues found, and false claims | blind grading of the review answers against `manifest/<lang>.json`; recall reported separately for issues the skill's scanner detects and for those it does not | review |

**Security issues in the refactor task are reported, not scored.** The skill's refactor mode keeps every security rule but freezes contracts; fixing S1 to S8 there is allowed, not required. The scanner count after the run is shown for information.

## Validity checks, per run

- The baseline never called the skill; the skill condition did call it (runs where it did not are flagged and kept).
- No Read, Grep or Glob outside the project folder and the exported plugin.
- Auto-replies: the same text and the same rule for both conditions (a session that ends with a question in its last paragraph gets a reply, at most 3 times).

## Design

Python and Node, 3 tasks, 2 conditions, 3 repetitions: 36 runs. Same model (`sonnet`), same isolated configuration and permissions as the first benchmark, plus the project's test commands and the git subcommands a refactor uses.

## Changes after the runs

- **2026-11-20, after the first full run.** The auto-reply rule now applies to the refactor task only, and also recognizes an explicit request for "pode" without a question mark. Reason: the first run stopped every skill refactor at the start message, and replying in the review task let sessions change files. Under the new rule, the 6 refactor runs without the skill would have received the same replies, so they stay valid; the 10 affected runs were excluded and not repeated. See `docs/BENCHMARK-REFACTOR.md`.
