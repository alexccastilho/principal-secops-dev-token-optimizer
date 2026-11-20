# Relational databases: PostgreSQL, SQLite, SQL Server, Oracle, Firebird and others

Version policy: follow `versoes-e-fontes.md`. Read the engine and version from the project (connection string, driver package, `docker-compose.yml`, the hosting panel) or from the server (`SELECT version();`, `SELECT @@VERSION;`, `sqlite_version()`, `rdb$get_context('SYSTEM','ENGINE_VERSION')`), then check endoflife.date (`postgresql`, `sqlite`, `mssqlserver`, `oracle-database`, `ibm-db2`, `duckdb`, `cockroachdb`) or the vendor page; Firebird: firebirdsql.org/en/downloads. A setting described here as a default "since version N" is a hint to check the docs of the version in use. MySQL and MariaDB: `mysql.md`. MongoDB, Redis, Firebase and other non-relational stores: `bancos-nosql.md`.

## Contents
- Rules for every engine
- PostgreSQL
- Supabase
- SQLite
- SQL Server
- Oracle Database
- Firebird
- IBM Db2
- DuckDB
- CockroachDB
- Microsoft Access
- DBF and Paradox files

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
* CPF, CNPJ, CEP and phone are text columns, never numeric: leading zeros are lost, and CNPJ became alphanumeric in 2026.
* The database port is never reachable from the internet. Admin access through a VPN, an SSH tunnel or the provider's console.

