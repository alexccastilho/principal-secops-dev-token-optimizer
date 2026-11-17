# Python — PEP 8 and python.org standards

Version policy: follow `versoes-e-fontes.md`. Read `requires-python` or the interpreter in use, look up the supported branches at devguide.python.org/versions, and target a supported branch the dependencies also support. End-of-life branches (and Python 2) are a finding. Feature notes marked "3.12+" and similar apply only when the project's minimum version includes them.

## Language and standards
* PEP 8 style, type hints (PEP 484) on every public function, f-strings for formatting.
* Virtual environment always (`python -m venv .venv`). Dependencies pinned in `requirements.txt` or `pyproject.toml` (PEP 621).
* `pathlib` over `os.path`. Context managers (`with`) for files, connections and locks. Dataclasses for data containers.
* EAFP over LBYL where natural. Specific exceptions only, never a bare `except:`.
* Entry point guarded with `if __name__ == "__main__":`.
* Newer features worth using when the minimum version allows: from 3.12 the improved f-string grammar, the `type` statement for aliases and the `override` decorator; from 3.14 t-strings (PEP 750). Free-threaded builds only when the whole dependency chain supports them.

## Security
* SQL: `cursor.execute(sql, params)` with placeholders. ORMs (SQLAlchemy, Django) with bound parameters. Never an f-string in SQL, not even for a "safe" internal value.
* Never `eval` or `exec` on user input. `subprocess.run([...])` with a list and `shell=False`.
* `secrets` module for tokens and password resets, never `random`. `secrets.compare_digest` for token comparison.
* Password hashing with `argon2-cffi` or `bcrypt`. `hashlib` alone is not password hashing.
* `pickle` never on untrusted data. YAML through `yaml.safe_load`. XML from untrusted sources through `defusedxml`.
* Web frameworks: framework CSRF on, template auto-escaping on, `DEBUG = False` in production, `ALLOWED_HOSTS` set, secrets from environment.
* Input validation at the boundary with pydantic (native in FastAPI) or the framework's forms. Validate types AND ranges AND business rules.
* Path handling: resolve and check containment (`Path(base).resolve() in target.resolve().parents`) before opening a user-supplied path.

## Exceptional conditions
* Catch specific exceptions, log with `logger.exception` for the traceback, return a generic message.
* Never `except: pass`. If an error is truly ignorable, catch the specific class and comment why.
* `finally` or a context manager for cleanup, so a failure never leaves a lock held or a transaction open.
* An exception in an auth check denies. Default the permission variable to `False`, never to `True`.

## Supply chain
* `pip-audit` on every dependency change.
* Pin with hashes for anything that touches production: `pip install -r requirements.txt --require-hashes`.
* Check the package name letter by letter. PyPI typosquatting is common and installs run arbitrary code through `setup.py`.
* `pip install` from a URL or a Git branch without a commit hash is unpinned code.

## Performance
* Measure first: `cProfile` or `timeit`. Optimizing an unmeasured path wastes effort.
* Generators and comprehensions instead of manual loops building lists. `itertools` for large sequences.
* Built-ins and stdlib (C-implemented) over hand-rolled logic. `collections.Counter`, `defaultdict`, `deque` where they fit.
* I/O-bound concurrency: `asyncio` or threads. CPU-bound: `multiprocessing`, because of the GIL. Choose per workload.
* `functools.lru_cache` (bounded) on pure functions.
* Database: one query with a join beats a loop of queries, every time.
