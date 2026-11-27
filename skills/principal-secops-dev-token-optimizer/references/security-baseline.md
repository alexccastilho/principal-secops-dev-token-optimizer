# Security baseline: OWASP Top 10:2025, ASVS 5.0, supply chain, LGPD

## Contents
- OWASP Top 10:2025 controls, category by category (supply chain is A03, authentication A07, logging A09, error handling A10)
- Version and vulnerability check (knowledge cutoff)
- Secrets handling
- Security headers and cookies
- File upload
- Payments
- LGPD (Brazilian personal data law)
- Features that call an LLM
- Incident or unpatched flaw (0-day)
- Deploy checklist
- After publishing
- Standards map
- Severity scale for audits

Target: the current OWASP ASVS, Level 1 for any public app, Level 2 when it handles money, health data or personal data at scale. The editions named in this file (OWASP Top 10:2025, ASVS 5.0.0) were checked as current on 2026-11-20; confirm the current edition with `versoes-e-fontes.md` before citing one in a formal document, and keep the control intent when the numbering changes.

## OWASP Top 10:2025 controls

**A01 Broken Access Control** (SSRF now lives here)
* Deny by default. Every protected route checks the session server-side, then checks that the logged user owns the specific record.
* Never trust an id, role, price or quantity that arrived from the client. Re-read them from the database.
* Object references: prefer opaque ids (UUID) over sequential ones, but never as the only defense.
* Outbound requests built from user input (SSRF): allowlist of hosts and schemes, no redirect following. Resolve the name once, check the resolved address, and connect to that same address, or a second DNS answer bypasses the check. Block loopback, private and link-local ranges in IPv4 and IPv6 (127.0.0.0/8, 10/8, 172.16/12, 192.168/16, 169.254.0.0/16 which holds the cloud metadata address, ::1, fc00::/7, fe80::/10).
* CORS: explicit origin list. Never `*` together with credentials.

**A02 Security Misconfiguration**
* Production: debug off, verbose errors off, directory listing off, default accounts removed, sample and admin panels removed or protected.
* Every environment (dev, staging, prod) hardened the same way, differing only in secrets.
* Cloud storage buckets private by default; check public access before deploy.
* Remove unused features, ports, services and framework modules.

**A03 Software Supply Chain Failures**
* Pin exact versions. Commit the lockfile. Install with the lockfile-respecting command (`npm ci`, `composer install`, `pip install -r requirements.txt --require-hashes`, `mvn -B`).
* Audit on every dependency change with the language's own auditor: `npm audit`, `composer audit`, `pip-audit`, `cargo audit`, `govulncheck ./...`, `bundle audit`, `dotnet list package --vulnerable`, and for Maven `mvn org.owasp:dependency-check-maven:check`.
* Language-neutral scanners that read the lockfile: `osv-scanner` (OSV database) and `trivy fs .` (also covers containers and IaC). Static analysis: `semgrep` or CodeQL. Automated update pull requests: Dependabot or Renovate.
* Prefer packages with recent releases, many dependents and a named maintainer. Watch for typosquats (one letter off from a popular name) and for dependency confusion (an internal package name that also exists on the public registry; pin the registry or scope).
* Abandoned package (no release in two years, archived repository, maintainer gone): treat it as a finding and propose a maintained replacement.
* Install-time scripts run arbitrary code in every ecosystem that has them (npm `postinstall`, Python `setup.py`, Composer scripts). Review before running on an unfamiliar package.
* Never install from a random gist, pastebin or unverified fork.
* Build and deploy scripts are code: review them, do not let them fetch and run remote scripts unpinned.
* For anything serious, generate an SBOM (CycloneDX or SPDX) and keep it with the release.

**A04 Cryptographic Failures**
* TLS everywhere, HSTS on, no mixed content.
* Passwords: Argon2id (memory ≥ 19 MiB, iterations ≥ 2, parallelism 1), or bcrypt with cost 12 by default (OWASP floor is 10; raise it while a login stays acceptably fast on the server). bcrypt reads only the first 72 bytes, so cap the accepted length there or use Argon2id. Where FIPS-140 is required: PBKDF2-HMAC-SHA256 with 600,000 iterations. Never MD5, SHA-1, SHA-256 alone, never homemade crypto.
* Data at rest: AES-256-GCM through the platform library. Keys from the environment or a KMS, rotated, never next to the ciphertext.
* Randomness for tokens from a cryptographic source (`random_bytes`, `secrets`, `crypto.randomBytes`, `SecureRandom`), never a plain RNG.
* Never log, cache or put in a URL: passwords, tokens, full card numbers, CPF.

