# PHP — PHP-FIG PSR and php.net standards

Version policy: follow `versoes-e-fontes.md`. Read the project's `composer.json` (`require.php`) or ask the hosting version, look up the current status at php.net/supported-versions.php, and target the newest stable branch the hosting supports. A branch that only gets security fixes is a finding to plan an upgrade; an end-of-life branch is a security finding by itself. Feature notes marked "(8.4+)" and similar apply only when the project's minimum version includes them; otherwise use the older idiom.

## Language and standards
* `declare(strict_types=1);` as the first statement of every file. Type every parameter, return and property.
* PSR-12 formatting, PSR-4 autoloading via Composer, PSR-3 logger interface when a logger exists.
* Modern features when they cut code: constructor property promotion, enums, readonly properties and classes, `match`, named arguments, first-class callable syntax, nullsafe operator, property hooks and asymmetric visibility (8.4+), pipe operator `|>` (8.5).
* Strict separation: business logic in classes, HTML in templates. No SQL and no logic inside HTML files.
* `array_find`, `array_any`, `array_all` (8.4+) instead of hand-rolled loops.

## Security
* Input: `filter_input()` / `filter_var()` with explicit filters. Never trust raw `$_GET`, `$_POST`, `$_COOKIE`, `$_FILES` or `$_SERVER['HTTP_*']`.
* Output: `htmlspecialchars($v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')` on every echo of dynamic data. In attributes, quote them. In JS context, `json_encode` with `JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT`.
* Sessions: `session_regenerate_id(true)` after login and after privilege change; cookie params `httponly`, `secure`, `samesite=Strict`; `session.use_strict_mode=1`.
* Passwords: `password_hash($p, defined('PASSWORD_ARGON2ID') ? PASSWORD_ARGON2ID : PASSWORD_DEFAULT)`, verify with `password_verify()`, rehash check with `password_needs_rehash()`. `PASSWORD_ARGON2ID` exists only when PHP was built with libargon2, which many shared hosts lack; `PASSWORD_DEFAULT` is bcrypt and is acceptable. Compare tokens with `hash_equals()`.
* CSRF: token in session, `random_bytes(32)`, checked with `hash_equals()` on every POST.
* File uploads: check `$_FILES['x']['error']` first, then size, then extension allowlist, then real MIME via `finfo`. Store with a `bin2hex(random_bytes(16))` filename outside the webroot.
* Never `eval`, `extract`, `unserialize` on user data, variable variables, or `include` built from input.
* `error_reporting(E_ALL)` in dev. Production: `display_errors=Off`, `log_errors=On`, `error_log` pointing at `storage/logs/app.log` outside the webroot.

## Exceptional conditions
* Wrap the request boundary in try/catch, log the exception with context, return a generic page. Set `set_exception_handler` and `set_error_handler` so nothing escapes.
* Never use `@` to suppress errors: it hides the bug. Check the condition explicitly instead.
* PDO in exception mode, so a failed query never silently returns false and gets treated as an empty result.

## Supply chain
* `composer.lock` committed. Deploy with `composer install --no-dev --optimize-autoloader`, never `composer update` on the server.
* `composer audit` after every dependency change.
* Prefer packages with a real maintainer and recent releases. Check the vendor name character by character before installing.

## Performance
* OPcache on in production. JIT rarely helps a typical web app; do not enable it by default.
* Generators (`yield`) instead of building large arrays. `unset()` large variables inside long loops.
* Composer autoload instead of manual `require`/`include` chains.
* String building: interpolation or `sprintf`. In loops, collect into an array and `implode`, never repeated concatenation.
* Cache expensive reads (APCu for single server, Redis for multiple) with an explicit TTL and invalidation on write.
* HTTP level: gzip compression for text responses (`mod_deflate` on Apache), long `Cache-Control` or `Expires` only for static files whose name changes when the content changes, `Cache-Control: no-store` on pages with personal data. Slow page? Measure first (browser DevTools Network tab, Lighthouse, the slow query log) and fix the biggest cost, not the first guess.
* `php.ini` limits sized to the app, not to the maximum: `memory_limit`, `max_execution_time`, `upload_max_filesize` and `post_max_size` (the second must be at least as large as the first). Unlimited values turn one bad request into an outage.

## Composer (suggest when applicable)
Trigger: new project, new dependency, PSR-4 needed, manual require/include replaceable. Skip for single-file scripts with no classes.

Format after the code, compact:
> **Composer recomendado** — [motivo em 1 linha pt-BR]
> `composer require vendor/package` · `composer dump-autoload -o`

## Shared hosting reality check
Most Brazilian shared hosting has no SSH, no Composer, no cron beyond cPanel. Before proposing a Composer-based structure, ask: "Sua hospedagem tem acesso SSH ou só o painel?" If only the panel, ship vendor/ inside the zip or write it dependency-free.

### Hardening to paste on shared hosting
`php.ini` (cPanel: "MultiPHP INI Editor"; keep only the lines the host allows):
```ini
expose_php = Off
display_errors = Off
log_errors = On
session.use_strict_mode = 1
session.use_only_cookies = 1
session.cookie_httponly = 1
session.cookie_secure = 1
session.cookie_samesite = Strict
allow_url_include = Off
```
`.htaccess` in the public folder (Apache 2.4, each block guarded so a missing module does not cause a 500):
```apache
# No directory listing.
Options -Indexes

# Block dotfiles (.env, .git) but keep /.well-known/ for security.txt and certificates.
<FilesMatch "^\.(?!well-known)">
    Require all denied
</FilesMatch>

<IfModule mod_headers.c>
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set X-Frame-Options "DENY"
</IfModule>

<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
```
Add `Strict-Transport-Security` only after HTTPS works on the whole site. Keep `.env`, `vendor/`, `storage/` and `logs/` outside the public folder; the `.htaccess` block above is a second line of defense, not the first.
