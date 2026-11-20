# Research log: web (php.md, node-js.md, python.md, java.md, frontend.md)

Writer: web. Date of all checks: 2026-11-20. Lifecycle dates are recorded here only; the reference files keep only feature gates and framework minimums.

## Verified facts

### PHP, WordPress, Laravel, Symfony, Composer
- PHP: supported branches 8.2 (security only, to 2026-12-31), 8.3 (security only, to 2027-12-31), 8.4 (active to 2026-12-31), 8.5 (active to 2027-12-31), 8.6 (released 2026-11-19, active to 2028-12-31); 8.0 and 8.1 end of life (https://www.php.net/supported-versions.php, checked 2026-11-20)
- PHP: same cycles and dates in endoflife.date (https://endoflife.date/api/php.json, checked 2026-11-20)
- PHP 8.4: property hooks, asymmetric visibility `public private(set)`, `array_find()`, `array_find_key()`, `array_any()`, `array_all()`, `new` without parentheses, `#[\Deprecated]`, lazy objects, `Dom\HTMLDocument` HTML5 parser; implicitly nullable parameter types deprecated; IMAP, OCI8, PDO_OCI, pspell moved to PECL (https://www.php.net/releases/8.4/en.php, checked 2026-11-20)
- PHP 8.5: pipe operator `|>`, `clone($obj, [...])` (clone with), `#[\NoDiscard]` with `(void)` cast, always-available URI extension (`Uri\Rfc3986\Uri`, WHATWG URL), `array_first()`, `array_last()`, closures and first-class callables in constant expressions, `#[\Override]` on properties, fatal errors include a backtrace, `setcookie()` `partitioned` key, `get_error_handler()`, `get_exception_handler()` (https://www.php.net/releases/8.5/en.php, checked 2026-11-20)
- PHP 8.5: backtick operator as alias of `shell_exec()` deprecated; `__sleep()`/`__wakeup()` soft-deprecated in favor of `__serialize()`/`__unserialize()`; `disable_classes` INI removed; non-canonical casts `(boolean)`, `(integer)`, `(double)`, `(binary)` deprecated (https://www.php.net/releases/8.5/en.php, checked 2026-11-20)
- PHP 8.6: partial function application with `?` and `...` placeholders, `clamp()`, `\Time\Duration`, `Io\Poll`, stream exceptions (`StreamException`), `SortDirection` enum, readonly property defaults, `mysqli::quote_string()`, Sodium ML-KEM-768 and X-Wing (https://www.php.net/releases/8.6/en.php, checked 2026-11-20)
- PHP 8.6: secure session defaults: `session.use_strict_mode` and `session.cookie_httponly` enabled, `session.cookie_samesite` defaults to `Lax`; `return` inside `finally` deprecated; mbstring regex functions (`mb_ereg()`, `mb_split()`) deprecated; many functions throw `ValueError` on NUL bytes or out-of-range values; `fclose()`, `file_put_contents()`, `copy()` return false when flush or close fails (https://www.php.net/releases/8.6/en.php, checked 2026-11-20)
- PHP-FIG: PER Coding Style 3.1 "extends, expands and replaces" PSR-12 (https://www.php-fig.org/per/coding-style/, checked 2026-11-20)
- Composer: `composer audit` options `--no-dev`, `--locked`, `--abandoned`, `--format`, `--ignore-severity` (https://getcomposer.org/doc/03-cli.md#audit, checked 2026-11-20)
- Composer 2.9: blocks updates to versions with security advisories by default (`audit.block-insecure`) (https://blog.packagist.com/composer-2-9/, checked 2026-11-20)
- Composer: current config uses `policy.advisories.block` (default true; `audit.block-insecure` deprecated alias), `policy.abandoned` (`audit` default `fail` since 2.7), `policy.cooldown` (`period` default null, so off); bypass with `--no-blocking` (https://getcomposer.org/doc/06-config.md, checked 2026-11-20)
- Composer: 2.11.0 released 2026-10-29 (https://getcomposer.org/changelog/2.11.0, checked 2026-11-20)
- Psalm: taint analysis, flag `--taint-analysis` (https://psalm.dev/docs/security_analysis/, checked 2026-11-20)
- WordPress: `$wpdb->prepare()` placeholders `%d`, `%f`, `%s`, `%i`; `%i` added in 6.2.0 (https://developer.wordpress.org/reference/classes/wpdb/prepare/, checked 2026-11-20)
- WordPress: minimum PHP 7.4 since WordPress 7.0, PHP 8.4+ recommended (https://make.wordpress.org/hosting/handbook/server-environment/, checked 2026-11-20)
- WordPress: cycles 7.1 (2026-08-19) current, 7.0, 6.9 (https://endoflife.date/api/wordpress.json, checked 2026-11-20)
- WordPress: Plugin Check (PCP) by WordPress.org, `wp plugin check` WP-CLI command, includes security best-practice checks (https://wordpress.org/plugins/plugin-check/, checked 2026-11-20)
- WordPress: WordPress Coding Standards is a PHP_CodeSniffer ruleset, install `wp-coding-standards/wpcs:"^3.0"` (https://github.com/WordPress/WordPress-Coding-Standards, checked 2026-11-20)
- Laravel 13: requires PHP 8.3 minimum (supports 8.3 to 8.5); bug fixes 18 months, security 2 years; CSRF middleware formalized as `PreventRequestForgery` with origin-aware verification; `#[Middleware]` and `#[Authorize]` controller attributes (https://laravel.com/docs/13.x/releases, checked 2026-11-20)
- Laravel: 13 (2026-03-17), 12 security to 2027-02-24, 11 end of life 2026-03-12 (https://endoflife.date/api/laravel.json, checked 2026-11-20)
- Symfony 8.0: minimum PHP 8.4.0, unmaintained since July 2026 (https://symfony.com/releases/8.0, checked 2026-11-20)
- Symfony 7.4 LTS: minimum PHP 8.2.0, bug fixes to November 2028, security to November 2029 (https://symfony.com/releases/7.4, checked 2026-11-20)

### Node.js, TypeScript, Deno, Bun, frameworks
- Node.js: 26 Active LTS since 2026-10-28; 24 Maintenance LTS (active ended 2026-10-20, EOL 2028-04-30); 22 Maintenance, EOL 2027-04-30; 20 EOL 2026-04-30; 25 EOL (https://endoflife.date/api/nodejs.json, checked 2026-11-20)
- Node.js: permission model is Stability 2 (stable since 23.5.0 and 22.13.0), flag `--permission`, allow flags `--allow-fs-read`, `--allow-fs-write`, `--allow-child-process`, `--allow-worker`, `--allow-net`, `--allow-addons`, `--allow-wasi`; `--permission-audit`; doc says it is a "seat belt", not a security boundary against malicious code; symlinks are followed outside granted paths (https://nodejs.org/api/permissions.html, checked 2026-11-20)
- Node.js: type stripping enabled by default in 23.6.0 and 22.18.0, stable in 25.2.0 and 24.12.0; does no type checking; unsupported: `enum`, `namespace` with runtime code, parameter properties, import aliases, decorators, `tsconfig` `paths`; `--experimental-transform-types` removed in 26.0.0 (https://nodejs.org/api/typescript.html, checked 2026-11-20)
- Node.js 24.0.0: `URLPattern` global, permission flag renamed from `--experimental-permission` to `--permission`, npm 11, `url.parse()` runtime-deprecated (https://nodejs.org/en/blog/release/v24.0.0, checked 2026-11-20)
- Node.js 26.0.0: Temporal enabled by default, Undici 8, `--experimental-transform-types` removed, `module.register()` runtime-deprecated (https://nodejs.org/en/blog/release/v26.0.0, checked 2026-11-20)
- Node.js: CLI flags `--run`, `--env-file`, `--env-file-if-exists`, `--watch`, `--disable-proto` documented in v26 CLI (https://nodejs.org/api/cli.html, checked 2026-11-20)
- npm 11: `min-release-age` added in 11.10.0 (2026-02-11); `--allow-git` added in 11.9.0; `allowScripts` install-script policy phase 1 in 11.16.0 (https://docs.npmjs.com/cli/v11/using-npm/changelog, checked 2026-11-20)
- npm 12 (docs 12.2.3 "Latest"): `allow-git` default `none`; `min-release-age` default null; `ignore-scripts` default false; unreviewed dependency install scripts are blocked with a warning unless listed in `allow-scripts`; `strict-allow-scripts` makes that an error; `npm approve-scripts` (https://docs.npmjs.com/cli/v12/using-npm/config, checked 2026-11-20)
- npm: `audit-level`, `include-attestations` for `npm audit signatures` (https://docs.npmjs.com/cli/v11/using-npm/config, checked 2026-11-20)
- pnpm: dependency build scripts blocked until approved via `allowBuilds`; `strictDepBuilds` default true; v11 replaced `onlyBuiltDependencies` with `allowBuilds` (https://pnpm.io/settings/build, checked 2026-11-20)
- pnpm: `minimumReleaseAge` in minutes, default 1440; `trustPolicy` `no-downgrade` or `off` (default off); `blockExoticSubdeps` default true (https://pnpm.io/settings/dependency-resolution, checked 2026-11-20)
- Bun: does not run dependency lifecycle scripts by default except a curated list; `trustedDependencies` in package.json replaces that list (https://bun.com/docs/pm/lifecycle, checked 2026-11-20)
- Bun: single cycle 1.x (https://endoflife.date/api/bun.json, checked 2026-11-20)
- Deno: secure by default; `--allow-read`, `--allow-net`, `--allow-env`, `--allow-run`, `-A`; `--deny-*` overrides; treat `--allow-run` and `--allow-ffi` as equal to `--allow-all`; `deno audit` exists (https://docs.deno.com/runtime/fundamentals/security/, checked 2026-11-20)
- TypeScript 6.0: `strict` default true, `module` default `esnext`, `types` default `[]`, `noUncheckedSideEffectImports` true; deprecates `target: es5`, `baseUrl`, `moduleResolution node`/`classic`, `outFile`; last JS-based compiler (https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/, checked 2026-11-20)
- TypeScript 7.0: released 2026-07-08, native port in Go, package `typescript`, binary `tsc`; options deprecated in 6.0 are hard errors; no programmatic API (expected in 7.1); typescript-eslint and Volar tools should run 6.0 side by side via `@typescript/typescript6` (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/, checked 2026-11-20)
- TypeScript 5.8: `--erasableSyntaxOnly` errors on enums, runtime namespaces, parameter properties, `import =`/`export =` (https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html, checked 2026-11-20)
- TypeScript: `noUncheckedIndexedAccess` exists (4.1) (https://www.typescriptlang.org/tsconfig/, checked 2026-11-20)
- Express 5: rejected promises in async handlers go to the error handler; wildcards must be named (`/*splat`); regex characters in paths unsupported; `req.query` default parser `simple`; `req.body` undefined when not parsed; `express.urlencoded` default `extended: false`; requires Node 18+ (https://expressjs.com/en/guide/migrating-5.html, checked 2026-11-20)
- Express: majors 5 and 4 both without EOL date in endoflife.date (https://endoflife.date/api/express.json, checked 2026-11-20)
- Next.js 16: `middleware.ts` renamed `proxy.ts` (codemod `middleware-to-proxy`), proxy runs on Node.js (https://nextjs.org/docs/messages/middleware-to-proxy, checked 2026-11-20)
- React: CVE-2025-55182, CVSS 10, unauthenticated RCE in React Server Components (`react-server-dom-*` 19.0, 19.1.0, 19.1.1, 19.2.0), fixed in 19.0.1, 19.1.2, 19.2.1 and patched framework releases (https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components, checked 2026-11-20)
- NestJS: `ValidationPipe` options `whitelist`, `forbidNonWhitelisted`, `transform`; global via `app.useGlobalPipes()` (https://docs.nestjs.com/techniques/validation, checked 2026-11-20)
- Fastify: official plugins `@fastify/helmet`, `@fastify/rate-limit`, `@fastify/csrf-protection`, `@fastify/cookie`, `@fastify/cors` (https://fastify.dev/ecosystem/, checked 2026-11-20)
- Fastify: route `schema` validates `body`, `querystring`, `params`, `headers`; response schema helps prevent accidental disclosure (https://fastify.dev/docs/latest/Reference/Validation-and-Serialization/, checked 2026-11-20)
- ESLint: docs list only flat config `eslint.config.*`; v10.x is current docs line (https://eslint.org/docs/latest/use/configure/configuration-files, checked 2026-11-20)

### Python, Django, FastAPI, Flask
- Python: 3.15 (2026-10-09) and 3.14 bugfix; 3.13 security since 2026-10-01; 3.12, 3.11 security only; 3.10 EOL 2026-10-01 (https://endoflife.date/api/python.json, checked 2026-11-20)
- Python 3.12: PEP 695 `type` statement and type parameter syntax, PEP 701 f-string grammar, PEP 698 `typing.override` (https://docs.python.org/3/whatsnew/3.12.html, checked 2026-11-20)
- Python 3.14: PEP 750 t-strings (`string.templatelib.Template`), PEP 649/749 deferred annotations (`annotationlib`), PEP 758 `except A, B:` without brackets, PEP 765 SyntaxWarning for return/break/continue leaving `finally`, PEP 779 free-threaded build officially supported, PEP 784 `compression.zstd`, PEP 734 `concurrent.interpreters`, PEP 768 `sys.remote_exec()` (disable with `PYTHON_DISABLE_REMOTE_DEBUG` or `-X disable-remote-debug`), `forkserver` default start method on Unix except macOS (https://docs.python.org/3.14/whatsnew/3.14.html, checked 2026-11-20)
- Python 3.14: tarfile default extraction filter is `data`; `filter` argument added in 3.12; pass `filter='data'` explicitly on older versions (https://docs.python.org/3/library/tarfile.html, checked 2026-11-20)
- Python 3.15: PEP 810 `lazy import`, PEP 814 `frozendict`, PEP 661 `sentinel`, PEP 686 UTF-8 default encoding, PEP 799 `profiling` package (`profiling.sampling`), PEP 829 `.start` files and deprecation of `import` lines in `.pth` (https://docs.python.org/3.15/whatsnew/3.15.html, checked 2026-11-20)
- pip: `pip lock` (PEP 751 pylock.toml) experimental since 25.1; `--uploaded-prior-to` since 26.0, accepts durations like `P3D` since 26.1 (https://pip.pypa.io/en/stable/news/, checked 2026-11-20)
- pip-audit: PyPA project, supports `pyproject.toml` and `pylock.*.toml`, `pip-audit --require-hashes -r requirements.txt` (https://pypi.org/project/pip-audit/, checked 2026-11-20)
- uv: `uv audit` command, `--exclude-newer` (`UV_EXCLUDE_NEWER`), `--require-hashes` for `uv pip` (https://docs.astral.sh/uv/reference/cli/, checked 2026-11-20)
- Ruff: linter and formatter; flake8-bandit `S` rules such as S608, S602, S105 (https://docs.astral.sh/ruff/rules/, checked 2026-11-20)
- Django: 6.1 (2026-08-05), 6.0, 5.2 LTS to 2028-04-30; 4.2 LTS EOL 2026-04-07 (https://endoflife.date/api/django.json, checked 2026-11-20)
- Django 6.0: built-in CSP: `django.middleware.csp.ContentSecurityPolicyMiddleware`, `SECURE_CSP`, `SECURE_CSP_REPORT_ONLY`, `csp()` context processor for nonces; `django.tasks` framework (no worker bundled); template partials; supports Python 3.12 to 3.14; `DEFAULT_AUTO_FIELD` defaults to `BigAutoField`; PBKDF2 iterations 1,200,000; `URLField` assumes https (https://docs.djangoproject.com/en/6.0/releases/6.0/, checked 2026-11-20)
- FastAPI: tutorial uses `pwdlib[argon2]` (`PasswordHash.recommended()`) and PyJWT (https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/, checked 2026-11-20)
- FastAPI: docs have a "Strict Content-Type Checking" page; latest release 0.165.0 on 2026-11-18 (https://fastapi.tiangolo.com/release-notes/, checked 2026-11-20)
- Flask 3.1 docs: Jinja autoescape on; no built-in CSRF; `MAX_CONTENT_LENGTH` unset by default, `MAX_FORM_MEMORY_SIZE` 500 kB, `MAX_FORM_PARTS` 1000; `TRUSTED_HOSTS`; `SESSION_COOKIE_SECURE`/`HTTPONLY`/`SAMESITE`; unquoted attributes and `javascript:` hrefs are not covered by escaping (https://flask.palletsprojects.com/en/stable/web-security/, checked 2026-11-20)

### Java, Spring, Jakarta EE, Quarkus
- Java: Oracle JDK 25 LTS (2025-09-16), 21 LTS; 26 and 27 non-LTS (27 released 2026-09-15) (https://endoflife.date/api/oracle-jdk.json, checked 2026-11-20)
- Java: Eclipse Temurin 25 LTS to 2031-09-30, 21 LTS to 2029-12-31 (https://endoflife.date/api/eclipse-temurin.json, checked 2026-11-20)
- JDK 21: virtual threads (444), record patterns (440), pattern matching for switch (441), sequenced collections (431), structured concurrency preview (453) (https://openjdk.org/projects/jdk/21/, checked 2026-11-20)
- JDK 24: JEP 486 permanently disable the Security Manager, JEP 491 synchronize virtual threads without pinning, JEP 496 ML-KEM, JEP 497 ML-DSA, JEP 485 stream gatherers, JEP 472 prepare to restrict JNI (https://openjdk.org/projects/jdk/24/, checked 2026-11-20)
- JDK 25: final: 506 scoped values, 510 key derivation function API, 511 module import declarations, 512 compact source files and instance main methods, 513 flexible constructor bodies, 519 compact object headers; preview: 470 PEM encodings, 505 structured concurrency (fifth preview), 502 stable values (https://openjdk.org/projects/jdk/25/, checked 2026-11-20)
- JDK 26: 500 prepare to make final mean final, 504 remove applet API, 517 HTTP/3 for HTTP Client; structured concurrency sixth preview (https://openjdk.org/projects/jdk/26/, checked 2026-11-20)
- JDK 27: 527 post-quantum hybrid key exchange for TLS 1.3, 523 G1 default in all environments, structured concurrency seventh preview, PEM encodings third preview (https://openjdk.org/projects/jdk/27/, checked 2026-11-20)
- Spring Boot 4.0: Spring Framework 7 and Spring Security 7 baselines, Jackson 3 (Jackson 2 deprecated), Servlet 6.1, Persistence 3.2, Validation 3.1, Tomcat 11, Jetty 12.1 (https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes, checked 2026-11-20)
- Spring Boot 4.2.0 docs: requires Java 17+, compatible up to Java 27 (https://docs.spring.io/spring-boot/system-requirements.html, checked 2026-11-20)
- Spring Boot actuator: only `health` exposed over HTTP by default; `management.endpoints.web.exposure.include`; `env`/`configprops` values sanitized by default (`show-values`); custom `SecurityFilterChain` turns off actuator auto-security (https://docs.spring.io/spring-boot/reference/actuator/endpoints.html, checked 2026-11-20)
- Spring Security 7: Lambda DSL required, `.and()` chaining invalid, `apply()` replaced by `with()` (https://docs.spring.io/spring-security/reference/6.5/migration-7/configuration.html, checked 2026-11-20)
- Spring Security 7 migration: Jackson 3 `SecurityJacksonModules` with a `PolymorphicTypeValidator` (https://docs.spring.io/spring-security/reference/migration/index.html, checked 2026-11-20)
- Quarkus: `quarkus.security.jaxrs.deny-unannotated-endpoints` (default false), `quarkus.security.jaxrs.default-roles-allowed`, `quarkus.http.auth.permission.<name>.paths`/`.policy` (https://quarkus.io/guides/security-authorize-web-endpoints-reference, checked 2026-11-20)
- Quarkus: 3.40 LTS released 2026-09-30 (https://endoflife.date/api/quarkus-framework.json, checked 2026-11-20)
- Jakarta EE: Platform 11 released, Platform 12 under development (https://jakarta.ee/specifications/platform/, checked 2026-11-20)
- OWASP Dependency-Check: NVD API key "highly encouraged", without it updates are extremely slow; mandatory upgrade to 12.1.0+; Maven `failBuildOnCVSS` (https://github.com/dependency-check/DependencyCheck, https://jeremylong.github.io/DependencyCheck/dependency-check-maven/index.html, checked 2026-11-20)
- Find Security Bugs: SpotBugs plugin for Java web security audits (https://find-sec-bugs.github.io/, checked 2026-11-20)

### Frontend, accessibility, CSP, WebAssembly
- WCAG 2.2 is the current Recommendation (2023-10-05, updated 2024-12-12), ISO/IEC 40500:2025; WCAG 3.0 is an early draft (https://www.w3.org/WAI/standards-guidelines/wcag/, checked 2026-11-20)
- EU European Accessibility Act (Directive (EU) 2019/882) applies from 2025-06-28 (https://eur-lex.europa.eu/eli/dir/2019/882/oj/eng, checked 2026-11-20)
- Trusted Types: Baseline 2026 newly available (since February 2026); CSP `require-trusted-types-for 'script'` and `trusted-types <policy>` (https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API, checked 2026-11-20)
- `Element.setHTML()`: limited availability (not Baseline); default sanitizer removes script, iframe, event handlers; do not reinsert its output via `innerHTML` (https://developer.mozilla.org/en-US/docs/Web/API/Element/setHTML, checked 2026-11-20)
- CSP: strict policy `script-src 'nonce-{RANDOM}' 'strict-dynamic'; object-src 'none'; base-uri 'none'`, `frame-ancestors`, `upgrade-insecure-requests` (does not replace HSTS), `report-to` with `Reporting-Endpoints`, `report-uri` deprecated, `Content-Security-Policy-Report-Only` cannot be delivered via meta (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP, checked 2026-11-20)
- CSP: `'wasm-unsafe-eval'` allows WebAssembly compilation without allowing JS eval; `'unsafe-hashes'` (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src, checked 2026-11-20)
- HTML: `target="_blank"` implies `rel="noopener"` in modern browsers; add `noreferrer` to drop the Referer (https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a, checked 2026-11-20)
- WebAssembly 3.0 completed 2025-09-17: memory64, multiple memories, GC, typed references, tail calls, exception handling, relaxed SIMD, JS string builtins (https://webassembly.org/news/2025-09-17-wasm-3.0/, checked 2026-11-20)
- Core Web Vitals: LCP <= 2.5 s, INP <= 200 ms, CLS <= 0.1 at the 75th percentile (https://web.dev/articles/vitals, checked 2026-11-20)

### Added during writing
- PHP 8.0: default PDO error mode changed from silent to exceptions (https://www.php.net/manual/en/migration80.incompatible.php, checked 2026-11-20)
- Symfony: `symfony check:security` exists; docs recommend `composer audit` in CI because it reports more advisories (https://symfony.com/doc/current/setup.html, checked 2026-11-20)
- Rector: automated PHP upgrades, PHP 5.3 to 8.5 (https://getrector.com/, checked 2026-11-20)
- Node.js: `--disable-proto` modes `delete` and `throw`; `--max-old-space-size` (https://nodejs.org/api/cli.html, checked 2026-11-20)
- Prisma: `$queryRawUnsafe`/`$executeRawUnsafe` carry significant SQL injection risk; `$queryRaw` tagged template uses prepared statements (https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries, checked 2026-11-20)
- Bun: lockfile `bun.lock` (text since 1.2), `bun install --frozen-lockfile` (https://bun.com/docs/pm/cli/install, checked 2026-11-20)
- Spring Boot 4.0 migration: upgrade to the latest 3.5.x first (https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide, checked 2026-11-20)
- Spring Boot properties: `spring.web.error.include-stacktrace` default `never`; `spring.jpa.open-in-view` default `true` (https://docs.spring.io/spring-boot/appendix/application-properties/index.html, checked 2026-11-20)
- Spring Security: `PasswordEncoderFactories.createDelegatingPasswordEncoder()`, `Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8()` needs BouncyCastle (https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html, checked 2026-11-20)

- Symfony 8.1: requires PHP 8.4.0 or higher (https://symfony.com/releases/8.1, checked 2026-11-20)
- PHP: class `Uri\WhatWg\Url` documented in the manual (https://www.php.net/manual/en/class.uri-whatwg-url.php, checked 2026-11-20)
- Java: Oracle JDK LTS cycles 25, 21, 17, 11, 8 (https://endoflife.date/api/oracle-jdk.json, checked 2026-11-20)

## Changed from the previous text
- All five titles: removed em dashes; frontend.md got a version policy paragraph.
- php.md: PSR-12 replaced by PER Coding Style; pipe operator gated (8.5+); added PHP 8.5 and 8.6 gates (`#[\NoDiscard]`, URI extension, `clamp()`, partial application, secure session defaults in 8.6); backtick shell alias deprecated; `__sleep`/`__wakeup` soft-deprecated; Composer advisory blocking and `policy.cooldown`; Psalm taint analysis, PHPStan; Laravel and Symfony sections added; WordPress Plugin Check and WPCS; traps and legacy migration sections; removed em dash in the Composer sample line.
- node-js.md: permission model described as seat belt, not sandbox; type stripping (no type-check, erasable syntax); TypeScript 6 defaults and TypeScript 7 (no API, typescript-eslint on 6.0); npm 12 script policy, `allow-git`, `min-release-age`; pnpm `allowBuilds`, `minimumReleaseAge`; Bun `trustedDependencies`; Deno permissions; Express 5 changes; Fastify and NestJS bullets; Next.js `proxy.ts` and React Server Components CVE-2025-55182 lesson; traps and legacy sections.
- python.md: GIL line updated for free-threaded builds; tarfile `filter='data'`; 3.14 and 3.15 gates; pip `--uploaded-prior-to`, `pip lock`, uv audit; Ruff S rules; Django 6.0 CSP; FastAPI pwdlib and PyJWT; Flask limits and `TRUSTED_HOSTS`; remote debugging control; traps and legacy (Python 2) sections.
- java.md: Java 21/24/25 gates (JEP 491 pinning fix, Security Manager gone, scoped values, KDF API, ML-KEM/ML-DSA); structured concurrency still preview; Spring Boot 4 and Jackson 3; Spring Security 7 lambda DSL; actuator defaults; Quarkus deny-unannotated; Jakarta namespace migration; Dependency-Check NVD key; Find Security Bugs; traps and legacy sections.
- frontend.md: version policy; Trusted Types Baseline; `setHTML()` limited availability; strict CSP recipe with reporting; `rel=noopener` implied; WCAG 2.2 is ISO/IEC 40500:2025 and EAA; WebAssembly security notes; traps section.

## Not verified
- Spring Boot newest line: endoflife.date lists 4.1 as newest, docs.spring.io shows 4.2.0 as current. Discrepancy; no newest line written.
- Spring Security 7 removal of `authorizeRequests()` in favor of `authorizeHttpRequests()`: not confirmed on the pages read; written only as "use `authorizeHttpRequests`".
- ESLint removal of `.eslintrc` support: not confirmed; written as "flat config".
- Composer version that introduced `policy.cooldown`: not confirmed on the 2.11.0 changelog; written without a version.
- Jakarta EE 11 minimum Java SE; `uv export` to pylock format; `bun audit` details and Bun release-age setting; FastAPI minimum Python and Pydantic v1 status; pnpm version that introduced `minimumReleaseAge`.
- npm release that first shipped the blocked-by-default install-script policy (documented "as of npm 12"); which Node line bundles npm 12.
- Jackson 3 default for `FAIL_ON_UNKNOWN_PROPERTIES`; kept as an explicit instruction, version-independent.
- PHP 8.4 bcrypt default cost change: not on the release page; not written.
- Fastify response-schema stripping behavior: docs only say it helps prevent disclosure; written that way.
- `server.error.include-stacktrace` as the older Spring Boot property name (only the current `spring.web.error.*` name was seen).
- Stable API and tool names written without a fetch today (long-standing, no version claim): typescript-eslint `no-floating-promises`, `pnpm install --frozen-lockfile`, `deno.lock`, `datetime.utcnow()` deprecation, `uv sync --locked`, Ruff `UP` rules, Flask-WTF `CSRFProtect`, FastAPI `docs_url=None` and `response_model` filtering, `django-csp`, `manage.py check --deploy`, `@EnableMethodSecurity`, OpenRewrite, OSV-Scanner, Gradle `verification-metadata.xml`, `-XX:MaxRAMPercentage`, `ObjectInputFilter`, DOMPurify, axe DevTools, Stylelint, `fetchpriority`, jQuery `$(html)` XSS history, Lei Brasileira de Inclusao scope (Lei 13.146/2015 art. 63), WCAG 2.2 criteria wording (focus not obscured, redundant entry).
- Framework API names written from long-standing documentation without a fetch today: Laravel `$fillable`/`$guarded`, `$request->validated()`, `DB::raw`/`whereRaw` bindings, Blade `{!! !!}`, `config:cache`; Symfony `secrets:set`, `access_control`, `#[IsGranted]`, Twig `|raw`, Doctrine `setParameter()`; PHP `PDO::ATTR_EMULATE_PREPARES`, `proc_open()` array command form (PHP 7.4+), `unserialize` `allowed_classes`; Spring `@Transactional` rollback only on unchecked exceptions by default; `jakarta.*` namespace from Jakarta EE 9 and Spring Boot 3.
- Carried-over, version-independent items kept from the old text (Django/DRF basics, Hikari default pool, G1 tuning advice, CSS layout advice) were not individually re-verified; they contain no version numbers.
