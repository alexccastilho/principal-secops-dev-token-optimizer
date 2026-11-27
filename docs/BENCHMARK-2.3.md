# Benchmark of 2.3.0 (partial): without the skill, 2.2.1 and 2.3.0

[Português](BENCHMARK-2.3.pt-BR.md) · [Español](BENCHMARK-2.3.es.md) · [First benchmark](BENCHMARK.md) · [Refactor benchmark](BENCHMARK-REFACTOR.md)

Run on 2026-11-25 with Claude Code 2.1.332, the `sonnet` model (`claude-sonnet-5-5`), on Windows 11, in the isolated configuration of `benchmark/run_benchmark.py`. Three conditions: no skill, version 2.2.1 and version 2.3.0. Version 2.3.0 was measured from the working tree of the `v2.3` branch before its first commit, so its runs record the base commit with `-dirty`. **This run is partial:** three languages instead of six, two or three repetitions per cell, and one model. The raw summaries, the blind grades and the label mappings are in [benchmark/results/2.3.0/](../benchmark/results/2.3.0/). The second new-app round is in `custos2.json` and `create2-summary.json`. In 2.3.1 the summaries were recomputed from the same runs, with no new model call: cost with three decimals, C# build as not checked (0/0) instead of failed, and the Node.js original tests of the refactor suite as 3/3; a wrong test command had recorded them as 0/3.

## Short version

- **Activation:** 2.3.0 loaded for every kind of code request tested and for none of the non-code ones. 2.2.1 never loaded for a bug fix on an existing project, a new field, a new table, a dependency upgrade or writing tests.
- **Cost:** with the skill working in both, 2.3.0 was not more expensive than 2.2.1 (USD 1.61 against 1.73 for the three apps, 0.75 against 0.81 for the two reviews), a difference within the noise of two or three repetitions. A small bug fix now costs USD 0.10 instead of 0.06, because the skill now loads for it; 2.2.1 did not load, so that run was the model alone.
- **Quality:** in blind reviews, the 2.3.0 apps were as secure as the 2.2.1 apps or more, and easier for a non-programmer to run. 2.3.0 reviews found as many planted issues as the others, with no false claims.
- **Not verified:** C# could not be compiled (no .NET SDK on the test machine) in any condition. One 2.3.0 Node.js app was delivered without its two packages declared in `package.json`.

## Activation

Ten prompts that should load the skill and four that should not, in Python and Node.js projects, two repetitions each (4 runs per prompt). The criterion of gate 5 was written down before the 2.3.0 runs (`gate5-preregistro.md` in the results folder).

| Prompt | No skill | 2.2.1 | 2.3.0 |
|---|---|---|---|
| a01 review the code, most serious problem | 0/4 | 4/4 | 4/4 |
| a02 any security problem? | 0/4 | 4/4 | 4/4 |
| a03 order total wrong with a discount, fix it | 0/4 | 4/4 | 4/4 |
| a04 error when saving a client without phone | 0/4 | 2/4 | 4/4 |
| a05 add a CPF field | 0/4 | 0/4 | 4/4 |
| a06 is it safe to put online? | 0/4 | 4/4 | 4/4 |
| a07 update the dependencies | 0/4 | 0/4 | 4/4 |
| a08 create a suppliers table | 0/4 | 0/4 | 4/4 |
| a09 sales report is slow | 0/4 | 4/4 | 4/4 |
| a10 write tests for the discount | 0/4 | 0/4 | 3/4 |
| n01 to n04 (LGPD question, e-mail, capital, translation) | 0/16 | 0/16 | 0/16 |
| Refactor suite: review | 0/6 | 6/6 | 6/6 |
| Refactor suite: bug fix | 0/6 | 0/6 | 6/6 |

The 2.3.0 description was chosen in a small pilot on the bug-fix task before this run: the first draft loaded in 0 of 4 bug fixes and the final wording ("load before the first edit to any code file, even for a one-line fix") in 4 of 4.

## New app (contacts with login and SQLite)

Two repetitions per language. The first 2.3.0 run lost on delivery in the blind review: its apps asked the user to type commands in a terminal. The rule on proportional delivery was changed so that a non-programmer always gets a double-click launcher and the prerequisites with their links, and the 2.3.0 apps were built again. The table shows that second run.

| Language | Condition | Cost (USD) | Output tokens | Cache writes | Cache reads | Turns | Time (s) |
|---|---|---|---|---|---|---|---|
| Python | no skill | 0.123 | 6,599 | 12,540 | 69,268 | 5 | 47 |
| Python | 2.2.1 | 0.488 | 21,069 | 51,769 | 699,964 | 30.5 | 163 |
| Python | 2.3.0 | 0.440 | 18,458 | 47,462 | 659,290 | 35 | 135 |
| Node.js | no skill | 0.262 | 14,842 | 21,289 | 286,184 | 14.5 | 93 |
| Node.js | 2.2.1 | 0.582 | 26,687 | 59,248 | 781,052 | 37 | 174 |
| Node.js | 2.3.0 | 0.553 | 26,655 | 54,129 | 695,806 | 43 | 172 |
| C# | no skill | 0.257 | 15,280 | 22,648 | 137,148 | 17.5 | 89 |
| C# | 2.2.1 | 0.655 | 31,094 | 71,730 | 557,400 | 35.5 | 199 |
| C# | 2.3.0 | 0.621 | 31,828 | 60,784 | 598,422 | 45.5 | 199 |

