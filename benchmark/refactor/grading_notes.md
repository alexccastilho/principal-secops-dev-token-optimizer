# Grading notes for the review task

A review finding counts as **found** when it matches an entry of `manifest/<lang>.json` (its `accept` phrases help). It counts as a **false claim** only when it is wrong about the code: the problem does not exist, or is described at a place where it is not.

These weaknesses were not planted but are real. A review that raises them gets neither credit nor penalty:

**Python**
- `registrar_pagamento` and the CLI commands `pagar` and `usuario-add` take no acting user, so they check no role.
- Password hashes are compared with `==`, not in constant time.
- `loja/db.py` builds `PRAGMA`, `ALTER TABLE` and `COUNT(*)` statements with `%` from table and column names. The names come from the code itself, never from input, so this is a style point, not an injection.
- `UPDATE clientes SET ...` in `loja/clientes.py` is assembled from field names taken from a fixed list.

**Node**
- Password hashes are compared with `===`, not in constant time.
- The S4 secret, S5 `Math.random()` and S3 MD5 also mean old tokens stay valid until they expire; a review may describe that as one problem or as several.

**Both**
- No database encryption, no backup encryption, no log rotation: true for a small local system and outside the answer key.
- A review that says a planted issue exists in more places than the manifest lists is not making a false claim if the extra places really share the pattern.
