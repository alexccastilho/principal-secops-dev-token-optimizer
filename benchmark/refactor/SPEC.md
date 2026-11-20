# Refactor benchmark: fixture specification

This folder holds the inputs of the second benchmark: existing code that the agent must review, fix or refactor. The agent under test never sees this folder. The harness copies only `fixtures/<lang>/` into the run folder, and loads the skill from an exported copy that holds nothing but the plugin.

## Layout

```
benchmark/refactor/
  SPEC.md                    this file
  manifest/<lang>.json       planted issues and the bug (the answer key)
  validate.py                offline proof that the fixtures, hidden tests and references agree
  fixtures/<lang>/           the project the agent receives (becomes a Git repo at run time)
  hidden/<lang>/             tests the agent never sees, run after the session
  reference/<lang>/bugfix/   full copy of the fixture with only the bug fixed
  reference/<lang>/refactor/ full copy of the fixture, heavily restructured, same public contract
```

Languages: `python` (stdlib only, `sqlite3`, `unittest`, Python 3.10+) and `node` (Node 22.5+ built-ins only: `node:sqlite`, `node:test`, `node:assert`; CommonJS; no `package.json` dependencies).

## The project

"Loja do Bairro": back office of a small Brazilian shop, written years ago by several people. Library plus a small CLI, SQLite storage, no web server. Code, identifiers, comments and messages in Portuguese, as a real pt-BR codebase would be.

Modules (names are a guide; keep them plausible):
- customers (clientes): CRUD, CPF validation, e-mail validation, phone formatting, search by name.
- products and stock (produtos, estoque): CRUD, stock movements, low-stock list.
- orders (pedidos): create order with items, total, discount rules, payment status, cancel with stock return.
- users and login (usuarios, autenticacao): create user, password check, session token, roles `admin` and `vendedor`.
- reports (relatorios): sales by period, top products, CSV export of customers and orders, ordering by a column name.
- utilities (util): Brazilian date and money formatting, CEP formatting, CPF/CNPJ helpers.
- CLI entry (`cli.py` / `cli.js`) with a handful of commands.

**Size: 2,500 to 3,500 source lines (without tests), in 12 to 20 files.** The size matters: reading discipline only shows on a project too big to read whole for free. Realistic code, not filler: docstrings or comments where an ordinary team would write them, some stale, some missing.

## Public contract (frozen)

- Python: everything exported by `loja/__init__.py` (an explicit `__all__`), plus the CLI commands and their output format.
- Node: everything exported by `index.js` at the project root, plus the CLI commands and their output format.
- Functions take and return plain values (dicts / objects, lists, numbers in centavos as integers, strings). A database path or connection is passed in, so tests can use a temporary file.
- The README of the fixture describes the business rules and says how to run the tests, as a real project README would. It must not mention planted issues, benchmarks or the skill.

## Planted issues (identical set in both languages)

Record each in `manifest/<lang>.json` (a JSON list) with: `id`, `kind` (`security`, `quality` or `bug`), `files` and line ranges, `scanner_detectable` (true if `skills/principal-secops-dev-token-optimizer/scripts/revisar_codigo.py` flags it; check by running the scanner), a one-line `description` in English, and `accept` (short phrases a grader can use to recognize the issue in an answer).

Security:
- `S1` SQL built by string concatenation in customer search by name.
- `S2` report ordering column taken from the caller and put into `ORDER BY` unchecked.
- `S3` passwords hashed with unsalted MD5.
- `S4` hard-coded signing secret for session tokens (a plain phrase such as `"loja-bairro-2019"`; it must match no real provider key pattern).
- `S5` session token generated with a non-cryptographic random generator.
- `S6` missing ownership/role check: a `vendedor` can read or cancel any order, although the README says sellers only see their own orders.
- `S7` CSV export writes customer-supplied text as is (spreadsheet formula injection).
- `S8` stock update swallows a database error and reports success.

Quality:
- `Q1` CPF and e-mail validation copied in three places, with small differences between the copies.
- `Q2` dead code: at least two functions and one whole helper module that nothing calls.
- `Q3` one order-processing function of 120+ lines doing validation, pricing, stock and persistence.
- `Q4` discount rules written as magic numbers in two places that disagree with each other only for coupons (not for the bug below).

Bug (for the bug-fix task):
- `B1` The README rule: "Pedidos a partir de R$ 500,00 têm 10% de desconto." The code applies the discount only when the total is **greater than** 500,00, so an order of exactly R$ 500,00 gets no discount. It lives in one place in the pricing path (the Q4 duplicate must not contain this threshold, so there is exactly one correct fix site).

No marker comments, no `TODO: vulnerable`, no telling names (`unsafe_`, `bug_`, `legacy_bad`). The code should look like ordinary code written in a hurry.

## Visible tests (`fixtures/<lang>/tests/`)

An ordinary, incomplete suite: 25 to 40 tests over the main flows. All pass on the fixture. None covers the B1 boundary, S1 to S8, or the dead code.

## Hidden tests (`hidden/<lang>/`)

They import only the public contract (Python: `import loja` with the project root on `sys.path`; Node: `require(<project root>/index.js)`, the root given by the environment variable `PROJECT_ROOT`).

- `test_bugfix` (Python `test_bugfix.py`, Node `bugfix.test.js`): an order of exactly R$ 500,00 gets 10% off; R$ 499,99 gets none; R$ 500,01 gets 10%. **Fails on the fixture, passes on `reference/<lang>/bugfix`.**
- `test_contract` (`test_contract.py`, `contract.test.js`): 30 to 50 tests of the public contract with benign inputs: every exported function, the CLI output format, totals away from the 500,00 boundary. Must pass on the fixture, on both references, and on any honest refactor. Never tests the B1 boundary, malicious input, wrong-owner access or exact error message wording.

## References

- `reference/<lang>/bugfix/`: the fixture with only B1 fixed (one-line change plus, optionally, one visible test).
- `reference/<lang>/refactor/`: the fixture restructured hard (validation centralized, Q3 split, dead code removed, internal modules moved or renamed) while `loja/__init__.py` / `index.js` keep the same exports. Security issues may be fixed or left; B1 left as is.

## validate.py must prove, per language

1. Visible tests pass on the fixture.
2. Hidden `test_contract` passes on the fixture, on `reference/bugfix` and on `reference/refactor`.
3. Hidden `test_bugfix` fails on the fixture and passes on `reference/bugfix`.
4. The fixture contains no word from a short tell list (`vulner`, `inseguro`, `benchmark`, `planted`, `TODO`, `FIXME`, `bug`).
5. Source size within 2,500 to 3,500 lines.
6. Every `scanner_detectable: true` issue is flagged by the scanner at the recorded file, and every `false` one is not.
