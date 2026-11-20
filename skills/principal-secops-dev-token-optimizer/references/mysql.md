# MySQL and MariaDB

Version policy: follow `versoes-e-fontes.md`. Read the server and version with `SELECT VERSION();` or from the hosting panel (the string says "MariaDB" when it is MariaDB), then check endoflife.date (`mysql`, `mariadb`), dev.mysql.com/doc/refman/en/mysql-releases.html and mariadb.org/about/#maintenance-policy. Prefer an LTS line; an end-of-life server is a finding. Write SQL for the server that is actually there.

## Release model
* MySQL has two tracks. LTS: fixes only, no removals inside the line. Innovation: new features and removals, supported only until the next Innovation release. Production on a server you manage: LTS.
* Numbering: sequential up to 9.7; after that calendar versions `YY.M` (26.7 = July 2026). An LTS keeps its `YY.M` for its whole life.
* Upgrades go LTS to next LTS; skipping an LTS is not supported. Downgrading an Innovation release needs a dump and reload.
* MySQL 8.0 reached end of life on 2026-04-30 and 5.7 earlier: report it, plan the move to an LTS.
* MariaDB: one LTS per year, rolling releases every quarter. Rolling lines go out of support fast; on a server you manage use an LTS.
* MariaDB is not "MySQL with another name". Auth plugins, collations, JSON and some functions differ. Check before using anything specific to one of them.

## Access layer (any language)
* Prepared statements ALWAYS: PDO in PHP, `mysql2` prepared statements in Node, `PreparedStatement` in Java, parameterized cursor in Python. Zero interpolation.
* PDO: `ERRMODE_EXCEPTION`, `ATTR_EMULATE_PREPARES => false`, `charset=utf8mb4` in the DSN.
* Dynamic identifiers (table, column, `ORDER BY` direction) cannot be parameterized. Map them from an allowlist in code.
* Explicit transactions for any multi-statement write, with rollback in the catch block.
* Credentials from environment variables. Dedicated user, least privilege: no root, no `GRANT ALL`, no `FILE`, no `SUPER`. Grant only the verbs the app uses on the schemas it uses. Wildcards (`%`, `_`) in database grants are deprecated (8.2+): name the schema.
* Connection pooling on the app side. Never open a connection per query.

## Authentication
* `caching_sha2_password` is the default plugin from MySQL 8.0. The first login after a password change needs TLS, a local socket or RSA key exchange, otherwise it fails with "Authentication requires secure connection". Old drivers that do not support the plugin fail too. Fix by updating the driver or enabling TLS, not by downgrading the account.
* `mysql_native_password`: deprecated since 8.0.34, disabled by default in 8.4 (re-enable only as a stopgap with `mysql_native_password=ON`), removed in 9.0. Accounts still on it stop working after an upgrade past 8.4: migrate them with `ALTER USER ... IDENTIFIED WITH caching_sha2_password BY ...` before upgrading.
* `default_authentication_plugin` was removed in 8.4; use `authentication_policy`, and remove the old option from `my.cnf` before upgrading.
* MariaDB: root on a fresh install usually logs in through `unix_socket` (operating-system user, no password), so `mysql -u root -p` with a password fails. Do not "fix" it by giving root a password and opening it to the network; create an application user instead. For password accounts prefer PARSEC (11.6+) or `ed25519`; never `mysql_old_password`.

## Schema design
* Engine InnoDB. Charset `utf8mb4`. Never `utf8`, a deprecated alias of `utf8mb3`, which cannot store emoji and is due for removal.
* Collation: on MySQL `utf8mb4_0900_ai_ci` exists from 8.0. MariaDB does not have it (a `CREATE TABLE` with that name fails there); newer MariaDB uses `utf8mb4_uca1400_ai_ci`, older ones `utf8mb4_unicode_ci` or `utf8mb4_general_ci`. Read what the server uses (`SHOW VARIABLES LIKE 'collation%';`) and keep one collation per database: mixing them gives "Illegal mix of collations" on joins.
* Every table: `id` primary key (`BIGINT UNSIGNED AUTO_INCREMENT`, or UUID stored as `BINARY(16)` when distributed), plus `created_at` and `updated_at`. `TIMESTAMP` ends in January 2038: any date that can fall later (due date, contract end, birth date) is `DATE` or `DATETIME`.
* Right-size types: `TINYINT(1)` for flags, `DECIMAL(10,2)` for money and never `FLOAT`, `VARCHAR` sized to reality, CPF, CNPJ, CEP and phone as `CHAR` or `VARCHAR` and never a number (leading zeros are lost, and CNPJ became alphanumeric in 2026), lookup table instead of `ENUM` for values that change.
* Foreign keys with explicit `ON DELETE` and `ON UPDATE`, pointing at a primary key or a unique key (MySQL 8.4 rejects non-unique or partial keys by default).
* Personal data (CPF, e-mail, phone, address) isolated in its own table, so a deletion request under LGPD is one operation instead of a hunt.
* Migrations as versioned `.sql` files in the repo. No ad-hoc `ALTER` without a record.

