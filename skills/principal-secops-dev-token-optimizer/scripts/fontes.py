#!/usr/bin/env python3
"""Live facts for the skill: support status of a version and known flaws in dependencies.

The references hold stable rules; facts that change with the calendar are read here, at
the moment of use, from machine-readable sources. Output is short on purpose (it goes
into the model's context) and carries only structured fields, never free text from a
page, so fetched content cannot act as instructions.

  fontes.py versao <tecnologia> [--em-uso X.Y.Z]   support status (endoflife.date)
  fontes.py deps <pasta>                             known flaws in locked dependencies (OSV + CISA KEV)
  fontes.py onde <tecnologia>                        where to check by hand (registry entry)
  fontes.py lista                                    technologies in the registry
  fontes.py diagnostico [--links]                    every source still answers with the fields used (CI canary)

Global options: --json, --cache-dir DIR, --offline (or SECOPS_OFFLINE=1), --max-chars N.
Exit codes: 0 ok; 1 something to act on (end of life, behind the latest patch, known flaw);
2 usage error or unknown technology; 3 could not check (no network, source down or changed).

Python 3.8+, standard library only. Author: Alex Camacho Castilho
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parent / "fontes" / "registro.json"

# Fixed in the distributed script, never read from the registry: a changed registry can
# only point to paths on these hosts. A new host needs a new release.
ALLOWED_HOSTS = frozenset({"endoflife.date", "api.osv.dev", "www.cisa.gov"})
EOL_URL = "https://endoflife.date/api/v1/products/{slug}/"
OSV_BATCH = "https://api.osv.dev/v1/querybatch"
OSV_VULN = "https://api.osv.dev/v1/vulns/{id}"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

TTL = {"eol": 24 * 3600, "osv": 6 * 3600, "kev": 24 * 3600}
TIMEOUT = 15
MAX_BYTES = 8 * 1024 * 1024
MAX_DETAILS = 25
USER_AGENT = "secops-fontes/1 (+https://github.com/alexccastilho/principal-secops-dev-token-optimizer)"

OK, ACT, USAGE, UNCHECKED = 0, 1, 2, 3


class Unchecked(Exception):
    """A source could not be read; the caller reports "não conferido", never a guess."""


# --------------------------------------------------------------------------- cache and HTTP

def cache_dir(arg: Optional[str]) -> Path:
    """Where cached answers live. Never the skill folder (read-only on claude.ai, replaced on
    every update) and never the user's project. Claude Code substitutes ${CLAUDE_PLUGIN_DATA}
    in the skill text; when it arrives literal or empty, fall back to the user cache."""
    candidates = [arg, os.environ.get("SECOPS_CACHE_DIR")]
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        candidates.append(os.path.join(os.environ["LOCALAPPDATA"], "secops", "cache"))
    candidates.append(os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "secops"))
    candidates.append(os.path.join(tempfile.gettempdir(), "secops-cache"))
    for cand in candidates:
        if not cand or "${" in cand or cand.startswith("$"):
            continue
        path = Path(cand)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return path
        except OSError:
            continue
    return Path(tempfile.mkdtemp(prefix="secops-"))


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        if urllib.parse.urlsplit(newurl).hostname not in ALLOWED_HOSTS or not newurl.startswith("https://"):
            raise Unchecked(f"redirecionamento recusado para {urllib.parse.urlsplit(newurl).hostname}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_SameHostRedirect)


class Fetcher:
    def __init__(self, cache: Path, offline: bool):
        self.cache, self.offline = cache, offline
        self.stale_dates: List[float] = []  # instantes do cache vencido usado

    def oldest_stale(self) -> Optional[str]:
        """Data do cache vencido mais antigo, para exibir. Compara o instante,
        nao o texto: "01/12" vem antes de "25/11" em ordem de texto."""
        if not self.stale_dates:
            return None
        return time.strftime("%d/%m/%Y", time.localtime(min(self.stale_dates)))

    def _key(self, url: str, body: Optional[bytes]) -> Path:
        digest = hashlib.sha256(url.encode() + b"\0" + (body or b"")).hexdigest()[:32]
        return self.cache / f"{digest}.json"

    def get_json(self, url: str, kind: str, body: Optional[Dict[str, Any]] = None) -> Any:
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
            raise Unchecked(f"host fora da lista permitida: {parts.hostname}")
        raw_body = json.dumps(body, sort_keys=True).encode() if body is not None else None
        path = self._key(url, raw_body)
        cached = None
        if path.is_file():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                cached = None
        if cached and time.time() - cached.get("t", 0) < TTL[kind]:
            return cached["data"]
        if self.offline:
            return self._stale(cached, "modo offline")
        req = urllib.request.Request(url, data=raw_body, method="POST" if raw_body else "GET",
                                     headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                                              "Content-Type": "application/json"})
        try:
            with _OPENER.open(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise Unchecked("resposta grande demais")
            data = json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise Unchecked("não encontrado na fonte (404)")
            return self._stale(cached, f"fonte respondeu {exc.code}")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return self._stale(cached, f"sem resposta ({type(exc).__name__})")
        try:
            path.write_text(json.dumps({"t": time.time(), "data": data}), encoding="utf-8")
        except OSError:
            pass
        return data

    def _stale(self, cached: Optional[Dict[str, Any]], why: str) -> Any:
        if cached:
            self.stale_dates.append(float(cached.get("t", 0)))
            return cached["data"]
        raise Unchecked(why)


# --------------------------------------------------------------------------- registry

def load_registry() -> Dict[str, Any]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def find_tech(registry: Dict[str, Any], name: str) -> Tuple[str, Dict[str, Any]]:
    techs = registry["tecnologias"]
    key = name.strip().lower().replace(" ", "-")
    aliases = {"node": "nodejs", "node.js": "nodejs", "py": "python", "c#": "dotnet", ".net": "dotnet",
               "csharp": "dotnet", "golang": "go", "postgres": "postgresql", "mssql": "sqlserver",
               "sql-server": "sqlserver", "wp": "wordpress", "spring": "spring-boot", "temurin": "java"}
    key = aliases.get(key, key)
    if key not in techs:
        raise KeyError(name)
    return key, techs[key]


# --------------------------------------------------------------------------- versions

def _vtuple(text: str) -> Tuple[int, ...]:
    nums = re.findall(r"\d+", text or "")
    return tuple(int(n) for n in nums[:4])


def _vkey(text: str) -> Tuple[Any, ...]:
    """Chave para comparar versoes: 1.2.3-rc1 < 1.2.3 < 1.2.3.post1.
    Fase: 0 dev, 1 pre-release (alpha, beta, rc, pseudo-versao do Go), 2 final, 3 post."""
    m = re.match(r"\s*[vV]?(\d+(?:\.\d+)*)(.*)", text or "")
    if not m:
        return ((0, 0, 0, 0), 1, ((1, (text or "").lower()),))
    nums = tuple(int(n) for n in m.group(1).split(".")[:4])
    nums += (0,) * (4 - len(nums))
    rest = m.group(2).split("+", 1)[0].lower()  # "+build" nao muda a ordem
    parts = tuple((0, int(p)) if p.isdigit() else (1, p) for p in re.findall(r"\d+|[a-z]+", rest))
    if not parts:
        phase = 2
    elif parts[0] == (1, "post"):
        phase = 3
    elif parts[0] == (1, "dev"):
        phase = 0
    else:
        phase = 1
    return (nums, phase, parts)


def _status(rel: Dict[str, Any]) -> Tuple[str, bool]:
    """(pt-BR status, needs action)."""
    if rel.get("isEol"):
        return f"fim de vida desde {rel.get('eolFrom') or '?'}", True
    if rel.get("isEoas"):
        return f"só correções de segurança, até {rel.get('eolFrom') or '?'}", False
    until = rel.get("eolFrom")
    return ("suportada" + (f", até {until}" if until else "")), False


def normalize_version(text: str) -> str:
    """'v22.3.0', '^8.1', '>=3.11', 'net8.0', 'PHP 8.2.10' -> the first dotted number."""
    m = re.search(r"\d+(?:\.\d+)*", text or "")
    return m.group(0) if m else (text or "").strip()


def match_cycle(releases: List[Dict[str, Any]], in_use: str) -> Optional[Dict[str, Any]]:
    best, best_len = None, -1
    for rel in releases:
        name = str(rel.get("name", ""))
        if in_use == name or in_use.startswith(name + "."):
            if len(name) > best_len:
                best, best_len = rel, len(name)
    return best


def cmd_versao(args, fetch: Fetcher, registry) -> Tuple[int, Dict[str, Any], List[str]]:
    key, tech = find_tech(registry, args.tecnologia)
    if not tech.get("eol"):
        raise Unchecked(f"{tech['nome']} não tem ciclo de vida em API (camada {tech.get('camada')}); use: fontes.py onde {key}")
    data = fetch.get_json(EOL_URL.format(slug=tech["eol"]), "eol")
    try:
        releases = data["result"]["releases"]
    except (KeyError, TypeError):
        raise Unchecked("formato da fonte mudou (result.releases ausente)")
    out = {"tecnologia": tech["nome"], "fonte": EOL_URL.format(slug=tech["eol"]), "consultado_em": date.today().isoformat()}
    lines, code = [], OK
    if args.em_uso:
        args.em_uso = normalize_version(args.em_uso)
        rel = match_cycle(releases, args.em_uso)
        if not rel:
            out["em_uso"] = {"versao": args.em_uso, "status": "desconhecida na fonte"}
            lines.append(f"{tech['nome']} {args.em_uso}: ciclo não encontrado na fonte. Confira em {tech.get('notas') or out['fonte']}")
            return ACT, out, lines
        status, act = _status(rel)
        latest = (rel.get("latest") or {})
        behind = bool(latest.get("name")) and _vkey(args.em_uso) < _vkey(latest["name"]) and len(_vtuple(args.em_uso)) >= len(_vtuple(latest["name"]))
        out["em_uso"] = {"versao": args.em_uso, "ciclo": rel.get("name"), "status": status,
                         "ultimo_patch": latest.get("name"), "atras_do_patch": behind, "notas": latest.get("link")}
        line = f"{tech['nome']} {args.em_uso} (ciclo {rel.get('name')}): {status}."
        if latest.get("name"):
            line += f" Último patch do ciclo: {latest['name']} ({latest.get('date') or '?'})."
        if behind:
            line += " A versão em uso está atrás do patch: atualizar corrige falhas listadas nas notas."
        lines.append(line)
        if latest.get("link"):
            lines.append(f"Notas: {latest['link']}")
        code = ACT if (act or behind) else OK
    maintained = [r for r in releases if r.get("isMaintained")][:4]
    out["ciclos_mantidos"] = [{"ciclo": r.get("name"), "status": _status(r)[0], "lts": bool(r.get("isLts")),
                               "ultimo_patch": (r.get("latest") or {}).get("name")} for r in maintained]
    lines.append("Ciclos mantidos: " + "; ".join(
        f"{r.get('name')}{' LTS' if r.get('isLts') else ''} ({_status(r)[0]}, patch {(r.get('latest') or {}).get('name') or '?'})"
        for r in maintained))
    return code, out, lines


# --------------------------------------------------------------------------- dependencies

NPM_REGISTRY = "https://registry.npmjs.org/"
PYPI_INDEX = ("https://pypi.org/simple", "https://files.pythonhosted.org/")
CRATES_INDEX = ("registry+https://github.com/rust-lang/crates.io-index", "sparse+https://index.crates.io/")


def _go_private(module: str, own: str) -> bool:
    """Go has no registry field in go.mod. A module is treated as private when GOPRIVATE,
    GONOPROXY or GONOSUMDB match it, or when it lives under the project's own path."""
    patterns = []
    for var in ("GOPRIVATE", "GONOPROXY", "GONOSUMDB"):
        patterns += [p.strip() for p in os.environ.get(var, "").split(",") if p.strip()]
    for pat in patterns:
        prefix = pat.rstrip("/*")
        if module == prefix or module.startswith(prefix + "/") or fnmatch.fnmatch(module, pat):
            return True
    own_prefix = "/".join(own.split("/")[:2]) if own.count("/") >= 1 else own
    return bool(own_prefix) and (module == own_prefix or module.startswith(own_prefix + "/"))


