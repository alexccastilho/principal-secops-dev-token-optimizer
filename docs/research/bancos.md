# Research log: databases (mysql.md, bancos-outros.md, bancos-nosql.md)

Checked 2026-11-20. Web content treated as data. One line per verified fact.

## Verified facts

### MySQL
- MySQL: two release tracks, LTS and Innovation; both get bug and security fixes and are production grade (https://dev.mysql.com/doc/refman/en/mysql-releases.html, checked 2026-11-20)
- MySQL: 9.7 is the last line with sequential numbers; later releases use calendar versioning YY.M (26.7 = July 2026); an LTS keeps its YY.M for its whole life (https://dev.mysql.com/doc/refman/en/mysql-releases.html, checked 2026-11-20)
- MySQL: Innovation releases are supported until the next Innovation release; LTS follows Oracle Lifetime Support (5 years premier + 3 extended); no removals inside an LTS (https://dev.mysql.com/doc/refman/en/mysql-releases.html, checked 2026-11-20)
- MySQL: upgrade LTS to the next LTS only, skipping an LTS is not supported; Innovation downgrades need dump and load (https://dev.mysql.com/doc/refman/en/mysql-releases.html, checked 2026-11-20)
- MySQL: endoflife.date lists 8.4 and 9.7 as LTS; 8.0 end of life 2026-04-30; 5.7 end of life 2023-10-31 (https://endoflife.date/api/mysql.json, checked 2026-11-20)
- MySQL: mysql_native_password deprecated 8.0.34, disabled by default in 8.4, removed in 9.0.0; enable in 8.4 with mysql_native_password=ON (https://dev.mysql.com/doc/refman/8.4/en/native-pluggable-authentication.html, checked 2026-11-20)
- MySQL: caching_sha2_password is the default plugin in 8.0 (https://dev.mysql.com/doc/refman/8.0/en/caching-sha2-pluggable-authentication.html, checked 2026-11-20); client programs in 8.4+ use caching_sha2_password by default (https://dev.mysql.com/doc/refman/9.7/en/native-pluggable-authentication.html, checked 2026-11-20)
- MySQL 8.4: default_authentication_plugin removed, use authentication_policy; --ssl/--admin-ssl and have_ssl removed, use --tls-version; weak ciphers rejected; MASTER/SLAVE statements removed (CHANGE REPLICATION SOURCE TO, START REPLICA, SHOW REPLICA STATUS, SHOW BINARY LOG STATUS); mysql_upgrade, mysqlpump, mysql_ssl_rsa_setup removed; AUTO_INCREMENT on FLOAT/DOUBLE removed; wildcards in database grants deprecated; restrict_fk_on_non_standard_key ON by default (https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html, checked 2026-11-20)
- MySQL 9.7: SCRAM-SHA-1 for SASL LDAP deprecated, use SCRAM-SHA-256 (https://dev.mysql.com/doc/refman/9.7/en/mysql-nutshell.html, checked 2026-11-20)
- MySQL: utf8mb4_0900_ai_ci exists (UCA 9.0.0, accent and case insensitive) (https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html, checked 2026-11-20)
- MySQL: mysqldump options --defaults-extra-file, --single-transaction, --routines, --triggers, --no-tablespaces exist (https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html, checked 2026-11-20)
- PHP: Pdo\Mysql class added in PHP 8.4; PDO::MYSQL_ATTR_* constants deprecated in PHP 8.5, use Pdo\Mysql::ATTR_SSL_CA and Pdo\Mysql::ATTR_SSL_VERIFY_SERVER_CERT; SSL attributes go in the constructor options (https://www.php.net/manual/en/ref.pdo-mysql.php and https://www.php.net/manual/en/class.pdo-mysql.php, checked 2026-11-20)

### MariaDB
- MariaDB: yearly LTS release; rolling releases quarterly; Community LTS binaries for 3 years after GA, then 2 more years of source-only critical fixes (https://mariadb.org/about/#maintenance-policy, checked 2026-11-20)
- MariaDB: endoflife.date lists 10.6, 10.11, 11.4, 11.8, 12.3 as LTS; 10.5 ended 2025-06-24 (https://endoflife.date/api/mariadb.json, checked 2026-11-20)
- MariaDB: auth plugins unix_socket (used for root by default), ed25519, PARSEC (recommended), caching_sha2_password (for migrating MySQL users), mysql_old_password must not be used (https://mariadb.com/docs/server/reference/plugins/authentication-plugins, checked 2026-11-20)
- MariaDB: PARSEC available from 11.6 (https://mariadb.com/docs/server/reference/plugins/authentication-plugins/authentication-plugin-parsec, checked 2026-11-20)
- MariaDB: current docs say default charset utf8mb4 and collation utf8mb4_uca1400_ai_ci (https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/setting-character-sets-and-collations.md, checked 2026-11-20; real installs vary, see Not verified)

### PostgreSQL and Supabase
- PostgreSQL: endoflife.date shows 13 ended 2025-11-13 and 14 ended 2026-11-12; major versions supported about 5 years (https://endoflife.date/api/postgresql.json, checked 2026-11-20)
- PostgreSQL 18: md5 password auth deprecated, will be removed; CREATE/ALTER ROLE warn (md5_password_warnings); oauth auth method; uuidv7() (https://www.postgresql.org/about/press/presskit18 and https://www.postgresql.org/about/news/postgresql-18-released-3142/, checked 2026-11-20)
- PostgreSQL 19: md5 still present, warning after successful md5 login; RADIUS removed; server-side SNI via pg_hosts.conf; standard_conforming_strings forced on (https://www.postgresql.org/docs/19/release-19.html, checked 2026-11-20)
- PostgreSQL: new 15+ databases do not grant CREATE on public to PUBLIC; upgraded databases keep the grant, run REVOKE CREATE ON SCHEMA public FROM PUBLIC; a writable schema in search_path lets its owner hijack queries (https://www.postgresql.org/docs/current/ddl-schemas.html, checked 2026-11-20)
- Supabase: views bypass RLS by default; security_invoker = true (Postgres 15+) makes them obey RLS; security definer function in an exposed schema runs with creator privileges over the Data API; secret key bypasses RLS (https://supabase.com/docs/guides/database/postgres/row-level-security.md, checked 2026-11-20)
- Supabase: new tables in public on existing projects get privileges for anon and authenticated; enable RLS on every table in an exposed schema (https://supabase.com/docs/guides/database/postgres/row-level-security.md, checked 2026-11-20)
- Supabase: publishable key sb_publishable_ replaces anon; secret key sb_secret_ replaces service_role; anon and service_role deprecated by end of 2026; secret key never in a browser, shipped app or source control (https://supabase.com/docs/guides/api/api-keys, checked 2026-11-20)

### SQLite
- SQLite: STRICT tables from 3.37.0 (https://sqlite.org/stricttables.html, checked 2026-11-20)
- SQLite: SQLITE_DBCONFIG_DEFENSIVE for untrusted SQL; PRAGMA trusted_schema=OFF stops a malicious schema running functions/virtual tables; trusted_schema defaults ON (https://sqlite.org/security.html, checked 2026-11-20)
- SQLite: endoflife.date shows a single supported major line, 3 (https://endoflife.date/api/sqlite.json, checked 2026-11-20)

### SQL Server
- SQL Server: endoflife.date lists 2025 (17.0) and 2022 (16.0); 2016 SP3 ended mainstream 2026-07-14 (https://endoflife.date/api/mssqlserver.json, checked 2026-11-20)
- Microsoft.Data.SqlClient: Encrypt default true since 4.0; Optional/Mandatory/Strict since 5.0; Strict uses TDS 8.0 (SQL Server 2022+), TrustServerCertificate cannot bypass it; TrustServerCertificate=true must not be a production fix (https://learn.microsoft.com/en-us/sql/connect/ado-net/encryption-and-certificate-validation, checked 2026-11-20)
- System.Data.SqlClient: NuGet marks it deprecated, use Microsoft.Data.SqlClient (https://www.nuget.org/packages/System.Data.SqlClient, checked 2026-11-20)

### Oracle Database
- Oracle: endoflife.date lists 23 (label 26ai) and 19c as LTS; 21c is an innovation release; 11.2, 12.1, 12.2, 18c past support (https://endoflife.date/api/oracle-database.json, checked 2026-11-20)
- Oracle: 26ai replaces 23ai as the long-term release (press release 2025-10-14) (https://www.oracle.com/sa/news/announcement/ai-world-database-26ai-powers-the-ai-for-data-revolution-2025-10-14/, checked 2026-11-20)

### Firebird
- Firebird: downloads page lists 5.0, 4.0 and 3.0 lines with releases dated 2026-04-17; 6.0 still in development per roadmap (https://firebirdsql.org/en/downloads/ and https://firebirdsql.org/en/roadmap, checked 2026-11-20)
- Firebird: firebird.conf defaults: WireCrypt Required (server) / Enabled (client); AuthServer Srp256; UserManager Srp; DatabaseAccess Full (docs advise against Full in production); ExternalFileAccess None; UdfAccess None, deprecated in 4.0; RemoteBindAddress empty binds all interfaces (https://firebirdsql.org/docs/chunk/en/refdocs/fbconf/fbconf-firebird-cfg.html, checked 2026-11-20)
- Firebird 3: SRP is the default authentication; Legacy_Auth sends almost plain passwords and needs WireCrypt lowered; UDFs deprecated (https://firebirdsql.org/file/documentation/release_notes/html/en/3_0/rlsnotes30.html, checked 2026-11-20)
- Firebird: ExternalFileAccess directories must not overlap DatabaseAccess or UdfAccess (https://firebirdsql.org/docs/chunk/en/refdocs/fbconf/fbconf-firebird-cfg.html, checked 2026-11-20)

### Db2, DuckDB, CockroachDB, Access, BDE
- Db2: endoflife.date lists 12.1 (no end date) and 11.5 end of support 2027-04-30; 11.1 and older ended (https://endoflife.date/api/ibm-db2.json, checked 2026-11-20)
- DuckDB: enable_external_access=false blocks file and remote reads; allowed_directories/allowed_paths stay allowed (read and write); lock_configuration=true freezes settings; order matters (https://duckdb.org/docs/current/operations_manual/securing_duckdb/overview, checked 2026-11-20)
- DuckDB: endoflife.date tracks LTS cycles (https://endoflife.date/api/duckdb.json, checked 2026-11-20)
- CockroachDB: Core retired 2024-11-18; Enterprise Free tier with mandatory telemetry for free clusters (https://cockroachlabs.com/enterprise-license-update, checked 2026-11-20)
- CockroachDB: endoflife.date lists 26.x releases with support and eol dates (https://endoflife.date/api/cockroachdb.json, checked 2026-11-20)
- Access: Access Database Engine 2016 Redistributable support ended 2025-10-14; replacement is the Microsoft 365 Access Runtime; not a server-side Jet replacement (https://www.microsoft.com/en-us/download/details.aspx?id=54920, checked 2026-11-20)
- BDE: deprecated, no new development; migrate to FireDAC; FireDAC does not support Paradox/dBase natively (https://docwiki.embarcadero.com/RADStudio/en/BDE_Application_Migration_(FireDAC) and https://docwiki.embarcadero.com/RADStudio/en/Using_BDE, checked 2026-11-20)

### MongoDB
- MongoDB: endoflife.date lists 9.0, 8.3, 8.0, 7.0 as supported majors; 6.0 ended 2025-07-31; x.1/x.2 rapid releases short-lived (https://endoflife.date/api/mongodb.json, checked 2026-11-20)
- MongoDB: security.authorization default disabled; values case sensitive from 9.0.0 (and 8.0.30 etc.), older versions silently ignored wrong case (https://www.mongodb.com/docs/manual/reference/configuration-options/, checked 2026-11-20)
- MongoDB: security.javascriptEnabled default true; disable if $where, mapReduce, $accumulator, $function unused; net.bindIp default localhost (https://www.mongodb.com/docs/manual/reference/configuration-options/, checked 2026-11-20)
- MongoDB 8.0: $where, $accumulator, $function deprecated; Queryable Encryption rangePreview removed, use Range (https://mongodb.com/docs/v8.0/release-notes/8.0-compatibility, checked 2026-11-20)
- MongoDB: checklist items: access control, least privilege, TLS, firewall + net.bindIp, --noscripting, Enterprise auditing, encryption at rest, Queryable Encryption / CSFLE (https://www.mongodb.com/docs/manual/administration/security-checklist/, checked 2026-11-20)
- Mongoose: connection-level sanitizeFilter was not applied (CVE-2026-125119, fixed 6.13.12, 7.8.13, 8.24.7, 9.11.4); global mongoose.set('sanitizeFilter') and per-query .sanitizeFilter() work (https://api.osv.dev/v1/vulns/CVE-2026-125119, checked 2026-11-20). Lead re-check 2026-11-20: an earlier connection-level bypass is CVE-2026-42334 ($nor operator, fixed 6.13.9, 7.8.9, 8.22.1, 9.1.6; https://osv.dev/vulnerability/CVE-2026-42334), and countDocuments() skipped sanitizeFilter in CVE-2026-125120. The reference cites no CVE number, only the safe configuration.

### Redis and Valkey
- Redis: Redis Open Source 8.0+ under RSALv2 or SSPLv1 or AGPLv3; 7.2 and earlier BSD-3 (https://redis.io/legal/licenses/, checked 2026-11-20)
- Valkey: BSD licensed, backed by the Linux Foundation (https://valkey.io/, checked 2026-11-20)
- Redis: ACLs since Redis 6; default user "on nopass ~* &* +@all"; -@dangerous category; key patterns do not limit FLUSHALL/FLUSHDB/SWAPDB, remove them explicitly; ACL GENPASS for strong passwords (https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/, checked 2026-11-20)
- Redis: endoflife.date lists 8.x releases; 7.2 and 7.4 with eol 2029-12-01 (https://endoflife.date/api/redis.json, checked 2026-11-20)
- Valkey: endoflife.date lists 9.x and 8.x lines (https://endoflife.date/api/valkey.json, checked 2026-11-20)

### Firebase
- Firebase App Check: when enforced, unverified requests to the product are rejected; check request metrics before enforcing; complements Authentication, does not stop all abuse (https://firebase.google.com/docs/app-check/enable-enforcement, checked 2026-11-20)

### DynamoDB
- DynamoDB: dynamodb:LeadingKeys restricts items by partition key; needs ForAllValues and a Null condition so Scan is not silently allowed; dynamodb:Attributes with dynamodb:Select and dynamodb:ReturnValues to hide attributes (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html, checked 2026-11-20)
- DynamoDB: encryption at rest always on with KMS; use IAM roles, not stored keys; VPC endpoint with aws:sourceVpce; client-side encryption; no sensitive data in primary key names or values (they appear in CloudTrail logs) (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices-security-preventative.html, checked 2026-11-20)
- DynamoDB: PartiQL ExecuteStatement takes Parameters as a list of AttributeValue for ? placeholders (https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_ExecuteStatement.md, checked 2026-11-20)

### Cassandra and ScyllaDB
- Cassandra: default AllowAllAuthenticator and AllowAllAuthorizer; built-in cassandra/cassandra superuser; create another superuser and disable the default; client connections unencrypted unless client_encryption_options enabled (https://cassandra.apache.org/doc/5.0/cassandra/managing/operating/security.html, checked 2026-11-20)
- Cassandra: endoflife.date lists 5.0, 4.1, 4.0 supported; 3.x ended 2024-09-05 (https://endoflife.date/api/apache-cassandra.json, checked 2026-11-20)
- ScyllaDB: moved to source-available license; 2025.1 first source-available release; 6.2 last AGPL release (https://www.scylladb.com/2025/04/08/announcing-scylladb-2025-1 and https://www.scylladb.com/source-available-faq, checked 2026-11-20)

### Elasticsearch and OpenSearch
- Elasticsearch: security enabled by default since 8.0 with auto-generated TLS for transport and HTTP (https://www.elastic.co/guide/en/elasticsearch/reference/8.x/targz.html, checked 2026-11-20)
- Elasticsearch: query_string not recommended for search boxes; use simple_query_string; allow_leading_wildcard can be set false (https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-query-string-query, checked 2026-11-20)
- OpenSearch: from 2.12 the demo security config requires OPENSEARCH_INITIAL_ADMIN_PASSWORD; before that the default was admin (https://docs.opensearch.org/3.4/security/configuration/demo-configuration/ and https://opensearch.org/blog/replacing-default-admin-credentials/, checked 2026-11-20)
- OpenSearch: endoflife.date lists 3 and 2 lines (https://endoflife.date/api/opensearch.json, checked 2026-11-20)

### Neo4j
- Neo4j: parameters cannot be used for labels, relationship types or property keys in plain form (MATCH (n:$param) invalid) (https://neo4j.com/docs/cypher-manual/current/syntax/parameters/, checked 2026-11-20)
- Neo4j: dynamic labels/types with $(...) in Cypher 5.26+, value from a parameter (https://neo4j.com/blog/developer/cypher-dynamism/, checked 2026-11-20)
- Neo4j APOC: some procedures run whole queries from input; dbms.security.procedures.allowlist defaults to loading all, override with a minimal list (https://neo4j.com/docs/apoc/current/security-guidelines/ and https://neo4j.com/docs/apoc/current/installation/, checked 2026-11-20)

### ClickHouse, InfluxDB, TimescaleDB
- ClickHouse: query parameters written {name:Type}, values sent as param_name (https://clickhouse.com/docs/interfaces/http_interface/, checked 2026-11-20)
- ClickHouse: a client with no parameters connects as user default with no password (https://clickhouse.com/docs/integrations/language-clients/python/driver-api, checked 2026-11-20)
- ClickHouse: access_management flag enables SQL-driven user management, which the docs recommend (https://ClickHouse.com/docs/en/operations/settings/settings-users, checked 2026-11-20)
- InfluxDB 3: SQL parameterized queries use $name with a params object; stated to help prevent injection (https://docs.influxdata.com/influxdb3/core/query-data/sql/parameterized-queries/, checked 2026-11-20)
- InfluxDB 3: admin token grants access to all actions; database tokens for scoped access (https://docs.influxdata.com/influxdb3/core/admin/tokens/, checked 2026-11-20)

### Vector databases and RAG
- OWASP: Top 10 for LLM Applications 2025 is the current edition; LLM01 Prompt Injection; LLM08 Vector and Embedding Weaknesses (cross-tenant leakage, embedding inversion, poisoning; mitigations: permission-aware stores, partitioning, source validation, retrieval logs) (https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/, checked 2026-11-20)
- pgvector: iterative index scans from 0.8.0 for filtered queries returning too few rows (https://github.com/pgvector/pgvector, checked 2026-11-20)
- Qdrant: self-deployed instances are not secure by default; api_key (1.2.0+), read_only_api_key (1.7.0+), JWT RBAC with jwt_rbac: true (1.9.0+); connections unencrypted by default (https://qdrant.tech/documentation/security.md, checked 2026-11-20)
- Milvus: authentication off until enabled (https://milvus.io/docs/authenticate.md, checked 2026-11-20)
- Chroma: v1.0.0 ships no built-in authentication in the open-source server; old CHROMA_SERVER_AUTHN_* variables are historical (https://docs.trychroma.com/reference/server-env-vars.md, checked 2026-11-20)

### Added during writing (second verification pass)
- MySQL: caching_sha2_password needs TLS, socket, or RSA key exchange on the first login after a password change; otherwise "Authentication requires secure connection" (https://dev.mysql.com/doc/refman/8.4/en/caching-sha2-pluggable-authentication.html, checked 2026-11-20)
- MySQL 8.0: default server charset utf8mb4 and collation utf8mb4_0900_ai_ci (https://dev.mysql.com/doc/refman/8.0/en/charset-server.html, checked 2026-11-20)
- PostgreSQL: password_encryption = 'scram-sha-256', reset every password, then switch pg_hba.conf from md5; md5 hashes are not converted automatically (https://www.postgresql.org/docs/current/auth-password.html, checked 2026-11-20)
- PostgreSQL: SECURITY DEFINER functions should SET search_path to trusted schemas then pg_temp last (https://www.postgresql.org/docs/current/sql-createfunction.html, checked 2026-11-20)
- PostgreSQL: table owners bypass RLS unless ALTER TABLE ... FORCE ROW LEVEL SECURITY; superusers and BYPASSRLS always bypass (https://www.postgresql.org/docs/current/ddl-rowsecurity.html, checked 2026-11-20)
- psycopg: sql module with Identifier for dynamic table/field names (https://www.postgresql.org/message-id/356f506e-1cbd-be9a-0fd6-bc1e50d9c9e1%40aklaver.com, checked 2026-11-20; mailing list, maintainer cited)
- SQL Server: xp_cmdshell disabled by default on new installations, should stay disabled (https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/xp-cmdshell-server-configuration-option, checked 2026-11-20)
- SQL Server: wrap identifiers from input in QUOTENAME(); review code calling EXEC/sp_executesql (https://learn.microsoft.com/sql/relational-databases/security/sql-injection, checked 2026-11-20)
- Oracle: DBMS_ASSERT (ENQUOTE_NAME, SIMPLE_SQL_NAME, QUALIFIED_SQL_NAME) for identifiers in dynamic SQL (https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_ASSERT.html, checked 2026-11-20)
- CockroachDB: SERIALIZABLE by default; client must retry on 40001 "restart transaction" (https://docs.cockroachlabs.com/docs/stable/transactions, checked 2026-11-20)
- DuckDB: extensions run with process privileges; autoload_known_extensions/autoinstall_known_extensions false, allow_community_extensions false; "Treat SQL in DuckDB like code"; settings are not a sandbox (https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview.html, checked 2026-11-20)
- Db2: db2audit tool and AUDIT statement for auditing; RCAC chapters in the security guide (https://www.ibm.com/docs/SSEPGG_11.1.0/com.ibm.db2.luw.admin.cmd.doc/doc/r0002072.html, checked 2026-11-20)
- Firebird: gbak -b backup, -c restore to a new file (https://firebirdsql.org/manual/gbak-cmdline.html, checked 2026-11-20)
- Firebird: Dialect 1 only for legacy InterBase; DATE holds date and time in Dialect 1; double quotes delimit identifiers in Dialect 3; Dialect 3 default (https://firebirdsql.org/file/documentation/chunk/en/refdocs/fblangref50/fblangref50-structure.html, checked 2026-11-20)
- Firebird: RDB$GET_CONTEXT('SYSTEM','ENGINE_VERSION') returns server version (2.1+); databases.conf holds aliases (3.0+, aliases.conf before) (https://firebirdsql.org/file/documentation/chunk/en/refdocs/fblangref50/fblangref50-functions.html and https://firebirdsql.org/docs/chunk/en/refdocs/fbconf/fbconf-databases.html, checked 2026-11-20)
- Access: PARAMETERS declaration and QueryDef parameters for parameter queries (https://msdn.microsoft.com/en-us/library/office/ff845220.aspx, checked 2026-11-20)
- Cassandra: PasswordAuthenticator, CassandraAuthorizer, server_encryption_options names (https://cassandra.apache.org/doc/5.0/cassandra/managing/operating/security.html, checked 2026-11-20)
- ClickHouse: readonly=1 allows reads and session-only changes; readonly=2 also allows SET, temporary tables and RESTORE (https://clickhouse.com/docs/operations/settings/permissions-for-queries, checked 2026-11-20)
- InfluxDB 1.x: authentication disabled by default; auth-enabled = true in [http] plus an admin user (https://docs.influxdata.com/influxdb/v1/administration/authentication_and_authorization/, checked 2026-11-20)
- Neo4j: neo4j user password defaults to neo4j and must be changed at first login (https://neo4j.com/docs/operations-manual/current/configuration/set-initial-password/, checked 2026-11-20)
- Milvus: enable with common.security.authorizationEnabled true; root user created with password Milvus (https://milvus.io/docs/authenticate.md, checked 2026-11-20)
- DynamoDB: ExpressionAttributeNames (#name) and ExpressionAttributeValues (:value) placeholders (https://docs.aws.eu/amazondynamodb/latest/developerguide/ExpressionPlaceholders.html, checked 2026-11-20)
- Redis: protected mode guards unprotected instances; admins can still disable it (https://redis.io/docs/latest/operate/oss_and_stack/management/security/, checked 2026-11-20)

- SQLite: untrusted SQL: SQLITE_DBCONFIG_DEFENSIVE, lower limits, authorizer, progress handler; untrusted files: trusted_schema OFF, integrity_check or quick_check first, cell_size_check, mmap_size=0 (https://sqlite.org/security.html, checked 2026-11-20)
- SQLite: foreign_keys default OFF; DELETE is the default journal mode (WAL must be set); busy_timeout pragma; VACUUM INTO as a backup alternative (https://sqlite.org/pragma.html and https://sqlite.org/lang_vacuum.html, checked 2026-11-20)
- PostgreSQL: format() %I quotes identifiers (equivalent to quote_ident) (https://www.postgresql.org/docs/current/functions-string.html, checked 2026-11-20)
- MongoDB: lifecycle table: 7.0 EOL 2027-08-31, 8.0 2029-10-31, 8.2 2026-07-31, 8.3 2029-10-31, 9.0 2031-10-31 (Enterprise Advanced) (https://www.mongodb.com/legal/support-policy/lifecycles, checked 2026-11-20)
- MongoDB: COLLSCAN = collection scan in explain output (https://www.mongodb.com/docs/manual/reference/explain-results/, checked 2026-11-20)
- MySQL: utf8 is a deprecated alias for utf8mb3; utf8mb3 deprecated, use utf8mb4 (https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8.html, checked 2026-11-20)
- Firestore rules: ownership pattern request.auth != null && request.auth.uid == userId (path wildcard) (https://firebase.google.com/docs/firestore/security/rules-conditions, checked 2026-11-20)
- Supabase: policy example using (select auth.uid()) = user_id (https://supabase.com/docs/guides/database/postgres/row-level-security.md, checked 2026-11-20)
- DuckDB: prepared statements accept ?, $1 and $name (https://duckdb.org/docs/2.0/sql/query_syntax/prepared_statements.html, checked 2026-11-20)
- Firebird: database without DEFAULT CHARACTER SET gives columns charset NONE (bytes copied without conversion); UTF8 recommended (https://firebirdsql.org/file/documentation/chunk/en/refdocs/fblangref50/fblangref50-datatypes-chartypes.html, checked 2026-11-20)
- SQL Server: Always Encrypted keeps keys away from the Database Engine (https://learn.microsoft.com/en-us/sql/relational-databases/security/encryption/always-encrypted-database-engine, checked 2026-11-20); TDE whole-database vs Always Encrypted columns (https://azure.microsoft.com/blog/transparent-data-encryption-or-always-encrypted/, checked 2026-11-20); READ_COMMITTED_SNAPSHOT uses row versions under READ COMMITTED (https://learn.microsoft.com/zh-cn/dotnet/framework/data/adonet/sql/snapshot-isolation-in-sql-server, checked 2026-11-20)
- Oracle: Unified Auditing, TDE, native network encryption in the security guide (https://docs.oracle.com/en/database/oracle/oracle-database/23/dbseg/introduction-to-oracle-database-security.html, checked 2026-11-20); EXPLAIN PLAN FOR then DBMS_XPLAN.DISPLAY (https://docs.oracle.com/en/database/oracle/oracle-database/23/arpls/DBMS_XPLAN.html, checked 2026-11-20)
- Db2: DBADM and SECADM are administrative database authorities, cannot be granted to PUBLIC (https://www.ibm.com/docs/SSEPGG_11.5.0/com.ibm.db2.luw.admin.sec.doc/doc/c0055206.html, checked 2026-11-20)
- BDE: removed from the RAD Studio installer (https://upgrade-center.embarcadero.com/upgrading/firedac, checked 2026-11-20)

## Changed from the previous text
- mysql.md: added the LTS/Innovation model and the 9.7 to YY.M calendar versioning change; 8.0 is now end of life (2026-04-30), a finding.
- mysql.md: added auth plugin section: caching_sha2_password, mysql_native_password removed in 9.0 (old PHP/drivers break), MariaDB unix_socket/ed25519/PARSEC.
- mysql.md: added 8.4 removals that break scripts (MASTER/SLAVE statements, default_authentication_plugin, mysql_upgrade, AUTO_INCREMENT on FLOAT).
- mysql.md: PDO SSL constants now Pdo\Mysql::ATTR_SSL_CA (8.4+), old names deprecated in 8.5; added ATTR_SSL_VERIFY_SERVER_CERT.
- mysql.md: MariaDB collation guidance changed from "use utf8mb4_unicode_ci" to "read the server default; uca1400 on newer servers".
- bancos-outros.md: now relational only; added Firebird, Db2, DuckDB, CockroachDB, Access, DBF/Paradox; MongoDB, Redis, Firebase moved to bancos-nosql.md.
- PostgreSQL: md5 deprecated (18+), RADIUS removed (19+), search_path hijack, upgraded databases keep CREATE on public, Supabase views/security definer/new key names.
- SQLite: STRICT, trusted_schema, defensive mode for untrusted files.
- SQL Server: Microsoft.Data.SqlClient instead of System.Data.SqlClient; Encrypt=Strict (TDS 8.0); TrustServerCertificate=true is not a fix.
- bancos-nosql.md (new): MongoDB (authorization default disabled, case-sensitive values, Mongoose sanitizeFilter connection-level bug), Redis/Valkey license split and ACL details, DynamoDB LeadingKeys with Null condition, Cassandra defaults, Elasticsearch/OpenSearch, Neo4j, ClickHouse, InfluxDB, vector DBs and RAG.

## Not verified
- MySQL planned 28.4 LTS (search summary only). Left out.
- MariaDB uca1400 collations "since 10.10" (secondary sources). Written as "newer MariaDB".
- MariaDB version when unix_socket became the root default. Written as "usually".
- MariaDB LTS duration: policy page (3 years community binaries) and endoflife.date (5 years for 11.4) disagree. Left out.
- MariaDB exact default collation per version: docs and real installs disagree. The reference tells the reader to read it from the server.
- Elasticsearch AGPL license option (2024): not confirmed on elastic.co. Left out.
- CVE-2025-49844 (Redis Lua use-after-free): NVD page did not load. The reference keeps only the durable rule (restrict scripting per ACL, patch).
- DynamoDB PITR window and DeletionProtectionEnabled parameter name: secondary sources only. Written without numbers or parameter names.
- pgvector version that added HNSW. Left out.
- Cassandra 5.0 MutualTlsAuthenticator: third-party only. Left out.
- CockroachDB insecure-mode warning text: third-party mirrors only; rule written generically.
- Firebird SYSDBA default password on old installers: not confirmed; written as "any default or well-known SYSDBA password".
- Firebird default port number, client DLL names, Python driver names, DBF/Paradox file extensions, legacy code page names: not confirmed; removed or written generically.
- Access: file-password encryption strength, Jet 4.0 status, Compact and Repair naming: not confirmed; written generically.
- SQL Server Query Store, SET XACT_ABORT ON, BACKUP WITH CHECKSUM, SQL Server Audit naming: not confirmed this session; removed or generalized.
- Oracle RMAN and AWR: not confirmed this session; removed.
- Pinecone, TimescaleDB, InfluxDB 2.x specifics: not researched; written as version-independent rules.
- Oracle 26ai support end date: not cross-checked against Oracle's PDF; no date in the reference.
- Carried over from the old text, long-standing, not re-fetched this session: require_secure_transport, slow_query_log, innodb_buffer_pool_size, REPEATABLE READ default, EXPLAIN type=ALL / Using filesort (MySQL); pg_dump -Fc, pg_restore, pg_stat_statements, EXPLAIN (ANALYZE, BUFFERS), READ COMMITTED default (PostgreSQL); .backup (SQLite); sp_executesql, SqlParameter, sa, db_owner, sysadmin (SQL Server); maxmemory, KEYS vs SCAN (Redis); mongodump, $jsonSchema, explain("executionStats") (MongoDB).
- New wording not individually fetched: psycopg sql.Identifier (mailing list only), Elasticsearch document- and field-level security, MongoDB "reject keys starting with $" (general guidance), Firebase Storage rules wording.
