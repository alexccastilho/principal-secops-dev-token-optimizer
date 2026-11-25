# Delivery standard: what "done" means, per kind of artefact

Read this when the task creates or changes a project, a database schema, an API or a deploy. It is a workflow file: it does not count against the reference budget in `SKILL.md`, section 6.

Proportionality first. Apply what the request creates or changes. In existing code, never impose this list on the code around the change (`SKILL.md`, section 4, rule 2). For a small personal app, the minimum below is enough.

## Contents

- Minimum for any delivery
- Code
- Database and schema
- API
- Tests
- Operation

## Minimum for any delivery

- It builds and the happy path runs (`SKILL.md`, section 7). A file the instructions mention exists.
- The language manifest is present and lists every package the code imports: `package.json`, `composer.json`, `requirements.txt` or `pyproject.toml`, `go.mod`, `.csproj`, `pom.xml`.
- `LEIA-ME.md` with how to run, how to stop, where the data lives and how to back it up, in pt-BR for the user.
- For a non-programmer: every prerequisite named with its official download link, and one double-click launcher (`iniciar.bat` on Windows) that installs what is missing, builds if needed and starts the app. Never an instruction that requires typing in a terminal.
- `.gitignore` that keeps out secrets (`.env`), the local database file, logs and build output.
- Configuration and secrets come from environment variables; `.env.example` lists them with fake values.

## Code

- The language's official formatter and linter style (the stack reference names them; the version comes from `scripts/fontes.py versao`). Types where the language has them.
- Names from the business domain (`calcularDesconto`, not `processa2`).
- Errors handled at the boundary: generic message to the user, detail to the log, deny on failure. No empty `catch`.
- No dead code, no commented-out blocks, no debug prints left behind.

## Database and schema

- Schema changes as numbered migrations (`001_criar_contatos.sql`, framework migrations, Flyway, Alembic), each with its reverse when the tool supports it. Never a loose `CREATE` run by hand in production.
- Every table has a primary key. Declare the rules in the schema, not only in code: `NOT NULL`, `UNIQUE`, `FOREIGN KEY` with an explicit `ON DELETE`, `CHECK` for ranges and closed lists.
- An index for every column used in a `WHERE`, `JOIN` or `ORDER BY` the code actually runs. No index nobody uses.
- Types that fit: money as `DECIMAL(12,2)` or integer cents, never floating point; dates as date or timestamp types with the time zone decided; CPF, CNPJ, CEP and phone numbers as text, never numbers.
- SQLite: turn on foreign keys per connection when the driver does not (`PRAGMA foreign_keys = ON`) and check which one applies to the driver in use.
- The application connects with a user that has only the rights it needs, never the administrator.
- Seed data separate from the schema, and never real personal data in a seed.
- One line in `LEIA-ME.md` on how to back up and restore the database.

## API

- A written contract: routes, inputs, outputs and error codes (OpenAPI when the stack makes it cheap, otherwise a table in the README).
- Input validated at the edge with an explicit schema; unknown fields rejected.
- Lists paginated with a maximum page size; a limit on request size and rate on public routes.
- Errors with one stable shape (`{"erro": "...", "codigo": "..."}`), never a stack trace.
- A version in the path or a header once anyone outside the project consumes it.

## Tests

- Tests that catch a real regression, with literal expected values, including the denied-access case for every protected route (`references/estrutura.md` has the rules).
- Only when the request or the risk calls for them in a small app (personal data in production, money); otherwise offer them in one line.

## Operation

- How to run, update and roll back, in `LEIA-ME.md`.
- Logs record identifiers, not names, e-mails or documents.
- Dependencies pinned with a lockfile, and `scripts/fontes.py deps <pasta>` run on it before delivery when dependencies were added or changed.
