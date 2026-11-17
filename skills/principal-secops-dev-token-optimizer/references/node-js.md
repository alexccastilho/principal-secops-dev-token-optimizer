# Node.js and JavaScript (current ECMAScript) — OpenJS / MDN standards

Version policy: follow `versoes-e-fontes.md`. Read `engines` or `.nvmrc`, look up the release schedule at nodejs.org/en/about/previous-releases, and run an LTS line in production (Active LTS preferred, Maintenance LTS acceptable while it lasts), never a Current release. LTS lines change on a fixed calendar, so no number is written here. An end-of-life line is a finding. Check the browser support of a language feature on MDN or caniuse.com before using it in front-end code.

## Language rules (front and back)
* `const` by default, `let` when reassigned, `var` never. ES modules (`"type": "module"`).
* `async/await` only. Every await wrapped in try/catch at the boundary. After `fetch()`, check `if (!response.ok)` before reading the body.
* Optional chaining `?.` and nullish coalescing `??` instead of manual checks. Destructuring for clarity.
* No inline handlers (`onclick=""`). `addEventListener` with cached selectors, event delegation for lists.
* Built-ins in current LTS lines that remove dependencies (confirm in the Node docs for the version in use): `node:test` for tests, `fetch` global, `--watch`, `node --run`, `structuredClone`, `AbortSignal.timeout`.

## Node.js backend
* LTS version pinned in `package.json` `engines`. Lockfile committed. Deploy with `npm ci`, never `npm install`.
* Secrets from `process.env` (`--env-file=.env` in dev, no dotenv dependency needed). Validate presence at startup and fail fast with a clear message.
* Express or the framework in use: `helmet` for headers, rate limiting on auth and reset routes, body size limits, centralized error middleware with a generic message out and the full error to the log.
* Validate all input at the route boundary with a schema (zod) before any logic. Reject, do not coerce.
* Never block the event loop: no sync fs or crypto calls in handlers, heavy CPU goes to worker threads.
* Streams for large files instead of buffering whole payloads.
* Graceful shutdown on `SIGTERM`: stop accepting, finish in-flight, close the pool.

## TypeScript
* `"strict": true` in `tsconfig.json` (plus `noUncheckedIndexedAccess` for new code). No `any` without a comment saying why; prefer `unknown` and narrow it.
* ESLint with `typescript-eslint` recommended rules; Prettier or the project formatter for style. Type-check in CI with `tsc --noEmit`.
* Types are erased at runtime: validate every external input (request body, environment, JSON file) with a schema (zod) and infer the type from it, do not just cast with `as`.

## Security
* JWT: short expiry with rotation, stored in an `HttpOnly` cookie rather than localStorage. Verify signature and algorithm explicitly. Reject `alg: none`.
* Sessions over JWT for a plain server-rendered app. Simpler and revocable.
* Path handling: `path.join` plus validation against traversal (`..`). Never concatenate user input into a path.
* No `child_process.exec` with user data. Use `execFile` with an argument array.
* Prototype pollution: never merge untrusted JSON into an object with a recursive merge. Reject `__proto__`, `constructor`, `prototype` keys at the schema level.
* Regex from user input, or a complex regex over user input, can hang the process. Bound the input length.
* Next.js and other full-stack frameworks: every Server Action, Route Handler and API route checks the session and ownership itself; hiding the button or protecting the page is not access control. Only variables meant to be public get the `NEXT_PUBLIC_` (or `VITE_`) prefix, because the prefix ships the value to every browser. Keep the framework patched: its security releases are often critical.

## Supply chain
* `npm audit` on every dependency change. `npm ci` in deploy so the lockfile is authoritative.
* Check the package before installing: recent release, real repository, dependents count, name spelled exactly right.
* Install scripts run arbitrary code. For an unfamiliar package, `npm install --ignore-scripts` and inspect first. `npm audit signatures` verifies the registry signatures and provenance of what is installed.
* Keep the dependency count low. Every package is a maintainer you are trusting with production.

## Exceptional conditions
* `process.on('unhandledRejection')` and `'uncaughtException'`: log, then exit and let the process manager restart. Never swallow and continue with corrupted state.
* External calls (payment, e-mail, third-party API) get a timeout, a bounded retry with backoff, and a defined behavior on final failure.
* An error inside an auth check denies access. Never fall through to allow.

## Performance
* Reuse connections: DB pool (`mysql2/promise`), keep-alive HTTP agents.
* `Promise.all` for independent async work instead of sequential awaits.
* Cache hot reads (in-memory `Map` with TTL for one process, Redis when there are several), invalidated on write.
* Production: `NODE_ENV=production`, process manager (pm2 or systemd), log rotation, memory limit set.
