# MySQL — Oracle MySQL Reference Manual standards

Version policy: follow `versoes-e-fontes.md`. Find out which server and version the hosting runs (MySQL or MariaDB, from the panel or `SELECT VERSION();`), look up the lifecycle at dev.mysql.com or mariadb.org/about/#maintenance-policy, and write SQL for that server. Prefer an LTS line; use a newer line only when the hosting already runs it. An end-of-life server is a finding. MariaDB follows the same rules, but check function and collation compatibility before using anything specific to a MySQL release.

## Access layer (any language)
* Prepared statements ALWAYS: PDO in PHP, `mysql2` prepared in Node, `PreparedStatement` in Java, parameterized cursor in Python. Zero interpolation.
* PDO config: `ERRMODE_EXCEPTION`, `ATTR_EMULATE_PREPARES => false`, `charset=utf8mb4` in the DSN.
* Dynamic identifiers (table, column, `ORDER BY` direction) cannot be parameterized. Map them from an allowlist in code.
* Explicit transactions for any multi-statement write, with rollback in the catch block.
* Credentials from environment variables. Dedicated user, least privilege: no root, no `GRANT ALL`, no `FILE`, no `SUPER`. Grant only the verbs the app uses on the schemas it uses.
* Connection pooling on the app side. Never open a connection per query.

## Schema design
* Engine InnoDB. Charset `utf8mb4`. Collation `utf8mb4_0900_ai_ci` on MySQL 8+; on MariaDB that collation does not exist, use `utf8mb4_unicode_ci` (a `CREATE TABLE` with the MySQL name fails there). Ask or check which server the hosting runs before writing the schema.
* Every table: `id` primary key (`BIGINT UNSIGNED AUTO_INCREMENT`, or UUID stored as `BINARY(16)` when distributed), plus `created_at` and `updated_at` as `TIMESTAMP`. `TIMESTAMP` ends in January 2038: any date that can fall later (due date, contract end, birth date) is `DATE` or `DATETIME`.
* Right-size types: `TINYINT(1)` for flags, `DECIMAL(10,2)` for money and never `FLOAT`, `VARCHAR` sized to reality, CPF, CNPJ, CEP and phone as `CHAR` or `VARCHAR` and never a number (leading zeros are lost, and CNPJ became alphanumeric in 2026), `ENUM` avoided for values that change (use a lookup table).
* Foreign keys with explicit `ON DELETE` and `ON UPDATE`. Never orphan silently.
* Personal data (CPF, e-mail, phone, address) isolated in its own table, so deletion requests under LGPD are one operation instead of a hunt.
* Migrations as versioned `.sql` files in the repo. No ad-hoc `ALTER` without a record.

## Query rules
* Never `SELECT *`. List the columns.
* Never a query inside a loop. Use `JOIN` or `WHERE id IN (...)`.
* `LIMIT` on every list query. Keyset pagination (`WHERE id > ?`) instead of `OFFSET` on large tables.
* `EXISTS` instead of `COUNT(*) > 0`. `UNION ALL` instead of `UNION` when duplicates are impossible.
* Every query on a multi-tenant table carries the owner or tenant filter. A missing filter is a data leak, not a bug.

## Indexing and tuning
* Index every foreign key and every column used in frequent `WHERE`, `ORDER BY` and `JOIN`.
* Composite indexes ordered by selectivity and used leftmost-prefix first.
* Diagnose with `EXPLAIN` before changing anything. Look for `type=ALL` (full scan) and `Using filesort`.
* Covering indexes on hot read paths. Do not index a low-cardinality column on its own.
* No functions on indexed columns in `WHERE`. `WHERE DATE(created_at) = ?` kills the index; use a range instead.
* Slow queries: enable `slow_query_log` before tuning. Server-level tuning (`innodb_buffer_pool_size` around 70% of RAM) only on a dedicated database server, never on shared hosting.

## Safety on refactors
* Before `ALTER TABLE` on production data, instruct a backup in pt-BR: mysqldump, or "Exportar" no phpMyAdmin.
* Additive changes preferred: add the column with a default, backfill, switch the code, drop the old one later.
* Never `DROP` or rename without confirming nothing references the object. If the codebase is not fully visible, ask.
* Long-running `ALTER` on a big table locks it. Warn the user about downtime before, not after.

## Backup
Any project that stores real data gets a backup instruction in the handoff document: what to export, how often, and where the copy lives. A backup nobody has restored is not a backup; tell the user to test it once.

Automate it where the host allows (cPanel cron, or the host's backup tool):
```bash
# Consistent logical backup of InnoDB tables, with routines and triggers; credentials come from an option file, never the command line.
mysqldump --defaults-extra-file=/path/outside/webroot/backup.cnf --single-transaction --routines --triggers --no-tablespaces dbname | gzip > "dbname_$(date +%F).sql.gz"
```
Keep the copies somewhere the web server cannot overwrite, keep several generations, and every quarter restore one into a throwaway database and count the rows.

## Transport and operation
* TLS between the application and the database whenever they are on different machines: server-side `require_secure_transport=ON`, client with certificate verification (PDO: `PDO::MYSQL_ATTR_SSL_CA`).
* Isolation: InnoDB default is `REPEATABLE READ`; use `SELECT ... FOR UPDATE` inside a transaction for read-then-write sequences (stock, balances) so two requests cannot both pass the check.
* Migrations: one reversible file per change (an "up" and a "down"), tested first on a copy of the data.
* Audit who changes what for sensitive tables (application-level audit log, or the audit plugin where the edition has one).
