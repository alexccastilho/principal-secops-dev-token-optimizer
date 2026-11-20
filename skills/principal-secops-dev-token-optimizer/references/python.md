# Python: PEP 8 and python.org standards (Django, FastAPI, Flask)

Version policy: follow `versoes-e-fontes.md`. Read `requires-python` in `pyproject.toml`, `.python-version`, the lockfile (`uv.lock`, `poetry.lock`, `pylock.toml`) or the Docker image, then check devguide.python.org/versions (or endoflife.date/api/python.json). Target a supported branch the dependencies also support. End-of-life branches, and any Python 2, are a finding. Notes marked "(3.14+)" apply only when the project's minimum includes them. Django lifecycle: djangoproject.com/download (supported versions table).

## Contents
- Standards and style
- Security
- Exceptional conditions
- Supply chain
- Tuning
- Traps and fixes
- Legacy Python: safe maintenance and staged migration
- Django
- FastAPI
- Flask

## Standards and style
* PEP 8 style, type hints on every public function, f-strings for formatting. Ruff as linter and formatter (`ruff check`, `ruff format`); mypy or pyright for types in CI.
* Virtual environment always (`python -m venv .venv`, or `uv`). Dependencies declared in `pyproject.toml` (PEP 621) and locked.
* `pathlib` over `os.path`. Context managers for files, connections and locks. Dataclasses for data containers. Explicit `encoding="utf-8"` on `open()` while supporting versions before 3.15 (UTF-8 default in 3.15+).
* EAFP where natural. Specific exceptions only, never a bare `except:`. Entry point under `if __name__ == "__main__":`.
* (3.12+) `type Alias = ...` and generic syntax `def f[T](x: T)`, `typing.override`, nested quotes in f-strings.
* (3.14+) t-strings (`t"..."` returns `string.templatelib.Template`, so a library can escape each interpolated value: useful for SQL and HTML builders that support it); `except A, B:` without brackets; deferred annotations (`annotationlib`); `compression.zstd`. Free-threaded builds are supported but optional: use only when every C extension in the chain supports them.
* (3.15+) `lazy import x` for slow imports, `frozendict`, `sentinel`.

## Security
* SQL: `cursor.execute(sql, params)` with placeholders; ORMs with bound parameters. Never an f-string, `%` or `+` in SQL, not even for an "internal" value. Identifiers only from an allowlist.
* Commands: never `eval`/`exec` on input. `subprocess.run([...], shell=False)` with a list; never `os.system` or `shell=True` with external data.
* Tokens: `secrets` module, compared with `secrets.compare_digest`. Never `random`.
* Passwords: `argon2-cffi`, `pwdlib[argon2]` or `bcrypt`; the framework hasher in Django. `hashlib` alone is not password hashing.
* Deserialization: `pickle`, `shelve`, `marshal` never on untrusted data; `yaml.safe_load`; `defusedxml` for untrusted XML.
* Archives: `tarfile` extraction with `filter="data"` (the default in 3.14+; pass it explicitly when the minimum is older). `zipfile`: check each member's resolved path before writing.
* Paths: `target = (base / user_part).resolve()` then `target.is_relative_to(base.resolve())` before opening.
* HTTP clients: always a `timeout`; never `verify=False`. A user-supplied URL needs a host allowlist and private-range blocking (SSRF).
* Templates: Jinja2 with `autoescape=True` (Flask and Django enable it); never `Markup()` or `|safe` on user data.
* Validation at the boundary with pydantic (native in FastAPI) or framework forms: types, ranges and business rules.
* Production processes: remote debugging attach exists in 3.14+; set `PYTHON_DISABLE_REMOTE_DEBUG=1` (or `-X disable-remote-debug`) where other local users could reach the process.

## Exceptional conditions
* Catch specific exceptions, `logger.exception(...)` for the traceback, generic message out.
* Never `except: pass`. If truly ignorable, catch the specific class and comment why.
* `finally` or a context manager for cleanup. No `return` inside `finally` (it swallows the exception; SyntaxWarning in 3.14+).
* An exception in an auth check denies. Default `allowed = False`.

## Supply chain
* `pip-audit` (PyPA) on every dependency change: `pip-audit -r requirements.txt`, or point it at `pyproject.toml`/`pylock.toml`. With uv: `uv audit`.
* Production installs from a lock with hashes: `pip install --require-hashes -r requirements.txt`, `uv sync --locked`, or a `pylock.toml` (PEP 751; `pip lock` is experimental since pip 25.1).
* Cooldown against fresh malicious uploads: `pip install --uploaded-prior-to=P3D` (pip 26.0+; durations from 26.1), uv `--exclude-newer`.
* Check the package name letter by letter; typosquatting on PyPI is common and source distributions run code at build time. Prefer wheels.
* Never `pip install` from a URL or Git branch without a pinned commit hash.

