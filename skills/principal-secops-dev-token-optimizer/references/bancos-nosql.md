# Non-relational databases: MongoDB, Redis, Firebase, DynamoDB, search, graph, analytics and vector stores

Version policy: follow `versoes-e-fontes.md`. Read the server and driver versions from the project (`package.json`, `requirements.txt`, `docker-compose.yml` image tags, the cloud console) or the server (`db.version()`, `INFO server`, `SELECT version()`), then check endoflife.date (`mongodb`, `redis`, `valkey`, `apache-cassandra`, `elasticsearch`, `opensearch`, `neo4j`, `clickhouse`, `influxdb`) or the vendor page. Managed cloud services (Firebase, DynamoDB, Pinecone) have no version to pin; check the SDK version and the service's current docs. Relational engines: `bancos-outros.md` and `mysql.md`.

## Contents
- Rules for every store
- MongoDB
- Redis and Valkey
- Firebase
- DynamoDB
- Cassandra and ScyllaDB
- Elasticsearch and OpenSearch
- Neo4j
- ClickHouse
- InfluxDB and TimescaleDB
- Vector databases and RAG

## Rules for every store
* "NoSQL" does not mean "no injection". Every query language here (filters, Cypher, CQL, PartiQL, InfluxQL, search DSL) is injectable when built from strings or from raw request objects. Use the driver's parameters; validate types and allowlist field names.
* Several of these engines ship with authentication off (MongoDB, Cassandra, the Redis default user, Milvus, self-hosted Qdrant, InfluxDB 1.x) or with a well-known default account. Before anything else: authentication on, default account changed or disabled, port bound to a private interface, firewall closed.
* Dedicated application account with only the permissions it uses; credentials from environment variables or a secret store.
* TLS with certificate verification whenever traffic crosses a network.
* Access control lives on the server. A rule checked only in the front end or the mobile app is no rule.
* Backup on purpose (snapshot or dump), copy kept where the server cannot overwrite it, restore tested every quarter. A cache is not a backup.
* Personal data (LGPD): know which collections or keys hold it, encrypt the sensitive fields, have a deletion path. CPF, CNPJ, CEP and phone stored as strings.

## MongoDB
* NoSQL injection is real: a request body passed straight into a filter lets `{"$ne": null}` or `{"$gt": ""}` match any record (login bypass). Validate input with a schema (zod, Joi, pydantic, `$jsonSchema`), accept only the expected scalar types, reject keys starting with `$`.
* Mongoose: `mongoose.set('sanitizeFilter', true)` globally, or `.sanitizeFilter()` per query. Setting it only in `mongoose.connect()` options was not applied in several releases; keep Mongoose patched. Wrap only operators you wrote yourself in `mongoose.trusted()`.
* `security.authorization` defaults to `disabled`: set it to `enabled` (exact lowercase; older versions silently ignore `Enabled` and stay open). Create the user administrator first, then least-privilege users per app.
* `net.bindIp` stays on localhost or a private address; never `0.0.0.0` with a public IP. TLS for all connections, internal auth (keyfile or X.509) between replica set members.
* Server-side JavaScript (`$where`, `mapReduce`, `$function`, `$accumulator`) is on by default: set `security.javascriptEnabled: false` (or `--noscripting`) when unused. `$where`, `$function` and `$accumulator` are deprecated (8.0+).
* Encryption: at rest via the storage engine or disk encryption; Queryable Encryption or Client-Side Field Level Encryption for CPF and similar fields. Range queries on Queryable Encryption use the `Range` algorithm (`rangePreview` was removed in 8.0).
* Tuning: an index for every frequent filter and sort; check with `explain("executionStats")` (look for `COLLSCAN`). Projections instead of fetching whole documents. Arrays that grow without bound inside one document (logs, comments) belong in their own collection.
* Lifecycle: support windows differ per line (some minor lines expire within months, others last years). Read the end date of the exact line at mongodb.com/legal/support-policy/lifecycles.
* Backup with `mongodump` or the platform's snapshots, and restore-test.

