# Node.js, TypeScript, Deno and Bun: OpenJS, MDN and TC39 standards

Version policy: follow `versoes-e-fontes.md`. Read `engines`, `.nvmrc`, `.node-version`, `packageManager`, the `typescript` devDependency and the Docker base image, then check nodejs.org/en/about/previous-releases (or endoflife.date/api/nodejs.json). Production runs an LTS line (Active LTS preferred, Maintenance acceptable while it lasts), never a Current or odd-numbered line. An end-of-life line is a finding. Notes marked "(24+)" refer to the Node major; "(TS 5.8+)" to TypeScript. Deno: endoflife.date/api/deno.json. Bun: bun.com release notes. Browser features: check Baseline on MDN before using them in front-end code.

## Contents
- Standards and style
- TypeScript
- Security
- Exceptional conditions
- Supply chain
- Tuning
- Traps and fixes
- Legacy code: safe maintenance and staged migration
- Frameworks: Express, Fastify, NestJS, Next.js
- Deno and Bun

## Standards and style
* `const` by default, `let` when reassigned, never `var`. ES modules (`"type": "module"`), `node:` prefix for built-ins.
* `async/await`; check `response.ok` after `fetch()` before reading the body.
* `?.` and `??` instead of manual checks. No inline handlers (`onclick=""`) in front-end code.
* Lint: ESLint flat config (`eslint.config.js`) with `typescript-eslint`; Biome is an acceptable single tool if the project already uses it. Format with Prettier or the project formatter.
* Built-ins that remove dependencies (confirm in the docs of the Node line in use): `node:test`, global `fetch`, `--watch`, `node --run <script>`, `--env-file`, `structuredClone`, `AbortSignal.timeout`. (24+) global `URLPattern`. (26+) `Temporal` instead of date libraries.