## Query rules
* Never `SELECT *`. List the columns.
* Never a query inside a loop. Use `JOIN` or `WHERE id IN (...)`.
* `LIMIT` on every list query. Keyset pagination (`WHERE id > ?`) instead of `OFFSET` on large tables.
* `EXISTS` instead of `COUNT(*) > 0`. `UNION ALL` instead of `UNION` when duplicates are impossible.
* Every query on a multi-tenant table carries the owner or tenant filter. A missing filter is a data leak, not a bug.

## Indexing and tuning
* Index every foreign key and every column used in frequent `WHERE`, `ORDER BY` and `JOIN`. Composite indexes leftmost-prefix first.
* `EXPLAIN` before changing anything. Look for `type=ALL` (full scan) and `Using filesort`.
* Covering indexes on hot read paths. Do not index a low-cardinality column on its own.
* No functions on indexed columns in `WHERE`. `WHERE DATE(created_at) = ?` kills the index; use a range.
* Turn on `slow_query_log` before tuning. Server-level tuning (`innodb_buffer_pool_size` and similar) only on a dedicated database server, never on shared hosting.

## Traps and fixes
* Login errors naming `caching_sha2_password` or `mysql_native_password` right after a server upgrade: old client library or an account still on the old plugin. Update the driver and migrate the account; re-enabling the old plugin is a stopgap that ends at 9.0.
* Scripts and runbooks with `CHANGE MASTER TO`, `START SLAVE`, `SHOW SLAVE STATUS`, `SHOW MASTER STATUS` break on 8.4: use `CHANGE REPLICATION SOURCE TO`, `START REPLICA`, `SHOW REPLICA STATUS`, `SHOW BINARY LOG STATUS`.
* `mysql_upgrade`, `mysqlpump` and `mysql_ssl_rsa_setup` no longer exist in 8.4. Backup scripts that call `mysqlpump` fail; switch to `mysqldump` or MySQL Shell dump utilities.
* `AUTO_INCREMENT` on a `FLOAT` or `DOUBLE` column blocks the upgrade to 8.4: change the column to an integer first.
* PDO TLS constants: `Pdo\Mysql::ATTR_SSL_CA` and `Pdo\Mysql::ATTR_SSL_VERIFY_SERVER_CERT` from PHP 8.4; the old `PDO::MYSQL_ATTR_SSL_*` names are deprecated from PHP 8.5. Use the name the project's minimum PHP supports, and pass them in the `new PDO(...)` options, not with `setAttribute`.
* Dump from MySQL loaded into MariaDB (or the reverse) fails on collations and auth plugins: replace collation names and recreate users with the target server's syntax, never import the `mysql` system schema.

## Safe changes and backup
* Before `ALTER TABLE` on production data, instruct a backup in pt-BR: mysqldump, or "Exportar" no phpMyAdmin.
* Additive changes preferred: add the column with a default, backfill, switch the code, drop the old one later.
* Never `DROP` or rename without confirming nothing references the object. If the codebase is not fully visible, ask.
* A long `ALTER` on a big table can lock it. Warn about downtime before, not after.
* Any project with real data gets a backup instruction in the handoff: what to export, how often, where the copy lives. A backup nobody restored is not a backup.
```bash
# Consistent logical backup of InnoDB tables with routines and triggers; credentials come from an option file, never the command line.
mysqldump --defaults-extra-file=/path/outside/webroot/backup.cnf --single-transaction --routines --triggers --no-tablespaces dbname | gzip > "dbname_$(date +%F).sql.gz"
```
* Keep copies where the web server cannot overwrite them, several generations, and every quarter restore one into a throwaway database and count the rows.
* Server upgrade: back up, read the release notes of every line in between, test the dump on the target version first, then upgrade LTS to LTS.

## Transport and operation
* TLS whenever app and database are on different machines: server `require_secure_transport=ON`, client with certificate verification (the CA file plus verify-server-cert in PDO). 8.4 rejects weak ciphers; `--ssl` was removed, use `--tls-version`.
* Isolation: InnoDB default is `REPEATABLE READ`. Use `SELECT ... FOR UPDATE` inside a transaction for read-then-write sequences (stock, balances) so two requests cannot both pass the check.
* Port 3306 never open to the internet. Remote admin through an SSH tunnel or the host's panel.
* Audit who changes what on sensitive tables (application audit log, or the audit plugin where the edition has one).
