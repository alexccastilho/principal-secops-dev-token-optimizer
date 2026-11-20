# PHP: PHP-FIG and php.net standards (WordPress, Laravel, Symfony)

Version policy: follow `versoes-e-fontes.md`. Read `composer.json` (`require.php`, `composer.lock` platform) or ask the hosting panel version, then check php.net/supported-versions.php or endoflife.date/api/php.json. Target the newest branch the hosting and the framework both support. A security-only branch is a finding to plan an upgrade; an end-of-life branch is a security finding by itself. Notes marked "(8.5+)" and similar apply only when the project's minimum includes them; otherwise use the older idiom. Framework lifecycles: laravel.com/docs (Support Policy), symfony.com/releases, wordpress.org (Hosting Handbook for PHP requirements).

## Contents
- Standards and style
- Security
- Exceptional conditions
- Supply chain
- Tuning
- Traps and fixes
- Legacy PHP: safe maintenance and staged migration
- Composer, shared hosting and hardening
- WordPress
- Laravel
- Symfony

## Standards and style
* `declare(strict_types=1);` first statement of every new file. Type every parameter, return and property.
* PER Coding Style (it replaces PSR-12), PSR-4 autoload via Composer, PSR-3 logger when a logger exists. Formatter: PHP-CS-Fixer or PHP_CodeSniffer; Laravel Pint in Laravel projects. Follow the project's existing config.
* Static analysis: PHPStan or Psalm in CI. Psalm `--taint-analysis` traces user input to SQL, shell and HTML sinks.
* Business logic in classes, HTML in templates. No SQL and no logic inside HTML files.
* Modern features when they cut code: enums, readonly properties and classes, `match`, constructor promotion, named arguments, first-class callables, nullsafe `?->`.
* (8.4+) property hooks, asymmetric visibility `public private(set)`, `array_find()`, `array_find_key()`, `array_any()`, `array_all()`, `new Foo()->bar()` without extra parentheses, `#[\Deprecated]`, `Dom\HTMLDocument` (HTML5 parser).
* (8.5+) pipe operator `|>`, `clone($obj, ['prop' => $v])` for readonly with-ers, `#[\NoDiscard]` (silence with `(void)`), `array_first()`, `array_last()`, built-in URI extension (`Uri\Rfc3986\Uri`, `Uri\WhatWg\Url`) for parsing URLs instead of `parse_url()`.
* (8.6+) partial function application (`f(?, 'x')`), `clamp()`, `SortDirection` enum, readonly property defaults, `\Time\Duration`.

## Security
* Input: `filter_input()` / `filter_var()` with explicit filters. Never trust raw `$_GET`, `$_POST`, `$_COOKIE`, `$_FILES` or `$_SERVER['HTTP_*']`.
* SQL: PDO with prepared statements and `PDO::ATTR_EMULATE_PREPARES => false`; identifiers (table, column, ORDER BY) only from an allowlist. Never interpolate a variable into SQL.
* Output: `htmlspecialchars($v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')` on every echo of dynamic data, attributes always quoted. In a JS context: `json_encode` with `JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT`. A URL in `href`: allow only `http`/`https` schemes.
* Sessions: `session_regenerate_id(true)` after login and privilege change; cookie `httponly`, `secure`, `samesite`; `session.use_strict_mode=1`. (8.6+) strict mode, `httponly` and `SameSite=Lax` are the defaults; still set them explicitly while older branches are supported.
* Passwords: `password_hash($p, defined('PASSWORD_ARGON2ID') ? PASSWORD_ARGON2ID : PASSWORD_DEFAULT)`, `password_verify()`, `password_needs_rehash()`. Argon2id needs a libargon2 build (many shared hosts lack it); `PASSWORD_DEFAULT` (bcrypt) is acceptable. Tokens compared with `hash_equals()`, generated with `random_bytes()`.
* CSRF: token in session from `random_bytes(32)`, checked with `hash_equals()` on every state-changing request.
* Uploads: check `$_FILES['x']['error']`, then size, then extension allowlist, then real MIME via `finfo`. Store under `bin2hex(random_bytes(16))` outside the webroot; never serve uploads from a folder that executes PHP.
* Commands: avoid shell. If unavoidable, `escapeshellarg()` on every argument, or `proc_open()` with an array command (no shell). Never backticks (deprecated as `shell_exec` alias in 8.5+).
* Never `eval`, `extract` on input, variable variables, `include`/`require` built from input, or `unserialize` on user data (use `json_decode`; if unavoidable, `['allowed_classes' => false]`).
* Outbound requests from a user URL: allowlist the host, block private and loopback ranges, disable redirects or re-check each hop (SSRF).
* Secrets in environment or a config file outside the webroot. Errors: `display_errors=Off`, `log_errors=On`, log file outside the webroot.