**A05 Injection**
* SQL: parameterized statements only, in every language. Identifiers that must be dynamic (table, column, sort direction) come from an allowlist, never from input.
* Commands: argument arrays, never a shell string. No `shell=True`, no `exec()` with user data.
* XSS: escape on output, context-aware (HTML body, attribute, JS, URL). Use the template engine's auto-escaping, do not disable it. `innerHTML` only with sanitized content.
* LDAP, XPath, NoSQL, template engines and header values follow the same rule: structure from code, data as parameters.

**A06 Insecure Design**
* Before coding a sensitive flow (password reset, checkout, permissions), write down in pt-BR who may do what, then implement exactly that.
* Rate limit and lock out on authentication, password reset, coupon and OTP endpoints.
* Business limits enforced server-side: maximum quantity, minimum price, one vote per user, no negative values.
* Segregate tenants: a query without a tenant or owner filter is a bug.

**A07 Authentication Failures**
* Passwords (NIST SP 800-63B-4): minimum 15 characters when the password is the only factor, 8 when it is part of MFA; accept at least 64; no composition rules (no "one uppercase, one symbol"); no forced periodic rotation, only on evidence of compromise; check new passwords against a blocklist of common and breached ones and tell the user why one was refused.
* MFA available on anything with money or admin access.
* New session id after login and after privilege change. Invalidate on logout and on password change.
* Generic messages on login and on password recovery, so the form does not reveal which e-mails exist.
* Password reset tokens: single use, short expiry, random, invalidated after use.

**A08 Software or Data Integrity Failures**
* Never deserialize untrusted data with a native serializer (PHP `unserialize`, Java serialization, Python `pickle`). Use JSON with a schema.
* Verify integrity of anything downloaded at build time (hash or signature).
* Signed cookies and JWTs: verify the signature and the algorithm; reject `alg: none` and algorithm switching.
* Auto-update mechanisms verify a signature before applying.

**A09 Security Logging and Alerting Failures**
* Log with timestamp, source IP, user id, action, result: login success and failure, permission denied, admin action, payment, data export, schema change.
* Logs go to a file or service outside the webroot, rotated, readable only by the app user.
* Alert on patterns: repeated failures from one IP, first admin login from a new country, mass export.
* Never log secrets or full personal data. Mask CPF, card and token.

**A10 Mishandling of Exceptional Conditions**
* Catch at the boundary, decide explicitly, deny on doubt. An exception must never leave a user authenticated, a payment approved or a permission granted.
* No empty catch blocks. No suppressed errors (`@` in PHP, bare `except:` in Python).
* External call failures (payment gateway, e-mail, API) have a defined behavior: retry with backoff, or fail closed with a clear message.
* Validate before use rather than relying on the exception, where the check is cheap.
* User sees a generic message and a support code. The log gets everything.

## Version and vulnerability check (knowledge cutoff)

What this model knows about vulnerabilities and "latest" versions stops at its training cutoff. A library recommended from memory may have had a critical flaw published since. Before recommending, adding or keeping a version of a language, framework or package:

1. **Run the auditor** of the language (A03 above) and, when available, `osv-scanner` or `trivy fs .`. Read the result; do not assume it is clean. When commands can run, also run this skill's `scripts/fontes.py deps <pasta>` on the lockfile: it checks the locked versions against OSV and flags the flaws on the CISA KEV list, and `fontes.py versao <tecnologia> --em-uso <versão>` says whether a branch still gets security fixes. Exit 3 means it could not check: say so, never guess (`versoes-e-fontes.md`).
2. **Consult current sources when the web is available:** osv.dev and the GitHub Advisory Database for the package, nvd.nist.gov for the CVE, and the CISA Known Exploited Vulnerabilities (KEV) catalog for anything already exploited in the wild. FIRST's EPSS score estimates how likely a CVE is to be exploited and helps order the work. The vendor's supported-versions page (php.net/supported-versions.php, devguide.python.org/versions, nodejs.org/en/about/previous-releases, endoflife.date) says whether a branch still gets security fixes.
3. **No web access:** say so in one line in pt-BR and hand the check to the user: "Conferi esta versão só até a data de corte do meu conhecimento. Antes de publicar, rode `composer audit` e me mande o resultado."
4. Never recommend a branch that is end of life. Never present a version as "the latest" without having checked it.