def _nuget_private_feed(lock: Path, top: Path) -> bool:
    """A private feed in any nuget.config between the lockfile and the scanned folder (or in
    the user's own config) means a name could come from it: skip the whole lockfile."""
    configs = []
    for parent in [lock.parent] + list(lock.parents):
        configs += [parent / n for n in ("nuget.config", "NuGet.config", "NuGet.Config")]
        if parent == top:
            break
    appdata = os.environ.get("APPDATA")
    if appdata:
        configs.append(Path(appdata) / "NuGet" / "NuGet.Config")
    configs.append(Path.home() / ".nuget" / "NuGet" / "NuGet.Config")
    for cfg in configs:
        if cfg.is_file():
            text = cfg.read_text(encoding="utf-8", errors="replace")
            for url in re.findall(r'value\s*=\s*"([^"]+)"', text):
                if "://" in url and not url.startswith("https://api.nuget.org/"):
                    return True
    return False


def _pip_private_index() -> bool:
    """A private index set outside requirements.txt (environment or pip configuration) means
    any name in it could come from there: skip requirements files altogether."""
    def private(value: str) -> bool:
        return any(u and not u.startswith(PYPI_INDEX) for u in value.split())
    for var in ("PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "PIP_FIND_LINKS"):
        if private(os.environ.get(var, "")):
            return True
    configs = [Path(os.environ["PIP_CONFIG_FILE"])] if os.environ.get("PIP_CONFIG_FILE") else []
    for base in (os.environ.get("APPDATA"), os.environ.get("PROGRAMDATA")):
        if base:
            configs.append(Path(base) / "pip" / "pip.ini")
    home = Path.home()
    configs += [home / ".pip" / "pip.conf", home / ".config" / "pip" / "pip.conf", Path("/etc/pip.conf")]
    if os.environ.get("VIRTUAL_ENV"):
        configs += [Path(os.environ["VIRTUAL_ENV"]) / n for n in ("pip.ini", "pip.conf")]
    for cfg in configs:
        try:
            text = cfg.read_text(encoding="utf-8", errors="replace") if cfg.is_file() else ""
        except OSError:
            continue
        for m in re.finditer(r"^\s*(index-url|extra-index-url|find-links)\s*=\s*(.+)$", text, re.M):
            if private(m.group(2).strip()):
                return True
    return False


def read_locks(folder: Path) -> Tuple[List[Tuple[str, str, str, str]], List[str]]:
    """((ecosystem, name, version, file) for every public pinned dependency, skipped notes).

    Only a dependency that provably comes from the public registry is listed. Anything from a
    private registry, a path, a URL or a Git repository, or a file that mixes in a private
    index, is left out and never sent to a third party."""
    found: List[Tuple[str, str, str, str]] = []
    skipped: List[str] = []
    skip = {"node_modules", "vendor", ".git", ".venv", "venv", "__pycache__", "target", "bin", "obj"}

    def walk():
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in skip]
            for f in files:
                yield Path(root) / f

    for path in walk():
        name, rel = path.name, str(path.relative_to(folder))
        try:
            if name == "composer.lock":
                data = json.loads(path.read_text(encoding="utf-8"))
                for pkg in data.get("packages", []) + data.get("packages-dev", []):
                    # Packages served by Packagist carry its download-notification URL;
                    # private repositories (Satis, Private Packagist, VCS) do not.
                    if (pkg.get("name") and pkg.get("version")
                            and str(pkg.get("notification-url", "")).startswith("https://packagist.org/")):
                        found.append(("Packagist", pkg["name"], pkg["version"].lstrip("v"), rel))
            elif name == "package-lock.json":
                data = json.loads(path.read_text(encoding="utf-8"))
                pkgs = data.get("packages")
                entries = []
                if isinstance(pkgs, dict):
                    entries = [(k.split("node_modules/")[-1], e) for k, e in pkgs.items() if k.startswith("node_modules/")]
                else:
                    entries = list((data.get("dependencies") or {}).items())
                for dep, entry in entries:
                    if (isinstance(entry, dict) and entry.get("version") and not entry.get("link")
                            and str(entry.get("resolved") or "").startswith(NPM_REGISTRY)):
                        found.append(("npm", dep, entry["version"], rel))
            elif re.fullmatch(r"requirements.*\.txt", name):
                text = path.read_text(encoding="utf-8", errors="replace")
                if (re.search(r"^\s*(-i\b|--index-url|--extra-index-url|-f\b|--find-links)", text, re.M)
                        or _pip_private_index()):
                    skipped.append(f"{rel}: usa índice próprio, não enviado")
                    continue
                for line in text.splitlines():
                    m = re.match(r"\s*([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*==\s*([A-Za-z0-9_.\-+!]+)\s*(?:[;#].*)?$", line)
                    if m:
                        found.append(("PyPI", m.group(1), m.group(2), rel))
            elif name in ("poetry.lock", "uv.lock", "Cargo.lock"):
                text = path.read_text(encoding="utf-8", errors="replace")
                for block in re.split(r"\n\[\[package\]\]", "\n" + text)[1:]:
                    n = re.search(r'^name\s*=\s*"([^"]+)"', block, re.M)
                    v = re.search(r'^version\s*=\s*"([^"]+)"', block, re.M)
                    src = re.search(r'^source\s*=\s*(.+)$', block, re.M)
                    if not (n and v):
                        continue
                    if name == "poetry.lock":
                        # Poetry writes a [package.source] table only for non-PyPI packages.
                        public = "[package.source]" not in block
                        eco = "PyPI"
                    elif name == "uv.lock":
                        public = bool(src) and bool(re.search(r'registry\s*=\s*"(%s)/?"' % "|".join(map(re.escape, PYPI_INDEX)), src.group(1)))
                        eco = "PyPI"
                    else:
                        public = bool(src) and src.group(1).strip().strip('"').startswith(CRATES_INDEX)
                        eco = "crates.io"
                    if public:
                        found.append((eco, n.group(1), v.group(1), rel))
            elif name == "go.mod":
                text = path.read_text(encoding="utf-8", errors="replace")
                own = (re.search(r"^module\s+(\S+)", text, re.M) or [None, ""])[1]
                # So o que esta em "require": exclude e replace citam modulos que nao entram no build.
                block = False
                for raw in text.splitlines():
                    line = raw.split("//", 1)[0].strip()
                    if block:
                        if line.startswith(")"):
                            block = False
                            continue
                    elif re.match(r"require\s*\($", line):
                        block = True
                        continue
                    elif line.startswith("require "):
                        line = line[len("require "):].strip()
                    else:
                        continue
                    m = re.match(r"([a-z0-9.\-]+\.[a-z]{2,}/\S+)\s+(v[0-9]\S*)$", line)
                    if m and not _go_private(m.group(1), own):
                        found.append(("Go", m.group(1), m.group(2), rel))
            elif name == "Gemfile.lock":
                text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
                for section in re.split(r"\n\s*\n", text):
                    if not section.startswith("GEM\n"):
                        continue
                    remotes = re.findall(r"^  remote: (\S+)", section, re.M)
                    if remotes and all(r.rstrip("/") == "https://rubygems.org" for r in remotes):
                        for m in re.finditer(r"^    ([A-Za-z0-9_.\-]+) \(([0-9][^)]*)\)$", section, re.M):
                            found.append(("RubyGems", m.group(1), m.group(2).split("-")[0], rel))
                    elif remotes:
                        skipped.append(f"{rel}: fonte de gems própria, não enviada")
            elif name == "packages.lock.json":
                if _nuget_private_feed(path, folder):
                    skipped.append(f"{rel}: feed NuGet próprio configurado, não enviado")
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                for deps in (data.get("dependencies") or {}).values():
                    for pkg, entry in deps.items():
                        if entry.get("resolved") and entry.get("type") != "Project":
                            found.append(("NuGet", pkg, entry["resolved"], rel))
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    return sorted(set(found)), skipped


