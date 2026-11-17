# Other databases — PostgreSQL, SQLite, SQL Server, Oracle, MongoDB, Redis

For MySQL and MariaDB read `mysql.md`. Everything below follows each vendor's own documentation. Version policy: follow `versoes-e-fontes.md`. Find out which engine and version the project or hosting runs, look up its current support status at the vendor's site, and write for that version. A setting described as a default "since version N" is a hint to check the documentation of the version in use, not a fact to assume. Then run the vulnerability check in `security-baseline.md`.

## Rules for every engine
* Parameters or bind variables only. Zero string interpolation into a query, in any language. Dynamic identifiers (table, column, sort direction) come from an allowlist in code.
* Dedicated application account with the least privilege: only the verbs the app uses, on the schemas it uses. The application never connects as the administrator.
* Credentials from environment variables or a secret store, never in the code or the repository.
* TLS on every connection that crosses a network, with certificate verification on.
* Backup that is automated, stored where the server cannot overwrite it, and restored at least once a quarter into a throwaway instance. A backup nobody restored is not a backup.
* Explicit transactions for multi-statement writes, with rollback on error. Know the isolation level in use and retry on serialization failures.
* Migrations are versioned files in the repository, reversible, and tested first on a copy of the data. Backup before any destructive change (see the destructive-actions rule in `SKILL.md`).
* Diagnose with the engine's plan tool before adding indexes. Slow query logging on before tuning.
* Personal data (LGPD) isolated and encrypted at rest where the engine supports it; a deletion path designed before launch.

## PostgreSQL
* Placeholders `$1, $2` through the driver (`psycopg`, `pg`, `pgx`, PDO `pgsql`). Never `format()` or concatenation into SQL.
* Authentication in `pg_hba.conf` with `scram-sha-256`, never `trust`. Connection string `sslmode=verify-full`.
* Roles instead of per-user grants. On the `public` schema, revoke `CREATE` from `PUBLIC` (default since PostgreSQL 15, check older servers). Row Level Security (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` plus policies) for multi-tenant data.
* Types: `text` over `varchar(n)`, `timestamptz` over `timestamp`, `numeric(12,2)` for money (never `float`), `jsonb` over `json`, `bigint generated always as identity` for keys.
* Tuning: `EXPLAIN (ANALYZE, BUFFERS)`, the `pg_stat_statements` extension, autovacuum left on. Default isolation is `READ COMMITTED`; with `SERIALIZABLE` the app must retry on SQLSTATE `40001`.
* Backup: `pg_dump -Fc` and `pg_restore` for logical copies; continuous WAL archiving for point-in-time recovery on important data.

## SQLite
* Bound parameters (`?` or named) through the driver.
* Per connection: `PRAGMA foreign_keys = ON` (it is off by default), `PRAGMA journal_mode = WAL`, and a `busy_timeout` so concurrent writers wait instead of failing.
* The database file lives outside the public folder with permissions limited to the app user. SQLite has no built-in encryption; use SQLCipher when the file holds sensitive data.
* One writer at a time: not for heavy concurrent writes or for several servers sharing one file.
* Backup with the `.backup` command or `VACUUM INTO`, never by copying the file while it is being written.

## SQL Server
* `SqlParameter` or `sp_executesql` with parameters. Connection string `Encrypt=True;TrustServerCertificate=False`.
* Disable or lock down `sa`. Application login mapped to a database user in a role with only the required permissions; no `db_owner`, no `sysadmin`.
* Encryption at rest: TDE for the files; Always Encrypted or column-level encryption for the most sensitive columns. SQL Server Audit for who read or changed what.
* Tuning: Query Store and the actual execution plan before changing indexes. `READ_COMMITTED_SNAPSHOT` reduces blocking. `SET XACT_ABORT ON` in procedures that use transactions.
* Backup: `BACKUP DATABASE ... WITH CHECKSUM`, then `RESTORE VERIFYONLY`, plus a real restore test.

## Oracle Database
* Bind variables always (they also keep the shared cursor cache healthy). For an identifier that cannot be bound, validate with `DBMS_ASSERT`.
* Least privilege: never grant `DBA` or `ANY` privileges to the application schema; change the default passwords of the sample accounts.
* Network: native network encryption or TCPS. At rest: Transparent Data Encryption. Auditing: Unified Auditing.
* Tuning: `EXPLAIN PLAN` with `DBMS_XPLAN.DISPLAY`, AWR where licensed. Backup with RMAN and test the restore.

## MongoDB
* NoSQL injection is real: never pass a request body or query string straight into a filter, because `{"$ne": null}` or `$where` changes the query. Validate input against a schema, accept only the expected scalar types, reject keys starting with `$`.
* Authentication enabled (`security.authorization: enabled`), roles with least privilege, never exposed to the internet (bind to a private address and firewall the port). TLS on. Server-side JavaScript off (`security.javascriptEnabled: false`) unless needed.
* Schema validation with `$jsonSchema` on important collections. Indexes for every frequent filter and sort; check with `explain("executionStats")`.
* Backup with `mongodump` or the platform's snapshots, and restore-test.

## Redis
* Never exposed to the internet. Keep `protected-mode yes`, bind to a private interface, firewall the port, TLS where it crosses a network.
* Authentication with ACL users (Redis 6+), not a single shared password; restrict dangerous commands per user (`-@dangerous`, `-flushall`, `-config`).
* Treat it as a cache or a queue, not as the only copy of important data. Every key a cache holds gets a TTL; set `maxmemory` and an eviction policy.
* Never `KEYS *` in production; iterate with `SCAN`. Persistence (RDB or AOF) chosen on purpose, not left at the default.