## Redis and Valkey
* Never exposed to the internet. Keep `protected-mode yes`, bind to a private interface, firewall the port, TLS where it crosses a network.
* ACL users (Redis 6+), not the shared `requirepass`. A fresh server's `default` user has `nopass` and every command: give it a strong password or turn it `off`, and create one user per app with only its key prefix and commands (`ACL SETUSER app on >secret ~app:* +@read +@write -@dangerous`). Generate passwords with `ACL GENPASS`.
* Key patterns do not stop `FLUSHALL`, `FLUSHDB` or `SWAPDB`: remove them explicitly per user.
* Lua scripting (`EVAL`, `EVALSHA`) has had critical memory-safety flaws: deny `@scripting` to users that do not need it and patch promptly.
* Treat it as a cache or a queue, not the only copy of important data. Every cache key gets a TTL; set `maxmemory` and an eviction policy. Persistence (RDB or AOF) chosen on purpose.
* Never `KEYS *` in production; iterate with `SCAN`. Never put user input into a key name without a fixed prefix and length limit.
* Licensing: Redis 7.2 and earlier are BSD; Redis 8+ is RSALv2, SSPLv1 or AGPLv3 at the user's choice. Valkey is the BSD-licensed fork under the Linux Foundation, protocol-compatible for common use. Flag the license before a client ships Redis inside a product (`compliance-licencas.md`).

## Firebase (Firestore, Realtime Database, Storage)
* The security rules are the access control. Never ship `allow read, write: if true` or the "test mode" rules; every rule checks `request.auth` and that the document belongs to that user (`request.auth != null && request.auth.uid == userId`, with `userId` from the path).
* Validate type, size and allowed fields in the rules, and test them in the emulator before publishing.
* The web config (`apiKey`) is public by design and is not a secret. The Admin SDK service-account JSON is a secret: server only, never in the repository. The Admin SDK bypasses the rules.
* App Check reduces abuse from scripts and fake clients; it complements rules and Authentication, never replaces them. Watch the request metrics before enforcing, or old app versions stop working.
* Storage: rules on paths per user, file size and content type checked in the rule.

## DynamoDB
* Requests go through the SDK with typed attributes, so classic injection is rare. PartiQL (`ExecuteStatement`) is the exception: use `?` placeholders with `Parameters`, never build the statement string from input. In expressions use `ExpressionAttributeValues` and `ExpressionAttributeNames`.
* IAM roles, never access keys stored in the app or on the server. Least privilege per table and action.
* Per-user isolation: `dynamodb:LeadingKeys` with `ForAllValues:StringEquals` on the user's id, plus a `Null` condition on the same key, or `Scan` slips through. Hide columns with `dynamodb:Attributes` together with `dynamodb:Select` and `dynamodb:ReturnValues`.
* Never put CPF, e-mail or other sensitive values in partition or sort keys: key values show up in CloudTrail and other logs. Use opaque ids; client-side encryption (AWS Database Encryption SDK) for sensitive attributes.
* Private access through a VPC endpoint with an endpoint policy. Encryption at rest is always on (KMS).
* Turn on point-in-time recovery and deletion protection for tables that hold real data.
* Tuning: design keys for the access patterns; a `Scan` on a big table is slow and costly. Avoid hot partitions (one key taking most traffic).

## Cassandra and ScyllaDB
* Prepared statements with bound values in CQL; never concatenate.
* Cassandra defaults are open: `AllowAllAuthenticator` and `AllowAllAuthorizer`. Switch to `PasswordAuthenticator` and `CassandraAuthorizer`, log in with the built-in `cassandra`/`cassandra` account once, create your own superuser, then disable the default.
* Client and node-to-node encryption are off unless configured (`client_encryption_options`, `server_encryption_options`).
* Roles per app with grants per keyspace. A query that needs `ALLOW FILTERING` is a modelling problem: create a table for that query instead.
* ScyllaDB moved from AGPL to a source-available license (2025.1+); check the terms and size limits before choosing it.

## Elasticsearch and OpenSearch
* Never expose the cluster's HTTP or transport ports to the internet. Security (auth plus TLS) is on by default from Elasticsearch 8.0; on older clusters it must be turned on, not assumed.
* OpenSearch: the security plugin must stay enabled; from 2.12 the demo setup requires `OPENSEARCH_INITIAL_ADMIN_PASSWORD`. Earlier clusters may still have `admin`/`admin`: change it.
* Build queries as JSON objects in the client (`match`, `term`, `bool`), never by pasting input into a query string. Search boxes: `simple_query_string`, not `query_string` (whose syntax errors and field targeting are exposed to the user); set `allow_leading_wildcard` to `false` when wildcards are allowed.
* API keys or users scoped to the indices the app needs, read-only for the front end's search service. Document-level or field-level security for multi-tenant indices.
* Scripts and search templates only from your code, never from user input.
* Snapshots to a repository the cluster cannot delete, restore-tested.