def _severity(vuln: Dict[str, Any]) -> str:
    sev = ((vuln.get("database_specific") or {}).get("severity") or "").upper()
    return sev if sev in ("CRITICAL", "HIGH", "MODERATE", "MEDIUM", "LOW") else "?"


def _fixed(vuln: Dict[str, Any], name: str, installed: str) -> Optional[str]:
    """The lowest fixed version above the installed one. A flaw is often fixed on several
    branches (2.2.28, 3.2.14, 4.0.6); the first "fixed" event may belong to an older branch."""
    mine = _vkey(installed)
    fixes = []
    for aff in vuln.get("affected") or []:
        if (aff.get("package") or {}).get("name", "").lower() != name.lower():
            continue
        for rng in aff.get("ranges") or []:
            for ev in rng.get("events") or []:
                if ev.get("fixed") and _vkey(str(ev["fixed"])) > mine:
                    fixes.append(str(ev["fixed"]))
    return min(fixes, key=_vkey) if fixes else None


def _clean(text: str, limit: int = 80) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "MEDIUM": 2, "LOW": 3, "?": 4}


def cmd_deps(args, fetch: Fetcher, registry) -> Tuple[int, Dict[str, Any], List[str]]:
    folder = Path(args.pasta)
    if not folder.exists():
        raise FileNotFoundError(args.pasta)
    deps, skipped = read_locks(folder if folder.is_dir() else folder.parent)
    out: Dict[str, Any] = {"pasta": str(folder), "dependencias": len(deps), "consultado_em": date.today().isoformat(),
                           "fontes": [OSV_BATCH, KEV_URL], "falhas": [], "nao_enviados": skipped}
    note = (["Não enviados ao OSV (fonte privada ou não comprovadamente pública): " + "; ".join(skipped[:5])]
            if skipped else [])
    if not deps:
        lines = note + ["Nenhum arquivo de trava com dependências públicas de versão fixa encontrado (composer.lock, package-lock.json, "
                 "requirements com ==, poetry.lock, uv.lock, Cargo.lock, go.mod, Gemfile.lock, packages.lock.json). "
                 "Use a ferramenta da linguagem (npm audit, composer audit, pip-audit) ou gere o lockfile."]
        return OK, out, lines
    queries = [{"package": {"name": n, "ecosystem": e}, "version": v} for e, n, v, _ in deps]
    hits: List[Tuple[int, str]] = []
    for start in range(0, len(queries), 500):
        data = fetch.get_json(OSV_BATCH, "osv", {"queries": queries[start:start + 500]})
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            raise Unchecked("formato do OSV mudou (results ausente)")
        for i, res in enumerate(results):
            for v in (res or {}).get("vulns") or []:
                if v.get("id"):
                    hits.append((start + i, v["id"]))
    kev_ids = set()
    if hits:
        try:
            kev = fetch.get_json(KEV_URL, "kev")
            kev_ids = {v.get("cveID") for v in kev.get("vulnerabilities", []) if v.get("cveID")}
        except Unchecked:
            out["kev"] = "não conferido"
    # Detail calls are one request each: spread them across packages so a package with
    # dozens of flaws does not hide the others.
    by_pkg: Dict[int, List[str]] = {}
    for idx, vid in hits:
        by_pkg.setdefault(idx, []).append(vid)
    order, depth = [], 0
    while len(order) < min(MAX_DETAILS, len(hits)):
        added = False
        for idx, vids in by_pkg.items():
            if depth < len(vids) and len(order) < MAX_DETAILS:
                order.append((idx, vids[depth]))
                added = True
        if not added:
            break
        depth += 1
    rows = []
    for idx, vid in order:
        eco, name, version, rel = deps[idx]
        try:
            vuln = fetch.get_json(OSV_VULN.format(id=urllib.parse.quote(vid)), "osv")
        except Unchecked:
            vuln = {}
        # O CVE pode ser o proprio id do registro, nao so um apelido.
        ids = [vuln.get("id") or vid] + list(vuln.get("aliases") or [])
        aliases = list(dict.fromkeys(str(a) for a in ids if str(a).startswith("CVE-")))
        rows.append({"pacote": name, "versao": version, "ecossistema": eco, "arquivo": rel, "id": vid,
                     "cve": aliases[:2], "gravidade": _severity(vuln), "corrigida_em": _fixed(vuln, name, version),
                     "explorada_ativamente": any(a in kev_ids for a in aliases),
                     "resumo": _clean(vuln.get("summary", ""))})
    rows.sort(key=lambda r: (not r["explorada_ativamente"], SEV_ORDER.get(r["gravidade"], 4), r["pacote"]))
    out["falhas"] = rows
    out["falhas_sem_detalhe"] = max(0, len(hits) - MAX_DETAILS)
    # One line per package: worst severity, how many flaws, the lowest version that fixes all
    # detailed ones, and the most serious id. The full list stays in --json.
    pkgs: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for idx, vid in hits:
        eco, name, version, rel = deps[idx]
        pkgs.setdefault((name, version, rel), {"total": 0, "rows": []})["total"] += 1
    for r in rows:
        pkgs[(r["pacote"], r["versao"], r["arquivo"])]["rows"].append(r)
    summary = []
    for (name, version, rel), info in pkgs.items():
        detailed = info["rows"]
        worst = min((SEV_ORDER.get(r["gravidade"], 4) for r in detailed), default=4)
        kev = any(r["explorada_ativamente"] for r in detailed)
        fixes = [r["corrigida_em"] for r in detailed if r["corrigida_em"]]
        target = max(fixes, key=_vkey) if fixes else None
        top = sorted(detailed, key=lambda r: SEV_ORDER.get(r["gravidade"], 4))[:1]
        summary.append({"pacote": name, "versao": version, "arquivo": rel, "falhas": info["total"],
                        "pior": [k for k, v in SEV_ORDER.items() if v == worst][0], "kev": kev,
                        "atualizar_para": target, "exemplo": top[0]["id"] + (f" {top[0]['cve'][0]}" if top and top[0]["cve"] else "") if top else None})
    summary.sort(key=lambda s: (not s["kev"], SEV_ORDER.get(s["pior"], 4), s["pacote"]))
    out["por_pacote"] = summary
    lines = [f"{len(deps)} dependências fixas lidas; {len(hits)} falhas conhecidas em {len(summary)} pacotes "
             f"(OSV, {out['consultado_em']})."]
    for s in summary:
        tag = " [EXPLORADA ATIVAMENTE, CISA KEV]" if s["kev"] else ""
        fix = f"; atualizar para {s['atualizar_para']} ou mais nova" if s["atualizar_para"] else "; sem versão corrigida informada"
        ex = f"; ex.: {s['exemplo']}" if s["exemplo"] else ""
        lines.append(f"- {s['pior']}{tag} {s['pacote']} {s['versao']} ({s['arquivo']}): {s['falhas']} falhas{fix}{ex}")
    if out["falhas_sem_detalhe"]:
        lines.append(f"({out['falhas_sem_detalhe']} falhas sem detalhe consultado; gravidade e versão acima cobrem só as detalhadas.)")
    return (ACT if hits else OK), out, lines + note


