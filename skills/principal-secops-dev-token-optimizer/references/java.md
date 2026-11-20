# Java: Oracle Code Conventions and Effective Java (Spring Boot, Jakarta EE, Quarkus)

Version policy: follow `versoes-e-fontes.md`. Read `<maven.compiler.release>` or `<release>` in `pom.xml`, `toolchain`/`sourceCompatibility` in `build.gradle`, `.java-version` or the Docker base image, then check the vendor roadmap (oracle.com/java/technologies/java-se-support-roadmap.html, adoptium.net/support) or endoflife.date (`oracle-jdk`, `eclipse-temurin`, `spring-boot`, `quarkus-framework`). Target the newest LTS the framework supports; an older LTS is acceptable on existing code with a flagged upgrade path. A JDK or framework line without public security updates on a public app is a finding. Notes marked "(21+)" refer to the Java release; preview features are never used in production code. Spring Boot system requirements: docs.spring.io/spring-boot/system-requirements.html.

## Contents
- Standards and style
- Security
- Exceptional conditions
- Supply chain
- Tuning
- Traps and fixes
- Legacy Java: safe maintenance and staged migration
- Spring Boot and Spring Security
- Jakarta EE and Quarkus

## Standards and style
* Oracle naming: PascalCase classes, camelCase members, UPPER_SNAKE constants. Formatter: the project's (google-java-format or Spotless); Checkstyle if configured.
* Immutability first: records, `final` fields, `List.of()`/`Map.of()`, defensive copies. `Optional` only as a return type. Never return a null collection.
* try-with-resources for every `AutoCloseable`. `var` only when the type is obvious.
* (21+) virtual threads, record patterns, pattern matching for `switch`, sequenced collections (`getFirst()`, `reversed()`).
* (24+) stream gatherers; the Security Manager is permanently disabled, so it cannot sandbox anything.
* (25+) scoped values (replace `ThreadLocal` for request context with virtual threads), flexible constructor bodies (validate arguments before `super(...)`), module import declarations, compact source files for small scripts, Key Derivation Function API.
* Still preview, do not use in production: structured concurrency, PEM encodings API, lazy/stable constants, primitive types in patterns.
* Build with Maven or Gradle, wrapper committed, versions pinned. Static analysis: SpotBugs with the Find Security Bugs plugin, Error Prone if configured.

## Security
* SQL: `PreparedStatement` only. JPA/Hibernate with named parameters or Criteria; `@Query` or `createQuery` built by concatenation is injection. `ORDER BY` columns from an allowlist.
* Passwords: Spring Security `PasswordEncoderFactories.createDelegatingPasswordEncoder()` (stores the `{id}` prefix, so the algorithm can change later) or `Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8()` (needs BouncyCastle). Never homemade crypto or `MessageDigest` for passwords.
* Validation: Bean Validation (`@NotNull`, `@Size`, `@Pattern`, custom) on DTOs with `@Valid`. Never bind an entity directly to a request body (mass assignment).
* Deserialization: never native Java serialization (`ObjectInputStream`) on untrusted data; if legacy code must, set an `ObjectInputFilter` allowlist. Jackson: no default typing, no `@JsonTypeInfo(use = Id.CLASS)` on input, unknown properties rejected explicitly.
* XML: disable DTDs and external entities on every parser (`XMLConstants.FEATURE_SECURE_PROCESSING`, `disallow-doctype-decl`) to block XXE.
* Commands: `ProcessBuilder` with an argument list; never `Runtime.exec(String)` with input, never `sh -c` with input.
* Paths: `base.resolve(input).normalize()` then `startsWith(base)` before any file access.
* Logging: never log secrets; keep Log4j 2 and Logback patched (message lookups in old Log4j were remote code execution).
* Secrets from the environment, a vault or a config server. Never in a committed `application.properties`.
* Crypto: `SecureRandom` for tokens, `MessageDigest.isEqual` for constant-time compare, AES-GCM for encryption. (24+) ML-KEM and ML-DSA are available in the JDK; (27+) TLS 1.3 hybrid post-quantum key exchange.

## Exceptional conditions
* Never swallow an exception: log with context or rethrow wrapped.
* Centralized handler (`@RestControllerAdvice` in Spring, `ExceptionMapper` in Jakarta REST): generic body with a correlation id, detail to the log. Keep the stack trace out of error responses: the default is `never` (property `spring.web.error.include-stacktrace` in current Boot docs, `server.error.include-stacktrace` in older lines).
* An exception inside authorization or payment denies and rolls back (`@Transactional` rolls back on unchecked exceptions only; declare `rollbackFor` for checked ones).
* External calls: timeouts on every HTTP client, retry with backoff, circuit breaker, or fail closed.

