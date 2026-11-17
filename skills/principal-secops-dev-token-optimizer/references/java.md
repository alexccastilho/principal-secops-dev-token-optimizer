# Java — Oracle Code Conventions / Effective Java standards

Version policy: follow `versoes-e-fontes.md`. Read the release set in `pom.xml` or `build.gradle`, look up the current LTS and support dates (Oracle Java SE support roadmap, adoptium.net/support), and target the newest LTS the dependencies support. An older LTS is acceptable on an existing codebase with a flagged upgrade path; a release without public security updates on a public app is a finding.

## Language and standards
* Records for immutable data, sealed interfaces for closed hierarchies, switch expressions with pattern matching, `var` only when the type is obvious from the right-hand side.
* Newer additions worth using when the project's release includes them: virtual threads for I/O-bound concurrency (Java 21+), record patterns, sequenced collections. Check the JEP status of anything marked preview before relying on it.
* Oracle naming: PascalCase classes, camelCase methods and fields, UPPER_SNAKE constants, one public class per file.
* Immutability first: `final` fields, `List.of()` / `Map.of()`, defensive copies of mutable arguments.
* `Optional` as a return type for "maybe absent", never for fields or parameters. Never return a null collection; return an empty one.
* try-with-resources for everything `AutoCloseable`.
* Build with Maven or Gradle, versions pinned, wrapper committed. No jars copied by hand.

## Security
* SQL: `PreparedStatement` only. JPA and Hibernate with named parameters, never string-built JPQL. `@Query` with concatenation is injection.
* Passwords: Argon2 or bcrypt through Spring Security `PasswordEncoder`. Never homemade crypto.
* Validation at the boundary: Bean Validation (`@NotNull`, `@Size`, `@Pattern`, custom validators) on DTOs before any logic. Validate the DTO, never bind an entity directly to a request body.
* Deserialization: never native Java serialization on untrusted data. JSON via Jackson with default typing OFF and unknown properties rejected.
* Secrets from environment or a config server. Never in a committed `application.properties`.
* Spring Security: CSRF enabled for session-based apps, security headers on, method-level `@PreAuthorize` for least privilege, and an explicit `authorizeHttpRequests` chain that denies by default.
* Actuator endpoints closed or behind auth in production. An open `/actuator/env` leaks every secret.

## Exceptional conditions
* Never swallow an exception. Log with context or rethrow wrapped.
* `@ControllerAdvice` for a centralized handler: generic body to the client with a correlation id, full detail to the log.
* An exception inside an authorization or payment path denies and rolls back. Never fail open.
* Checked exceptions on external calls get an explicit policy: retry with backoff, circuit breaker, or fail closed.

## Supply chain
* `mvn versions:display-dependency-updates` and OWASP Dependency-Check in the build. Fail the build on a critical CVE.
* Pin plugin versions too. An unpinned Maven plugin is remote code execution at build time.
* Prefer artifacts from Maven Central with a published signature.

## Performance and tuning
* `StringBuilder` in loops. Streams for clarity, plain loops in measured hot paths.
* Connection pooling (HikariCP is the Spring Boot default). Never open a connection per request.
* Measure before tuning: JFR or JMH. Then right-size the heap (`-Xms` equal to `-Xmx`); G1 is fine for most services.
* Cache pure expensive computations (Caffeine) with explicit TTL and size bounds.
* JPA: load relations deliberately, watch for N+1, fix with `join fetch` or an `EntityGraph`.
* Virtual threads for many concurrent blocking calls, but keep the connection pool sized to the database, not to the thread count.