# --------------------------------------------------------------------------- where, list, diagnostics

def cmd_onde(args, fetch, registry):
    key, tech = find_tech(registry, args.tecnologia)
    out = dict(tech, id=key)
    lines = [f"{tech['nome']} (camada {tech.get('camada')}):"]
    if tech.get("eol"):
        lines.append(f"- ciclo de vida: {EOL_URL.format(slug=tech['eol'])}")
    for field, label in (("avisos", "avisos de segurança"), ("notas", "notas de versão"),
                         ("migracao", "guia de migração"), ("estilo", "guia de estilo")):
        if tech.get(field):
            lines.append(f"- {label}: {tech[field]}")
    if tech.get("osv"):
        lines.append(f"- falhas de pacotes: OSV, ecossistema {tech['osv']}")
    return OK, out, lines


def cmd_lista(args, fetch, registry):
    techs = registry["tecnologias"]
    out = {k: {"nome": v["nome"], "camada": v.get("camada")} for k, v in techs.items()}
    a = sorted(k for k, v in techs.items() if v.get("camada") == "A")
    b = sorted(k for k, v in techs.items() if v.get("camada") != "A")
    return OK, out, [f"Camada A (consulta automática): {', '.join(a)}", f"Camada B (só endereço): {', '.join(b)}"]