## Supply chain
* OWASP Dependency-Check (Maven or Gradle plugin, `failBuildOnCVSS`) in the build, with an NVD API key and a cached data directory in CI, or the platform's scanner (GitHub dependency review, OSV-Scanner). Fail the build on critical findings.
* `mvn versions:display-dependency-updates`, and Gradle dependency locking plus `verification-metadata.xml` for checksum verification.
* Pin plugin versions too: an unpinned Maven plugin is code execution at build time. Import the Spring Boot BOM instead of hand-picking versions.
* Prefer artifacts from Maven Central; check groupId spelling.

## Tuning
* Measure first: JFR (`-XX:StartFlightRecording`) or JMH for micro-benchmarks.
* Heap: `-Xms` equal to `-Xmx` for servers; containers use `-XX:MaxRAMPercentage`. G1 is the default and fine for most services.
* Connection pool (HikariCP in Spring Boot) sized to the database, not to the thread count, especially with virtual threads.
* (24+) `synchronized` no longer pins virtual threads; on 21 replace long `synchronized` blocks around I/O with `ReentrantLock` before enabling virtual threads.
* JPA: watch for N+1; fix with `join fetch` or an `@EntityGraph`. Set `spring.jpa.open-in-view=false` (default is true) so lazy loading cannot hide queries in the view layer.
* Cache pure expensive computations (Caffeine) with TTL and size bounds.

## Traps and fixes
* `String.equals` for comparing tokens: timing leak. `MessageDigest.isEqual`.
* `new Random()` for tokens or reset codes: `SecureRandom`.
* `catch (Exception e) { return true; }` in an auth check: fail open. Return deny.
* `@CrossOrigin("*")` with credentials: list exact origins in one CORS config.
* `permitAll()` on `/**` left from development: rules are evaluated in order, so put `anyRequest().authenticated()` (or `denyAll()`) last.
* Entity returned from a controller: lazy-loading exceptions and leaked fields. Map to a response DTO.
* `ThreadLocal` caches with virtual threads: one per task, memory grows. Scoped values (25+) or pass the context.

## Legacy Java: safe maintenance and staged migration
* Java 8 or 11 with Spring Boot 2 or `javax.*` that works: fix the reported fault first; never a rewrite.
* Stages: 1) pin the JDK in the build and CI, run Dependency-Check, add tests on critical paths; 2) move to the next LTS on a branch (8 to 11 to 17 to 21 to 25), fixing removed APIs and `--add-opens` warnings; 3) `javax.*` to `jakarta.*` (Spring Boot 3+, Jakarta EE 9+) with OpenRewrite recipes, reviewed per module; 4) framework major upgrades one at a time, applying each deprecation-preparation step first (for Spring Security, the 6.5 preparation guide before 7).
* Back up and deploy to staging before each stage.

## Spring Boot and Spring Security
* Spring Boot 4 brings Spring Framework 7, Spring Security 7, Jackson 3 (Jackson 2 deprecated), Servlet 6.1 and Tomcat 11. Upgrade from the latest 3.5 patch, fixing deprecations first.
* Spring Security 7: lambda DSL only (`.and()` chains no longer compile), `with()` instead of `apply()` for custom DSLs. Use `authorizeHttpRequests` and end with `anyRequest().authenticated()`.
* CSRF stays enabled for cookie or session auth; disable only for a stateless token API and say why. Method security with `@EnableMethodSecurity` and `@PreAuthorize` for object-level checks.
* Actuator: only `health` is exposed over HTTP by default. Expose more with `management.endpoints.web.exposure.include` only behind auth, never `*` on a public port. `heapdump` contains everything in memory, secrets included; `env` and `configprops` mask values only while `show-values` stays at its default. A custom `SecurityFilterChain` disables Boot's actuator protection, so write those rules yourself.
* Devtools and H2 console never in production builds.

## Jakarta EE and Quarkus
* Jakarta EE: `jakarta.*` namespace (EE 9+); Jakarta Security (`@RolesAllowed`, `HttpAuthenticationMechanism`); container-managed datasources; never disable the container's CSRF or session protections.
* Quarkus: deny by default with `quarkus.security.jaxrs.deny-unannotated-endpoints=true` (or `default-roles-allowed`), path rules via `quarkus.http.auth.permission.<name>.paths` and `.policy`. Prefer the current LTS stream for long-lived services. Native images: test reflection-based serialization and security annotations in native mode, not only on the JVM.