## Neo4j
* Parameters (`$name`) for every value. Labels, relationship types and property keys cannot be plain parameters (`MATCH (n:$param)` is invalid): use the dynamic form `$(...)` with a parameter (Cypher 5.26+) or an allowlist; never concatenate a label from input.
* APOC procedures that run Cypher from a string (`apoc.cypher.run` and similar) reintroduce injection; avoid them with input, and set `dbms.security.procedures.allowlist` to the minimum list (the default loads everything).
* The `neo4j` user's password defaults to `neo4j` and must be changed at first login: set a strong one at install; app user with a role limited to its graph. Bolt and HTTP with TLS; the browser UI not open to the internet.

## ClickHouse
* Server-side parameters `{name:Type}` (values sent as `param_name`, or the driver's parameter argument); never format values into SQL.
* A client with no credentials connects as `default` with an empty password on a fresh install. Give `default` a strong password or restrict it to localhost, and create named users through SQL-driven access control (`access_management`).
* Read-only users (`readonly = 1`) for dashboards and BI tools; per-user quotas and query limits so one report cannot exhaust the server.
* HTTP and native protocol ports bound to the private network; TLS where traffic crosses networks.

## InfluxDB and TimescaleDB
* InfluxDB 3: parameterized queries with `$name` and a `params` object (SQL and InfluxQL). Never paste input into a query string.
* Tokens: the admin token does everything; give apps database tokens with only read or write on their database. Tokens never in front-end code.
* InfluxDB 1.x: authentication is off by default (`auth-enabled = true` in `[http]`, plus an admin user). 1.x and 2.x differ from 3.x: check which line the project runs before applying this advice.
* TimescaleDB is a PostgreSQL extension: all PostgreSQL rules in `bancos-outros.md` apply. Retention and compression policies set on purpose, so old data is dropped by plan, not by accident.

## Vector databases and RAG
Covers pgvector, Qdrant, Milvus, Chroma, Pinecone and any store behind a retrieval-augmented chatbot. Map to OWASP Top 10 for LLM Applications (2025 edition at the time of writing; confirm at genai.owasp.org): LLM01 Prompt Injection, LLM08 Vector and Embedding Weaknesses.
* **Lock the store.** Qdrant self-hosted is open by default: set `api_key` (and `read_only_api_key` for the query side), TLS, and JWT RBAC (`jwt_rbac: true`) for per-collection rights. Milvus runs without authentication until `common.security.authorizationEnabled: true`; then change the default `root` password (`Milvus`). Chroma's open-source server (1.0+) has no built-in authentication: keep it on localhost or behind an authenticating proxy. Pinecone and other hosted stores: API key only on the server, one key per environment.
* **Tenant isolation before similarity.** Every query filters by tenant or user on the server (separate collection, namespace or partition per tenant, or a mandatory metadata filter the app adds itself). Never trust a filter value sent by the client. Vector search with a missing filter returns other customers' documents.
* **Permissions follow the source.** Store the source document's access list with each chunk and filter by the asking user's rights at query time. A RAG bot indexed with admin rights answers anyone with admin data.
* **Embeddings are personal data.** Embeddings can be partly inverted back to the text. Treat the vector store with the same LGPD controls as the source (access, retention, deletion: deleting a customer deletes their chunks).
* **Retrieved text is untrusted input.** Documents, web pages and uploads can carry hidden instructions (indirect prompt injection). Keep retrieved text in a clearly delimited data section, never in the system prompt; the model gets no tool or action that the asking user could not perform; validate tool calls on the server.
* **Ingestion is a write path.** Only trusted, validated sources get indexed; strip hidden content (white text, HTML comments, metadata) before embedding; log who added what. A poisoned document keeps answering until it is removed.
* **Output.** Escape model output before rendering it as HTML or Markdown with links or images (data can leak through image URLs). Log retrievals (who asked, which chunks) without logging secrets.
* pgvector: the PostgreSQL rules apply (RLS for tenant isolation works on vector tables too). An approximate index with a restrictive `WHERE` can return too few rows; iterative index scans (0.8.0+) fix that, check the installed version.