def cmd_diagnostico(args, fetch: Fetcher, registry):
    """For the scheduled CI canary: every source still answers with the fields this script reads."""
    problems, checked = [], 0
    for key, tech in registry["tecnologias"].items():
        if tech.get("eol"):
            checked += 1
            try:
                data = fetch.get_json(EOL_URL.format(slug=tech["eol"]), "eol")
                rel = data["result"]["releases"][0]
                missing = [f for f in ("name", "isEol", "eolFrom", "isMaintained", "latest") if f not in rel]
                if missing:
                    problems.append(f"{key}: campos ausentes no endoflife.date: {missing}")
            except (Unchecked, KeyError, IndexError, TypeError) as exc:
                problems.append(f"{key}: endoflife.date ({exc})")
    try:
        data = fetch.get_json(OSV_BATCH, "osv", {"queries": [{"package": {"name": "lodash", "ecosystem": "npm"}, "version": "4.17.20"}]})
        if not (data.get("results") or [{}])[0].get("vulns"):
            problems.append("OSV: consulta conhecida (lodash 4.17.20) voltou sem falhas")
    except Unchecked as exc:
        problems.append(f"OSV: {exc}")
    try:
        kev = fetch.get_json(KEV_URL, "kev")
        if not kev.get("vulnerabilities") or "cveID" not in kev["vulnerabilities"][0]:
            problems.append("CISA KEV: formato mudou")
    except Unchecked as exc:
        problems.append(f"CISA KEV: {exc}")
    if args.links:
        for key, tech in registry["tecnologias"].items():
            for field in ("avisos", "notas", "migracao", "estilo"):
                url = tech.get(field)
                if not url:
                    continue
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                        resp.read(1024)
                except Exception as exc:  # noqa: BLE001 - any failure is a finding here
                    problems.append(f"{key}.{field}: {url} ({type(exc).__name__})")
    out = {"tecnologias_conferidas": checked, "problemas": problems}
    lines = [f"{checked} tecnologias com API conferidas; {len(problems)} problemas."] + [f"- {p}" for p in problems]
    return (ACT if problems else OK), out, lines