Total for the three apps: USD 1.614 with 2.3.0 against 1.725 with 2.2.1 and 0.642 without the skill. With two repetitions this is noise-sized: in the first 2.3.0 run, Python cost 6% more than 2.2.1 and C# 24% less. 2.3.0 takes more turns (it checks versions live and compiles before delivering), but each turn carries less: fewer cache writes and less output in Python.

**Builds.** Python and Node.js compiled in every run of every condition. C# was not compiled in any condition: the test machine has no .NET SDK, so this is not verified.

**Works as delivered.** 11 of the 12 runs of 2.3.0 ran the scanner with `--entrega`. The one that did not was a Node.js app whose `npm install` was blocked by the test harness; it left `package.json` without `express` and `helmet`. Its launcher installs them, but a plain `npm start` on a fresh copy fails. A sentence was added to the gate after this run (write the dependency into the manifest by hand when an install is blocked); that sentence was not measured.

**Blind review.** A separate model graded one app per language and condition, with random labels and no paths that could reveal the condition, on security and on delivery for a non-programmer (1 to 10). It was done twice, by two graders: the first with the first 2.3.0 run, the second with the rebuilt apps. The second rubric added two delivery criteria (no typing in a terminal, every prerequisite named) that are the same rules added to the skill between the rounds, so the round 2 delivery grade is partly measured against the fix itself. The security criteria were the same in both rounds.

| Condition | Security, round 1 | Delivery, round 1 | Security, round 2 | Delivery, round 2 |
|---|---|---|---|---|
| No skill | 7.3 | 6.0 | 6.0 | 4.3 |
| 2.2.1 | 8.7 | 7.0 | 8.0 | 6.0 |
| 2.3.0 | 8.7 | 5.7 | 9.0 | 7.7 |

The same no-skill and 2.2.1 apps got different grades from the two graders, so compare conditions within a round, not across rounds. The only defect marked critical was in one no-skill Node.js app, graded in both rounds (first-run setup without CSRF protection).

**Scanner.** No real HIGH in any app. Two 2.3.0 Node.js apps triggered a HIGH on `db.exec(\`PRAGMA user_version = ${n}\`)`, where the number comes from a validated file name: the `child-process-exec` rule mistakes SQLite's `exec` for the one in `child_process`. That rule predates 2.3.0 and will be narrowed later. The Node.js app that skipped the gate also has two `sql-template-js` findings on a constant `WHERE` fragment, with every value passed as a parameter; also false positives.

## Existing project (refactor suite)

The 2,700-line practice project of the [refactor benchmark](BENCHMARK-REFACTOR.md), three repetitions.

| Task | Language | No skill | 2.2.1 | 2.3.0 |
|---|---|---|---|---|
| Review, cost (USD) | Python | 0.365 | 0.416 | 0.386 |
| Review, cost (USD) | Node.js | 0.357 | 0.389 | 0.359 |
| Bug fix, cost (USD) | Python | 0.060 | 0.058 (skill not loaded) | 0.100 |
| Bug fix, cost (USD) | Node.js | 0.058 | 0.058 (skill not loaded) | 0.098 |
| Bug fix solved | both | 6/6 | 6/6 | 6/6 |

The 18 review answers were graded blind against the answer key (`benchmark/refactor/manifest/`):

| Condition | Planted issues found (average of 13) | False claims (total) | Most serious problem named correctly |
|---|---|---|---|
| No skill | 10.8 | 4 | 6/6 |
| 2.2.1 | 11.2 | 2 | 4/6 |
| 2.3.0 | 11.3 | 0 | 6/6 |

The grader counted SQL injection as the most serious class; the two 2.2.1 answers that put MD5 hashing first are the ones marked wrong.

## Gates for publishing

| Gate | Result |
|---|---|
| 1. Tests pass and the ZIP builds | Passed: 57 tests |
| 2. Every new app compiles | **Accepted by the owner on 2026-11-25.** Python and Node.js compiled 8 of 8; C# could not be checked in any condition; one Node.js app fails a plain `npm start` |
| 3. Security at least that of 2.2.1 | Passed in both blind rounds |
| 4. Cost per working delivery at most that of 2.2.1 | **Accepted by the owner on 2026-11-25.** Not more expensive where the skill works in both (new app, review); the bug fix costs USD 0.04 more, the price of loading on every edit, which 2.2.1 did not do |
| 5. Activation (pre-registered criteria) | Passed: bug fix 6/6, prompts 2.2.1 missed 19/20, no regression 26/26, non-code 0/16 |

## Limits

Three languages, two or three repetitions per cell and one model: a difference of a few cents per app is within the noise. Every run had only this plugin installed, so working alongside other skills (section 11) was not measured. The activation and review runs used `SKILL.md` before its last two sentences (launcher and blocked install). The pilot that chose the description used the bug-fix task, which is also measured here. The proportional-delivery rule was corrected after the first blind review and only the creation suite was run again. The harness blocks package installs and running servers, which is stricter than a real session.