## PostgreSQL
* Placeholders `$1, $2` through the driver (`psycopg`, `pg`, `pgx`, PDO `pgsql`, JDBC). Never `format()` or concatenation into SQL. Dynamic identifiers in PL/pgSQL: `format('%I', name)` or `quote_ident`, plus an allowlist; in psycopg, `sql.Identifier`.
* Auth in `pg_hba.conf`: `scram-sha-256`, never `trust` on a network line. `md5` is deprecated (18+, warning on every md5 login in 19+): rehash by setting `password_encryption = 'scram-sha-256'` and resetting each password, then switch the `pg_hba.conf` lines. RADIUS was removed in 19.
* Client: `sslmode=verify-full` with the CA file. `require` encrypts but does not check who answers.
* Schemas: databases created on 15+ do not let `PUBLIC` create objects in `public`; a database upgraded from 14 or older keeps that grant, so run `REVOKE CREATE ON SCHEMA public FROM PUBLIC;`. Any schema in `search_path` that other users can write to lets them hijack your queries; `SECURITY DEFINER` functions get `SET search_path = <trusted_schema>, pg_temp` (`pg_temp` last).
* Roles instead of per-user grants. Row Level Security (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` plus policies) for multi-tenant data; the table owner bypasses RLS unless `FORCE ROW LEVEL SECURITY`.
* Types: `text` over `varchar(n)`, `timestamptz` over `timestamp`, `numeric(12,2)` for money (never `float`), `jsonb` over `json`, `bigint generated always as identity` for keys. `uuidv7()` exists from 18 for time-ordered UUIDs.
* Tuning: `EXPLAIN (ANALYZE, BUFFERS)`, the `pg_stat_statements` extension, autovacuum left on. Default isolation `READ COMMITTED`; with `SERIALIZABLE` the app retries on SQLSTATE `40001`. Connection pooler (PgBouncer or the provider's) when many app processes connect.
* Backup: `pg_dump -Fc` and `pg_restore` for logical copies; continuous WAL archiving for point-in-time recovery on important data.
* Traps: dumps taken with `standard_conforming_strings = off` do not load into 19+; re-dump with a current `pg_dump`. Upgrading a major version needs `pg_upgrade` or dump and restore, never just new binaries on the old data folder.
* TimescaleDB and pgvector are PostgreSQL extensions: same rules here; vector specifics in `bancos-nosql.md`.

## Supabase (and other PostgreSQL reached from the browser)
* Row Level Security on every table in an exposed schema, with a policy per operation, is the only access control there is. New tables in `public` get privileges for `anon` and `authenticated`; without RLS they are public.
* Views bypass RLS by default (they run as their creator). Create them `with (security_invoker = true)` (Postgres 15+) or keep them out of exposed schemas.
* A `security definer` function in an exposed schema runs with its creator's rights for anyone who can call it: keep such functions in a private schema or check `auth.uid()` inside.
* Keys: the publishable key (`sb_publishable_...`, replaces `anon`) may live in the front end; the secret key (`sb_secret_...`, replaces `service_role`) bypasses RLS and lives only on the server, never in a browser, an app bundle or the repository. The legacy `anon` and `service_role` keys are deprecated: move to the new keys.
* Test every policy logged in as two different users and logged out before publishing.

## SQLite
* Bound parameters (`?` or named) through the driver.
* Per connection: `PRAGMA foreign_keys = ON` (off by default), `PRAGMA journal_mode = WAL`, and a `busy_timeout` so concurrent writers wait instead of failing.
* `STRICT` tables (3.37+) reject values of the wrong type; plain tables accept anything in any column.
* SQL typed by users: the `SQLITE_DBCONFIG_DEFENSIVE` flag and lower limits, so a statement cannot corrupt the file or exhaust memory.
* A database file someone else supplied (upload, import): `PRAGMA trusted_schema = OFF` right after opening, then `PRAGMA quick_check` and reject the file on any error. Treat it as hostile input (`native-app-security.md`).
* The file lives outside the public folder with permissions limited to the app user. No built-in encryption; SQLCipher when it holds sensitive data.
* One writer at a time: not for heavy concurrent writes or for several servers sharing one file over a network share.
* Backup with `.backup` or `VACUUM INTO`, never by copying the file while it is being written.

## SQL Server
* `SqlParameter` or `sp_executesql` with parameters. Never `EXEC('...' + @input)`. Identifiers in dynamic SQL: `QUOTENAME` plus an allowlist.
* Driver: `Microsoft.Data.SqlClient`. `System.Data.SqlClient` is deprecated; moving changes the encryption default (Encrypt on since 4.0), so connections to a server without a valid certificate start failing. Fix the certificate.
* Connection string: `Encrypt=Mandatory` (or `true`) with `TrustServerCertificate=False`; `Encrypt=Strict` (TDS 8.0, SQL Server 2022+) where the server supports it. `TrustServerCertificate=True` turns off server identity checks and is never the production fix.
* Disable or lock down `sa`. Application login mapped to a database user in a role with only the required permissions; no `db_owner`, no `sysadmin`. Windows authentication or Entra ID where available instead of SQL logins.
* `xp_cmdshell` stays disabled. No linked servers to untrusted hosts.
* Encryption at rest: Transparent Data Encryption for the files; Always Encrypted for the most sensitive columns (keys stay with the client). A server audit for who read or changed what.
* Tuning: the actual execution plan before changing indexes. `READ_COMMITTED_SNAPSHOT` reduces reader and writer blocking.
* Backup: `BACKUP DATABASE`, then `RESTORE VERIFYONLY`, plus a real restore test.

## Oracle Database
* Bind variables always (they also keep the shared cursor cache healthy). An identifier that cannot be bound is validated with `DBMS_ASSERT`.
* Least privilege: never grant `DBA` or `ANY` privileges to the application schema; lock or change the passwords of sample and default accounts. Application connects as a user that does not own the schema, through grants or a proxy user.
* PL/SQL: `EXECUTE IMMEDIATE` with `USING` binds, never a concatenated string.
* Network: native network encryption or TCPS. At rest: Transparent Data Encryption. Auditing: Unified Auditing.
* Release labels: 19c and 23 (marketed as 26ai) are the long-term lines; 21c was an innovation release. Check the support date at oracle.com/support/lifetime-support before a project depends on a version.
* Tuning: `EXPLAIN PLAN FOR ...` then `DBMS_XPLAN.DISPLAY`. Backups proven by a real restore.

## Firebird (common in Brazilian Delphi systems)
* Parameters with `?` or `:name` in FireDAC, IBX, Jaybird or the Python drivers, never concatenated SQL. Delphi: `Query.ParamByName('id').AsInteger := ...`, never `'... WHERE id = ' + Edit1.Text`.
* Auth: SRP is the default from 3.0 (current `firebird.conf`: `AuthServer = Srp256`). `Legacy_Auth` sends almost plain passwords and forces weaker wire encryption: keep it off, and update the old client library shipped with the program instead of turning it on.
* Wire encryption: keep `WireCrypt = Required` on the server (default). Lowering it to make an old client connect is a finding.
* Change any default or well-known `SYSDBA` password at install; the application uses its own user with grants, never `SYSDBA`. Roles for groups of permissions.
* `firebird.conf`: `DatabaseAccess` defaults to `Full`; set `Restrict` to the data folder or use aliases in `databases.conf`. `ExternalFileAccess` and `UdfAccess` stay `None`; their folders never overlap each other or the database folder. UDFs are deprecated (since the 3.0 notes; `UdfAccess` since 4.0): replace with built-in or PSQL functions.
* The Firebird port never open to the internet; `RemoteBindAddress` to the internal interface when the server has a public one. Remote branches connect through a VPN, not port forwarding.
* The `.fdb` file is the whole database: outside shared folders, readable only by the Firebird service account. Never copy it while the server runs; backup with `gbak -b` and restore-test with `gbak -c` into a new file.
* Traps: Dialect 1 databases (old InterBase legacy) treat `DATE` as date plus time and double quotes as strings; Dialect 3 is the default and uses double quotes for identifiers. Do not change dialect in place. Character set `NONE` mixes encodings and garbles accents: new databases use `UTF8`, conversion is a planned migration. Generators (sequences) out of sync after a restore of partial data cause duplicate keys.
* Safe maintenance: upgrading 2.5 to 3.0 or later changes the on-disk format and auth. Do it as backup with the old `gbak`, restore with the new one on a test machine, run the app against it, then switch. Never upgrade the server and the Delphi client library separately on a live system.

## IBM Db2
* Parameter markers (`?`) through the driver (JDBC, CLI/ODBC, language drivers). Static SQL in packages where the app already uses it.
* Least privilege with roles; no `DBADM` or `SECADM` for the application user. Row and column access control (RCAC) for multi-tenant or sensitive columns.
* TLS on the client connection; encryption at rest where the edition supports it; the audit facility (`db2audit`, `AUDIT` statement) for audit trails.
* Lifecycle: 11.1 and older are out of support; check 11.5 and 12.1 dates at endoflife.date before planning.
* Tuning: read the access plan with the Explain facility, refresh statistics after big loads. Backup and test the restore.

## DuckDB
* Embedded analytics engine: parameters with `?` or `$name` through the API, never formatted SQL.
* SQL from users or from an AI agent can read and write files and URLs by default. Lock it down: `SET enable_external_access = false;` (with `allowed_directories` or `allowed_paths` first, if some folder must stay reachable), then `SET lock_configuration = true;` so the query cannot undo it. Order matters.
* Extensions run with the process's privileges: set `autoinstall_known_extensions` and `autoload_known_extensions` to `false` and `allow_community_extensions = false` unless needed.
* DuckDB's own guidance: treat SQL like Bash or Python code. These settings do not replace a sandbox (container, VM) when the SQL comes from users or an AI agent.
* Not a multi-writer server: one process writes a database file at a time.

## CockroachDB
* PostgreSQL wire protocol: same driver rules as PostgreSQL (`$1` placeholders, `sslmode=verify-full`).
* Never run a cluster in insecure mode outside a laptop: it has no authentication, encryption or authorization. Certificates for nodes and clients, CA key kept off the cluster.
* Transactions are `SERIALIZABLE` by default: the app retries on SQLSTATE `40001`.
* Licensing changed in 2024 (Core retired, free tier with mandatory telemetry): check the current license terms before choosing it for a client.

## Microsoft Access (.mdb, .accdb)
* A file database, not a server: no real user accounts, no audit, no safe concurrent use over a network share. Fine for one person; a business system with several users or web access needs a server database.
* From code (VBA, Delphi, .NET, Python via ODBC/OLE DB): parameterized queries (`?` in OLE DB/ODBC, `PARAMETERS` or `QueryDef` parameters in VBA). Never build SQL from a form field.
* The database password is not access control: anyone with the file and the password reads everything. Keep the file in a folder only the right people can open, and never on a public web server.
* Driver: the Access Database Engine 2016 Redistributable is out of support since 2025-10-14; Microsoft points to the Microsoft 365 Access Runtime. Match bitness (32 or 64) to the calling program, not to Windows.
* Backup: close every connection, then copy the file; compact it regularly. Keep several dated copies.
* Safe maintenance and migration: split front end (forms) and back end (tables) first. Then move the tables to SQL Server Express or PostgreSQL and link them from the same Access front end, so users keep working; replace the front end later, screen by screen. Never a big-bang rewrite of a system people use daily.

## DBF (dBase, Clipper, FoxPro) and Paradox files
* No access control, no transactions, weak locking: corruption on network shares is common. Treat the files as data to protect and migrate, not as a platform to build on.
* BDE (Borland Database Engine) is deprecated and no longer installed with current RAD Studio. FireDAC does not support Paradox or dBase natively (only through ODBC).
* Reading them from new code: a maintained library or ODBC driver, read-only where possible; validate field lengths and the code page (old DOS and Windows code pages, not UTF-8), or accents break.
* Safe maintenance: backup the whole folder (tables plus their index and memo files) with every program closed. Rebuild indexes after a crash before anyone writes again.
* Staged migration: 1) copy the data into a server database with a script and compare row counts and totals; 2) make the old program read from or sync with the new database where it can, or run both in parallel for a period; 3) move one module at a time (registrations, then sales, then finance); 4) retire the old files only after a full month closes with matching numbers. Never switch everything over a weekend.