## Exceptional conditions
* Catch at the request boundary, log with context, return a generic page. Set `set_exception_handler` and `set_error_handler` so nothing escapes.
* Never `@` to silence errors. Check the condition explicitly.
* PDO in exception mode (`PDO::ERRMODE_EXCEPTION`, default since 8.0), so a failed query never turns into an empty result.
* An exception inside an auth or payment check denies. Default `$allowed = false`.
* (8.6+) `fclose()`, `file_put_contents()` and `copy()` return false when the final flush fails, and many functions throw `ValueError` on NUL bytes or out-of-range input: check return values, catch `ValueError` at the boundary.

## Supply chain
* `composer.lock` committed. Deploy with `composer install --no-dev --optimize-autoloader`, never `composer update` on the server.
* `composer audit` after every dependency change; in CI `composer audit --locked`. Abandoned packages fail the audit by default (2.7+).
* Composer 2.9+ refuses to resolve versions with known advisories during `update`/`require` (`policy.advisories.block`, formerly `audit.block-insecure`). Do not disable it to make an install pass; upgrade the package or record why the advisory does not apply.
* Where the installed Composer supports it, `policy.cooldown` delays brand-new releases (off by default). `--no-blocking` bypasses all policy for one run: only for an urgent fix, said in pt-BR.
* Check the vendor name character by character on packagist.org; prefer a real maintainer and recent releases.

## Tuning
* OPcache on in production. JIT rarely helps a web app; do not enable it by default.
* Generators (`yield`) instead of large arrays. Composer autoload instead of `require` chains.
* Strings in loops: collect into an array and `implode`.
* Cache expensive reads (APCu single server, Redis multi) with TTL and invalidation on write.
* HTTP: compression for text (`mod_deflate`), long `Cache-Control` only for fingerprinted static files, `Cache-Control: no-store` on pages with personal data. Measure first (DevTools Network, Lighthouse, slow query log).
* `php.ini` limits sized to the app: `memory_limit`, `max_execution_time`, `upload_max_filesize`, `post_max_size` (at least as large as the upload limit). Unlimited values turn one bad request into an outage.

## Traps and fixes
* `==` with mixed types (`"abc" == 0` behaved differently before 8.0, `"1e3" == "1000"` is true): use `===` and `hash_equals()` for secrets.
* `in_array($x, $list)` without `true` as third argument: loose comparison. Pass `true`.
* `$_SERVER['HTTP_HOST']` or `PHP_SELF` echoed or used to build links: header injection and XSS. Use a configured base URL.
* `mysqli_real_escape_string` as "protection": still injectable in identifier and numeric contexts. Use prepared statements.
* `header('Location: ' . $_GET['next'])`: open redirect. Allow only relative paths or an allowlist, then `exit;`.
* `md5()`/`sha1()` for passwords, `rand()`/`mt_rand()`/`uniqid()` for tokens: replace with `password_hash()` and `random_bytes()`.
* `__sleep()`/`__wakeup()` are soft-deprecated (8.5+): new code uses `__serialize()`/`__unserialize()`.
* `return` inside `finally` is deprecated (8.6+) and hides the exception: move the return after the block.

## Legacy PHP: safe maintenance and staged migration
* Old `mysql_*` code, PHP 5/7, no Composer: never rewrite a working system. Fix the reported fault, then offer a staged plan.
* Stages: 1) inventory PHP version, extensions and hosting options; 2) add `composer.json` and an autoloader without moving files; 3) replace `mysql_*` with PDO prepared statements one file at a time; 4) raise PHP one supported branch at a time on a staging copy, reading each migration guide (php.net/manual/en/migrationXY.php); 5) only then refactor structure.
* Rector can automate syntax upgrades between branches; run it on a branch, review the diff, test before merging.
* Back up files and database before each stage (SKILL.md section 4).

## Composer, shared hosting and hardening
Suggest Composer when: new project, new dependency, PSR-4 needed, manual require chains replaceable. Skip for single-file scripts. Format after the code:
> **Composer recomendado**: [motivo em 1 linha pt-BR]
> `composer require vendor/package` · `composer dump-autoload -o`

Most Brazilian shared hosting has no SSH and no Composer. Ask first: "Sua hospedagem tem acesso SSH ou só o painel?" If only the panel, ship `vendor/` inside the zip or write it dependency-free.