## TypeScript
* `"strict": true` (default in TS 6.0+, set it explicitly anyway) plus `noUncheckedIndexedAccess`. No `any` without a comment; prefer `unknown` and narrow it.
* Type-check in CI with `tsc --noEmit`. Types vanish at runtime: validate every external input (request body, env, JSON file) with a schema (zod, valibot, or the framework's validator) and infer the type from it. Never just cast with `as`.
* Node runs `.ts` files by stripping types (on by default in 22.18+ and 23.6+, stable in 24.12+). It does NOT type-check, and it rejects `enum`, runtime `namespace`, constructor parameter properties, `import =` and `tsconfig` `paths`. Code meant to run that way sets `erasableSyntaxOnly` (TS 5.8+) and `verbatimModuleSyntax`.
* TS 6.0 changed defaults (`types` defaults to `[]`, add `"types": ["node"]`) deprecated `target: es5`, `baseUrl` and `moduleResolution: node`, and removed `outFile`. TS 7.0 (native Go compiler, same `tsc` command) turns those into hard errors and has no programmatic API yet: typescript-eslint and Vue/Svelte/Astro tooling keep TS 6 side by side (`@typescript/typescript6`). Upgrade one major at a time.

## Security
* Validate every input at the route boundary with a schema (zod, valibot, JSON Schema, or the framework's validator) before any logic. Reject, do not coerce.
* Injection: SQL through parameterized queries or the ORM's bound parameters (Prisma `$queryRaw` tagged template, never `$queryRawUnsafe` with input). NoSQL: reject objects where a string is expected (`{ "$ne": null }` login bypass).
* Commands: never `child_process.exec` or `spawn(..., { shell: true })` with user data. `execFile`/`spawn` with an argument array.
* Paths: `path.resolve(base, input)` then check the result starts with `base + path.sep`. Never concatenate user input into a path.
* Prototype pollution: no recursive merge of untrusted JSON. Reject `__proto__`, `constructor`, `prototype` keys in the schema; `Object.create(null)` or `Map` for user-keyed data. `--disable-proto=delete` is a backstop.
* `eval`, `new Function`, `vm` with input: never. `vm` is not a sandbox.
* Secrets from `process.env` (`--env-file` in dev, no dotenv needed). Validate presence at startup and fail fast. Only intentionally public values get `NEXT_PUBLIC_` or `VITE_` prefixes, since those ship to every browser.
* Passwords: `argon2` or `bcrypt` packages, or `crypto.scrypt`; tokens from `crypto.randomBytes` or `crypto.randomUUID`, compared with `crypto.timingSafeEqual`. Never `Math.random` for anything secret.
* JWT: verify signature with an explicit `algorithms` allowlist, check `exp`, `iss`, `aud`; reject `alg: none`. Short expiry with rotation, stored in an `HttpOnly` cookie, not localStorage. For a plain server-rendered app, server sessions are simpler and revocable.
* Regex over user input: bound the input length; avoid nested quantifiers (ReDoS hangs the single event loop).
* SSRF: a user-supplied URL for `fetch` gets a host allowlist, private and loopback ranges blocked, redirects re-checked.
* Permission model `--permission` with `--allow-fs-read`, `--allow-fs-write`, `--allow-net`, `--allow-child-process` (stable in 22.13+ and 23.5+): a seat belt for trusted code, not a sandbox against malicious code. Symlinks inside an allowed path escape it.

## Exceptional conditions
* `process.on('unhandledRejection')` and `'uncaughtException'`: log, then exit and let the process manager restart. Never continue with corrupted state.
* External calls get a timeout (`AbortSignal.timeout(ms)`), a bounded retry with backoff, and a defined final failure.
* An error inside an auth check denies. Never fall through to allow.
* Centralized error handler: generic message and correlation id to the client, stack to the log. Never send `err.stack` or `err.message` from the database to the browser.
* Graceful shutdown on `SIGTERM`: stop accepting, finish in-flight, close pools.

## Supply chain
* Lockfile committed; deploy with `npm ci` (or `pnpm install --frozen-lockfile`, `bun install --frozen-lockfile`). Never `npm install` on the server.
* `npm audit` (with `--audit-level=high` in CI) on every dependency change; `npm audit signatures` verifies registry signatures and provenance.
* Install scripts run arbitrary code. npm 12+ blocks unreviewed dependency install scripts with a warning: approve only what needs a build with `npm approve-scripts` (kept in `allowScripts`), and set `strict-allow-scripts=true` in CI. Older npm: `--ignore-scripts` for unfamiliar packages.
* Cooldown against freshly published malicious versions: npm `min-release-age=<days>` (11.10+), pnpm `minimumReleaseAge` (minutes, default one day in current pnpm), Bun and Deno per their docs. Exempt only a package that needs an urgent security fix.
* npm 12+ defaults `allow-git=none`; on older npm set `allow-git=none` or `root` so a transitive dependency cannot pull code from a Git URL. pnpm: `blockExoticSubdeps` (default on), build scripts only via `allowBuilds`.
* Check the package before installing: exact spelling, real repository, recent releases, dependents. Fewer packages, fewer maintainers trusted with production.

## Tuning
* Never block the event loop: no `*Sync` fs or crypto in request handlers; CPU-heavy work to `worker_threads`.
* Reuse connections: DB pool, keep-alive agents (undici is the built-in `fetch` client).
* `Promise.all` for independent work; streams for large files.
* Cache hot reads (in-memory `Map` with TTL for one process, Redis for several), invalidated on write.
* `NODE_ENV=production`, process manager (systemd, pm2 or the container orchestrator), log rotation, `--max-old-space-size` sized to the container.

## Traps and fixes
* Missing `await` on a promise in a try block: the rejection escapes the catch. Enable `@typescript-eslint/no-floating-promises`.
* `req.body.id` trusted for ownership: check the record belongs to the session user (IDOR).
* `res.redirect(req.query.next)`: open redirect. Allow only relative paths starting with a single `/`.
* `JSON.parse` on unbounded bodies: set body size limits in the framework.
* `cors({ origin: true, credentials: true })` reflects any origin with cookies: list exact origins.
* `url.parse()` is deprecated (24+) and parses differently from browsers: use `new URL()`.
* `jwt.decode()` used for auth: it does not verify. Use the verify function.
* Hiding a button or protecting only the page in a full-stack framework: every Server Action, Route Handler and API route checks session and ownership itself.

## Legacy code: safe maintenance and staged migration
* CommonJS, callbacks, an end-of-life Node line: fix the reported fault first; never a rewrite.
* Stages: 1) pin the current Node in `engines` and `.nvmrc`, commit the lockfile, run `npm audit`; 2) move one LTS line at a time on a staging copy, reading the release notes' semver-major changes; 3) replace deprecated APIs (`url.parse`, `new Buffer`) file by file; 4) add TypeScript with `allowJs` and `checkJs` before renaming files; 5) only then switch to ES modules.
* Express 4 to 5: read the migration guide; route syntax and `req.body` defaults change.

## Frameworks: Express, Fastify, NestJS, Next.js
* Express 5: rejected promises in async handlers reach the error middleware (no manual `.catch(next)`); `req.body` is `undefined` without a parser; wildcards must be named (`/*splat`); no regex characters in paths; `req.query` uses the simple parser. Add `helmet`, rate limiting on auth and reset routes, body size limits, a final error middleware.
* Fastify: declare a JSON Schema for `body`, `querystring`, `params` and `headers` in each route's `schema`, plus a response schema so extra fields are not leaked. Official plugins: `@fastify/helmet`, `@fastify/rate-limit`, `@fastify/csrf-protection`, `@fastify/cookie`, `@fastify/cors`.
* NestJS: global `app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }))`; guards on every controller (deny by default with a global guard plus a `@Public()` marker); never return entities directly.
* Next.js and React Server Components: Server Actions are public HTTP endpoints, so validate input and check auth inside each one. Next.js 16 renames `middleware.ts` to `proxy.ts`; proxy and middleware are not the only access check. Keep React and the framework patched: CVE-2025-55182 was an unauthenticated remote code execution in React Server Components (fixed in React 19.0.1, 19.1.2, 19.2.1 and patched framework releases).

## Deno and Bun
* Deno: deny by default. Grant narrow flags (`--allow-net=api.example.com`, `--allow-read=./data`, `--allow-env=API_KEY`); `--deny-*` overrides. Treat `--allow-run`, `--allow-ffi` and `-A` as full access. `deno audit` for dependencies; commit `deno.lock`.
* Bun: dependency lifecycle scripts run only for packages in `trustedDependencies` (or Bun's default list); keep that list short. Commit `bun.lock`. Bun aims at Node compatibility, but test every Node API the app uses before switching runtimes.