## Secrets handling

* `.env` at the project root, listed in `.gitignore`, never committed. Ship a `.env.example` with keys and empty values.
* Read them at startup and fail fast with a clear message if one is missing.
* If a secret was ever committed, it is burned: rotate it, do not just delete the line.
* Scan the whole git history, not only the working tree, before publishing a repository: `gitleaks detect` or `trufflehog git file://.`. Add a pre-commit secret scan so the next leak is caught before it is committed.
* Front-end code cannot hold secrets. Anything in the browser is public.

## Security headers and cookies

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
```
Cookies: `Secure; HttpOnly; SameSite=Strict` (use `Lax` only when a cross-site redirect flow requires it). Session cookie has no persistent expiry unless "lembrar de mim" is an explicit feature.

CSP with `unsafe-inline` is close to useless. Move inline scripts and styles to files, or use a per-request nonce.

## File upload

* Allowlist of extensions AND verified MIME type AND size limit.
* Random filename via a cryptographic source. Never keep the user's filename in the path.
* Store outside the webroot; serve through a script that checks permission and sets `Content-Disposition`.
* Never allow execution in the upload directory. Images: re-encode to strip embedded payloads.

## Payments

* Never receive, store or log the card number, CVV or expiry date. Use the gateway's hosted checkout or its tokenizing fields (Mercado Pago, Pagar.me, PagBank, Stripe). That keeps the system out of most of PCI DSS.
* A payment is confirmed only by the gateway's server-to-server notification (webhook) or by querying its API. Never by the return URL in the browser, a value sent by the client or a screenshot of a Pix receipt.
* Webhooks: verify the signature with the gateway secret, reject old timestamps, process each event id only once, answer quickly and do the work afterwards.
* Price, discount, freight and total are recomputed on the server from the database. The Pix amount and key in the QR code come from the server.

## LGPD (Lei 13.709/2018)

Applies to any system handling personal data of people in Brazil.

* Collect only what the feature needs. A field nobody uses is a liability.
* Record the legal basis for each purpose (consent, contract, legal obligation, legitimate interest). Consent must be specific, informed and revocable, never a pre-checked box.
* Support the data subject rights: access, correction, deletion, portability, and revoking consent. Design the deletion path before launch.
* Encrypt sensitive data at rest, restrict access by role, log who read what.
* Retention limit: define how long each dataset is kept, then actually delete it.
* The regulator is the ANPD, now Agência Nacional de Proteção de Dados (Lei 15.352/2026).
* Incident with risk or relevant damage to the subject: notify the ANPD and the affected people within **3 business days** of learning the incident affected personal data (Resolução CD/ANPD nº 15/2024, arts. 6 and 9; a complementary notice to the ANPD is allowed within 20 business days). Small processors (agentes de pequeno porte, Resolução CD/ANPD nº 2/2022) get these deadlines doubled, but only if they qualify: no high-risk processing and revenue within the legal limit (art. 3). Keep an incident record for at least 5 years (art. 10).
* Small processors may adopt a simplified information security policy and are not required to name an encarregado, but must offer a channel for data subjects (Resolução CD/ANPD nº 2/2022, arts. 11 and 13).
* Sending data abroad (a US-hosted API, an analytics provider) is international transfer. Note it in the privacy notice.

Explain this to the user in one plain pt-BR line when it applies, for example: "Como o formulário guarda CPF, ele precisa de um jeito de o cliente pedir exclusão dos dados. Já deixei o campo isolado numa tabela própria para isso ficar simples."

## Features that call an LLM

* Treat model output as untrusted input. Never `eval` it, never run it as SQL or shell without a whitelist.
* Content that came from a user, a webpage or a document can carry instructions to the model. Keep system instructions separate from data, and never grant the model a capability the current user does not already have.
* Cap tokens, rate limit per user, and log prompts without personal data.
* API keys stay server-side. A browser calling the provider directly leaks the key.
* An agent that calls tools or acts on its own (sends e-mail, runs code, moves money): least privilege per tool, human confirmation for irreversible actions. Map risks with the OWASP Top 10 for Agentic Applications.

## Incident or unpatched flaw (0-day)

Use when a flaw is announced with no fix yet, when a dependency in use shows up in the CISA KEV catalog, or when there are signs of intrusion (unknown admin user, changed files, strange outbound traffic, defaced page). The order matters:

1. **Isolate.** Put the site in maintenance mode or block the affected function. Change every password, token and key that the server could read. Say it first, in one line: "Antes de tudo, tire o site do ar pelo painel e troque a senha do banco."
2. **Mitigate.** Apply the temporary protection the advisory suggests (a WAF or `.htaccess` rule, disabling the module, restricting the route by IP). This is virtual patching: it buys time, it is not the fix.
3. **Preserve.** Copy the logs and the changed files before any cleanup. They are the evidence of what happened.
4. **Monitor.** Search the logs for the indicators of compromise the advisory published (paths, user agents, IPs, file hashes).
5. **Fix.** Update to the corrected version as soon as it exists, after a backup, and rerun the audit.
6. **Communicate.** If personal data was affected, the ANPD and the data subjects must be notified within 3 business days, 6 only for a qualifying small processor (see LGPD above). Record the incident: what, when, which data, what was done.

Never run a cleanup command copied from the internet on a compromised server without understanding it. When in doubt, restore from a backup taken before the intrusion and rotate every secret.

## Deploy checklist

```
- [ ] Debug and verbose errors off
- [ ] Secrets in environment variables, .env not committed
- [ ] HTTPS active and forced, HSTS on
- [ ] Security headers present
- [ ] Dedicated DB user, no root, least privilege
- [ ] Dependencies installed from lockfile, audit clean, versions checked against current sources
- [ ] Secret scan of the git history done
- [ ] Logs writing outside the webroot, rotation configured
- [ ] Backup of files and database taken and restore tested
- [ ] Admin and test accounts removed or with strong unique passwords
```

## After publishing

Security does not end at deploy. Keep this running:

* **Patch deadlines by severity** (recommended defaults, adjust to the business): CRITICAL or listed in KEV within 48 hours, HIGH within 7 days, MEDIUM within 30 days, LOW at the next regular update.
* **Re-audit** dependencies on a schedule (weekly is enough for most systems) and enable automatic security update pull requests.
* **Disclosure contact:** publish `/.well-known/security.txt` (RFC 9116) with a `Contact:` and an `Expires:` field, and a `SECURITY.md` in the repository.
* **Backups:** automated, kept in a place the server cannot overwrite, and a restore tested at least once a quarter.
* **Review** accounts and permissions when someone leaves the team.

## Standards map

Name the standard and edition when the user asks for compliance. The editions below were checked as current on 2026-11-20. Confirm the current one at the owner's site (sources in `versoes-e-fontes.md`) before quoting it in a formal document.

| Need | Standard |
|---|---|
| Web application risks | OWASP Top 10:2025 |
| Verification checklist | OWASP ASVS 5.0.0 |
| APIs | OWASP API Security Top 10 (2023) |
| Features that call an LLM | OWASP Top 10 for LLM Applications (2025) |
| AI agents that use tools | OWASP Top 10 for Agentic Applications (2026 edition, published December 2025) |
| Weakness catalog | CWE Top 25 (MITRE, yearly list; latest is 2025) |
| Secure development process | NIST SP 800-218 SSDF v1.1 (final; v1.2, SP 800-218 Rev. 1, was still a draft when checked) |
| Passwords and authentication | NIST SP 800-63B-4 |
| Payment cards | PCI DSS 4.0.1 (PCI SSC opened comments for the next iteration in 2026; check for a successor) |
| Information security management | ISO/IEC 27001:2022 |
| Server and database hardening | CIS Benchmarks |
| Build integrity | SLSA, SBOM in CycloneDX or SPDX |
| Brazilian personal data | LGPD (Lei 13.709/2018), Resolução CD/ANPD nº 15/2024 (incidents), nº 2/2022 (small processors) |
| EU products with software | Cyber Resilience Act (Regulation 2024/2847): reporting since 11 Sep 2026, full obligations from 11 Dec 2027; see `compliance-licencas.md` |

## Severity scale for audits

Report findings in this order, one line each, in pt-BR, with the fix:

* **CRÍTICO**: exploitable now, data or money at risk. Fix before anything else.
* **ALTO**: exploitable with effort or in a plausible scenario.
* **MÉDIO**: weakens defense, needs another flaw to be exploited.
* **BAIXO**: hygiene, best practice, no direct exposure.