# --------------------------------------------------------------------------- CLI

def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: Optional[List[str]] = None) -> int:
    _utf8_streams()
    parser = argparse.ArgumentParser(prog="fontes.py", description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--max-chars", type=int, default=1200)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("versao"); p.add_argument("tecnologia"); p.add_argument("--em-uso", default=None)
    p = sub.add_parser("deps"); p.add_argument("pasta")
    p = sub.add_parser("onde"); p.add_argument("tecnologia")
    sub.add_parser("lista")
    p = sub.add_parser("diagnostico"); p.add_argument("--links", action="store_true")
    args = parser.parse_args(argv)
    offline = args.offline or os.environ.get("SECOPS_OFFLINE") == "1"
    fetch = Fetcher(cache_dir(args.cache_dir), offline)
    handlers = {"versao": cmd_versao, "deps": cmd_deps, "onde": cmd_onde, "lista": cmd_lista,
                "diagnostico": cmd_diagnostico}
    try:
        registry = load_registry()
        code, out, lines = handlers[args.cmd](args, fetch, registry)
    except KeyError as exc:
        print(f"Tecnologia não está no registro: {exc}. Veja: fontes.py lista", file=sys.stderr)
        return USAGE
    except FileNotFoundError as exc:
        print(f"Caminho não encontrado: {exc}", file=sys.stderr)
        return USAGE
    except Unchecked as exc:
        msg = f"Não consegui conferir agora ({exc}). Declare como não verificado e indique onde conferir."
        print(json.dumps({"nao_conferido": str(exc)}, ensure_ascii=False) if args.json else msg)
        return UNCHECKED
    if fetch.stale_dates:
        note = f"Atenção: sem acesso à fonte agora; dados do cache de {fetch.oldest_stale()}."
        out["cache_vencido_de"] = fetch.oldest_stale()
        lines.insert(0, note)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        text = "\n".join(lines)
        if len(text) > args.max_chars:
            kept = text[:args.max_chars].rsplit("\n", 1)[0]
            text = kept + f"\n... (saída cortada em {args.max_chars} caracteres; use --json para tudo)"
        print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