## Tuning
* Measure first: `cProfile` (alias of `profiling.tracing` in 3.15+), the sampling profiler `python -m profiling.sampling` (3.15+), or `timeit`.
* Comprehensions and generators; built-ins and stdlib (`collections`, `itertools`) over hand-rolled loops.
* I/O-bound: `asyncio` or threads. CPU-bound: `multiprocessing`/`ProcessPoolExecutor`, or a free-threaded build when the dependencies support it. On Unix except macOS the default start method is `forkserver` (3.14+): code that relied on `fork` inheriting state must pass it explicitly.
* `functools.lru_cache(maxsize=...)` on pure functions.
* Database: one query with a join beats a loop of queries (N+1).

## Traps and fixes
* Mutable default argument `def f(x=[])`: shared across calls. Use `None` and create inside.
* `requests.get(url)` with no timeout hangs a worker forever: always `timeout=`.
* `assert` for security checks: stripped under `-O`. Use `if ...: raise`.
* `DEBUG = True` or `app.run(debug=True)` in production: the debugger executes code from the browser. Always off.
* `os.path.join(base, user)` with an absolute `user` discards `base`: resolve and check containment.
* `datetime.utcnow()` is naive and deprecated: `datetime.now(timezone.utc)`.
* `tempfile.mktemp()`: race condition. `NamedTemporaryFile` or `mkstemp`.
* Logging `request.data` or headers: leaks passwords and tokens. Log ids, not payloads.

## Legacy Python: safe maintenance and staged migration
* Python 2 or an end-of-life 3.x that works: fix the reported fault first; never a rewrite.
* Stages: 1) freeze what runs (`pip freeze > requirements-legacy.txt`), add tests around the critical paths; 2) run `pip-audit` and list blocked upgrades; 3) move one supported minor at a time in a fresh venv on a staging copy, reading "What's New" removals; 4) upgrade the framework one LTS at a time (Django: through each LTS, fixing deprecation warnings with `python -Wd`); 5) only then modernize syntax with Ruff's `UP` rules.

## Django
* Settings: `DEBUG = False`, `ALLOWED_HOSTS` set, `SECRET_KEY` from the environment, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` after HTTPS works. Run `python manage.py check --deploy`.
* ORM with parameters; `raw()`, `extra()` and `RawSQL` only with `params`. Never format strings into them.
* CSRF middleware on; `@csrf_exempt` only for webhook endpoints that verify a signature.
* Object-level access: filter by owner (`Model.objects.filter(owner=request.user)`), never fetch by id alone.
* (6.0+) built-in CSP: `django.middleware.csp.ContentSecurityPolicyMiddleware` with `SECURE_CSP` (or `SECURE_CSP_REPORT_ONLY` first) and the `csp` context processor for nonces. Older versions: `django-csp`.
* (6.0+) `django.tasks` defines background tasks but ships no production worker; keep the existing queue (Celery, RQ) until a real backend is chosen.
* DRF: default permission class `IsAuthenticated` (not `AllowAny`), throttling on auth endpoints, serializers with explicit `fields` (never `__all__` on models with secrets).

## FastAPI
* Pydantic models for every body, query and response (`response_model` strips fields the client must not see).
* Auth as a dependency (`Depends`) on the router, not repeated per route, so a new route cannot forget it.
* Password hashing as in the official tutorial: `pwdlib[argon2]` with `PasswordHash.recommended()`; JWT with PyJWT and an explicit `algorithms=[...]`.
* CORS: `CORSMiddleware` with exact origins; never `allow_origins=["*"]` with `allow_credentials=True`.
* Blocking calls (sync DB driver, `requests`) inside `async def` freeze the event loop: use `def` endpoints or async drivers.
* Disable or protect `/docs` and `/openapi.json` on internal-only APIs (`docs_url=None`).

## Flask
* `SECRET_KEY` from the environment; session cookies `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`.
* No built-in CSRF: use Flask-WTF `CSRFProtect` for forms.
* Set `MAX_CONTENT_LENGTH` (unset by default) and `TRUSTED_HOSTS` in production.
* Jinja escapes, but not unquoted attributes or `javascript:` URLs: quote attributes, validate URL schemes, add a CSP.
* Run behind a production WSGI server (gunicorn, waitress), never the development server.
