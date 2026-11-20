# Estrutura: write code that stays easy to change

Based in part on `untangle-codebase` and `prune-tests` from caldoai/skills (MIT, Copyright (c) 2026 Maze). See `THIRD_PARTY_NOTICES.md` in this skill's folder.

## Contents
- The one question
- Three ways to get it wrong
- Special cases: fix the cause
- Where code lives
- Tests that guard behavior
- Existing code: do not make it worse
- Security code is never surplus
- Checklist

Goal: every change the user asks for next month lands in one place, and nothing breaks silently when it does.

## The one question

Before writing, ask: **what has to change together with this?**

* Pieces that change together end up together.
* Pieces that change for different reasons are not tied to each other.
* Everything depends on what changes less than itself.

A rule that looks cleaner but breaks one of these three is not cleaner.

## Three ways to get it wrong

**Hidden links:** pieces that must change together, where the code does not show it.

| In the code | Why it hurts | Do instead |
|---|---|---|
| The same rule or value in two places (a price formula in the cart and in the invoice, `0.1` tax in three files) | change one, forget the other, the numbers disagree | one function or constant, used by both |
| A module reads a global, a session key or a file another module writes | change the writer, the reader breaks, nothing points to it | pass the value in, or give it one owner with a named function |
| A feature split across `controllers/`, `models/`, `views/` | one change needs three folders, the layout hides it | the feature's folder holds its routes, rules, queries and templates |
| Callers must call `init()` before `run()`, or pass arguments in a magic order | change it, callers break, nothing warns them | make the wrong order impossible: one call, or a constructor that does the setup |

**Needless links:** pieces tied together that change for different reasons.

| In the code | Do instead |
|---|---|
| Code reads another module's internal array, private field or table it does not own | ask the owner through a function that says what it means |
| Stable code (rules, calculations) imports something volatile (a payment SDK, an HTTP client, the UI) | the stable code defines what it needs; the volatile part plugs in from outside |
| A general function grows a parameter only one screen understands (`format_price($v, $is_checkout_page)`) | the special part stays in that screen; the general function stays general |
| A module whose interface mirrors its internals (one public function per private step) | fewer, deeper functions: the caller says what, the module decides how |

**Surplus:** pieces with no reason of their own to change.

* A wrapper that only forwards to another function.
* Config, a plugin hook or an interface for something that has one implementation and no plan for a second.
* Code nothing calls anymore. When your change makes something unused, remove it in the same change.

## Special cases: fix the cause

Each of these is a requirement the design never accounted for. Adding one more hides the real problem and makes the next bug harder to find.

| Special case | Usually means | Fix |
|---|---|---|
| `if ($id == 42)`, `if (user == "admin2")` | a rule that applies to more than one value, never named | name the rule, store it as data, apply it to everyone |
| a parameter for one specific caller | the function does two jobs | split it, or move the special part to the caller |
| `sleep`, `setTimeout(..., 100)`, a retry loop | an order of events nobody controls | wait for the event itself: a callback, a promise, a lock, a transaction |
| an empty `catch`, `@` before a call, `except: pass` | an error nobody decided how to handle | handle it (section 5 of SKILL.md: generic to the user, detailed to the log, deny on failure) or let it surface |
| a skipped or disabled test | a behavior nobody agrees on | decide the behavior, then fix the code or the test |

When the cause is outside the request, do not chase it: apply the minimal fix, and say in one line where the cause is and that you can fix it next.

## Where code lives

* **Group by feature, not by layer.** `src/pedidos/` holds everything about orders. A shared folder (`src/comum/`) holds only what two or more features really use: the database connection, login, the layout.
* **Colocate.** The test, the template and the query of a feature sit next to its code.
* **One owner per piece of data.** Each table, session key or file has one module that writes it. Others ask that module.
* **Configuration only for what varies.** Values that differ between computers (passwords, hosts, paths) go to `.env`. A value that is the same everywhere is a named constant in the code, not config.
* **Depth over count.** A module with a small interface and real work behind it beats five thin files that only call each other.

For a project from scratch, `projeto-do-zero.md` applies these rules to the standard skeleton.

## Tests that guard behavior

A test should fail on a regression, and only on a regression. When writing tests:

* **Literal expected values.** `assert apply_discount(100, 0.2) == 80`, never `== price - price * 0.2`: a test that repeats the code's formula passes when the formula is wrong.
* **Test what callers see.** Assert the result, the response, the saved row. Never private fields, internal call order or which helper ran.
* **Never mock the thing under test.** Mock only what is outside it: the network, the clock, a payment provider.
* **No test that cannot fail.** Do not test that the browser renders a `<button>`, or what the type system already guarantees.
* **One behavior, one test.** A second test of the same behavior at the same layer adds maintenance and no protection.
* **No production code only for tests.** No `_resetForTests()` in the real code; build the state through the public interface.

Security tests are the exception to "one behavior, one test": checking the same permission at the route and at the service is defense in depth. Keep both.

## Existing code: do not make it worse

These rules apply to what you write in the current task. They never authorize restructuring the code around it (SKILL.md, section 4, rule 2).

* The new code follows the rules above, even when the file around it does not.
* When the clean way needs a change outside the request (moving a duplicated rule to one place, splitting a module), do the minimal change and add one line: "Para essa mudança ficar num lugar só no futuro, dá para juntar as duas cópias da regra de frete. Quer que eu faça?"
* Never copy an existing duplication "to stay consistent". Consistency with a problem spreads the problem.
* When the whole project needs cleaning, that is refactor mode (SKILL.md, section 10), and only on explicit request.

## Security code is never surplus

* Authorization checks repeated in many routes may be moved to one middleware or guard. They are never removed as "duplicates" until every route goes through the central check.
* A `try/catch` that denies access on failure is not a swallowed exception. It keeps denying after any change.
* Input validation stays at the entry point even when an inner layer validates again.
* A test that checks a removed insecure endpoint stays gone guards a real regression. Keep it.

## Checklist

```
- [ ] Every new piece lives with the feature it serves
- [ ] No rule or value copied; the second use calls the first
- [ ] Nothing reads internals or globals owned by another module
- [ ] Nothing stable imports something more volatile
- [ ] No new special case where a fix at the cause fits, or the cause is named in one line
- [ ] No wrapper, config or extension point without a second real use
- [ ] Code made unused by this change is removed
- [ ] New tests use literal expected values and assert what callers see
- [ ] No security check, deny-on-failure handler or security test removed
```