`php.ini` (cPanel "MultiPHP INI Editor"; keep only lines the host allows):
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

# Block hidden files (.env) but keep /.well-known/ for security.txt and certificates.
<FilesMatch "^\.(?!well-known)">
    Require all denied
</FilesMatch>

# FilesMatch sees only the file name, so /.git/config would still be served.
<IfModule mod_alias.c>
    RedirectMatch 404 "/\.(?!well-known/)"
</IfModule>

<IfModule mod_headers.c>
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set X-Frame-Options "DENY"
</IfModule>

<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
```
Add `Strict-Transport-Security` only after HTTPS works on the whole site. Keep `.env`, `vendor/`, `storage/` and `logs/` outside the public folder; `.htaccess` is a second line of defense. In an uploads folder, an `.htaccess` with `<FilesMatch "\.(php|phar|phtml)$">` and `Require all denied` stops uploaded scripts from running.

## WordPress
* Never edit core, a parent theme or someone else's plugin: updates erase it. Use a child theme or a small custom plugin.
* Database: `$wpdb->prepare()` with `%d`, `%f`, `%s`, and `%i` for identifiers (WordPress 6.2+); `$wpdb->insert()`/`update()` for writes; table names from `$wpdb->prefix`. `prepare()` without placeholders is not protection.
* Escape late, at echo: `esc_html()`, `esc_attr()`, `esc_url()`, `esc_js()`, `wp_kses_post()`. Input: `wp_unslash()` then `sanitize_text_field()`, `absint()`, `sanitize_email()`.
* Every form, AJAX action and REST route: nonce (`check_admin_referer()`, `check_ajax_referer()`) AND `current_user_can()`. A nonce is not a permission. REST routes get a real `permission_callback`, never `__return_true` on writes or private data. `wp_ajax_nopriv_*` hooks are public endpoints.
* Uploads via `wp_handle_upload()`; user-supplied URLs fetched with `wp_safe_remote_get()`.
* `wp-config.php`: never in Git or the chat. Production: `DISALLOW_FILE_EDIT` true, `WP_DEBUG_DISPLAY` false.
* Lint with WordPress Coding Standards (PHP_CodeSniffer ruleset, security sniffs for escaping, nonces, sanitizing, prepared SQL). Before shipping a plugin, run Plugin Check (`wp plugin check <plugin>`).
* WordPress itself runs on old PHP (minimum is far below the recommended): a plugin must declare `Requires PHP` in its header and not use newer syntax than that.
* Most intrusions come through outdated or abandoned plugins: update core, themes and plugins after a backup, delete inactive ones, check last update and active installs before adding one.

## Laravel
* Lifecycle and PHP range per major in the docs Support Policy table; Laravel 13 needs PHP 8.3+.
* `APP_DEBUG=false` and a set `APP_KEY` in production; `.env` never committed or public. A leaked `APP_KEY` lets attackers forge encrypted cookies: rotate it.
* Mass assignment: `$fillable` on every model, never `$guarded = []` with `$request->all()`. Use `$request->validated()` from a Form Request.
* Queries: Eloquent or the query builder with bindings. `DB::raw()`, `whereRaw()`, `orderByRaw()`, `selectRaw()` only with `?` bindings; column names from an allowlist.
* Blade `{{ }}` escapes; `{!! !!}` does not: only for trusted, already-sanitized HTML.
* Authorization with policies and gates (`$this->authorize()`, `can` middleware, `#[Authorize]` attribute in 13+); route model binding does not check ownership.
* CSRF middleware stays on for web routes (13+: `PreventRequestForgery`, adds origin checks). Excluding a route from it needs another auth method.
* `php artisan config:cache` and `route:cache` in deploy; `composer audit` in CI.

## Symfony
* Supported lines and PHP minimums at symfony.com/releases (7.4 LTS needs PHP 8.2+, 8.x needs PHP 8.4+). Prefer the LTS for a long-lived app.
* `APP_ENV=prod`, `APP_DEBUG=0`; the profiler and `debug` bundles only in dev. A public profiler leaks secrets.
* Secrets via `secrets:set` (vault) or real environment variables, not committed `.env.local`.
* Security: `access_control` plus voters (`#[IsGranted]`) for object-level checks; firewall order matters, the first match wins.
* Twig auto-escapes; `|raw` only for trusted HTML. Forms include CSRF protection by default: keep `csrf_protection` on.
* Doctrine: DQL and QueryBuilder with `setParameter()`, never string concatenation.
* `composer audit` in CI (it covers more advisories than `symfony check:security`, which needs the Symfony CLI).
