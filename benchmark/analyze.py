"""Measure what each benchmark run produced and aggregate the two conditions.

For every run folder written by run_benchmark.py it measures: files and lines
of code, whether the code builds, security findings from the skill's own
scanner and from Semgrep (an independent tool, when installed), password
hashing, and the tokens, cost and time reported by Claude Code.

Usage:
  python benchmark/analyze.py --runs <folder used as --out> --results benchmark/results
Author: Alex Camacho Castilho
"""
import argparse
import json
import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCANNER = ROOT / "skills" / "principal-secops-dev-token-optimizer" / "scripts" / "revisar_codigo.py"

SOURCE_EXT = {
    "php": {".php"}, "python": {".py"}, "node": {".js", ".mjs", ".cjs", ".ts"},
    "java": {".java"}, "csharp": {".cs"}, "go": {".go"},
}
WEB_EXT = {".html", ".htm", ".css", ".twig", ".ejs", ".cshtml", ".razor", ".tmpl", ".gohtml"}
SKIP_DIRS = {"node_modules", "vendor", "bin", "obj", "target", ".venv", "venv", "__pycache__", "build", "dist", ".git"}
COMMENT = re.compile(r"^\s*(//|#|\*|/\*|\*/|--|<!--)")
STRONG_HASH = re.compile(r"argon2|bcrypt|password_hash\s*\(|PASSWORD_ARGON2|PASSWORD_BCRYPT|scrypt|pbkdf2|Rfc2898DeriveBytes|PasswordHasher", re.I)
WEAK_HASH = re.compile(r"\bmd5\b|\bsha1\b|sha256\(\s*\$?password|hashlib\.sha256\(", re.I)


def files_of(app, exts):
    for path in app.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts and not SKIP_DIRS.intersection(path.relative_to(app).parts):
            yield path


def count_lines(paths):
    total = code = 0
    for path in paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                total += 1
                if not COMMENT.match(line):
                    code += 1
    return total, code


def run(cmd, cwd, timeout=600):
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, shell=isinstance(cmd, str))
        return proc.returncode == 0, round(time.monotonic() - started, 1), (proc.stdout + proc.stderr)[-400:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, round(time.monotonic() - started, 1), repr(exc)


def find_root(app, marker):
    hits = sorted(app.rglob(marker), key=lambda p: len(p.parts))
    hits = [h for h in hits if not SKIP_DIRS.intersection(h.relative_to(app).parts)]
    return hits[0].parent if hits else None


def build_check(lang, app):
    """Return (status, seconds, detail). status is ok, fail or n/a (tool missing)."""
    srcs = list(files_of(app, SOURCE_EXT[lang]))
    if not srcs:
        return "fail", 0, "no source files"
    if lang == "php":
        if not shutil.which("php"):
            return "n/a", 0, "php not installed"
        bad = [p.name for p in srcs if not run(["php", "-l", str(p)], app)[0]]
        return ("fail" if bad else "ok"), 0, ",".join(bad)
    if lang == "python":
        ok, sec, out = run([sys.executable, "-m", "compileall", "-q", str(app)], app)
        return ("ok" if ok else "fail"), sec, out
    if lang == "node":
        if any(p.suffix == ".ts" for p in srcs):
            return "n/a", 0, "TypeScript project"
        bad = [p.name for p in srcs if not run(["node", "--check", str(p)], app)[0]]
        return ("fail" if bad else "ok"), 0, ",".join(bad)
    if lang == "go":
        if not shutil.which("go"):
            return "n/a", 0, "go not installed"
        root = find_root(app, "go.mod")
        if not root:
            return "fail", 0, "no go.mod"
        ok, sec, out = run("go mod tidy && go build ./...", root)
        return ("ok" if ok else "fail"), sec, out
    if lang == "csharp":
        if not shutil.which("dotnet"):
            return "n/a", 0, "dotnet not installed"
        root = find_root(app, "*.csproj")
        if not root:
            return "fail", 0, "no .csproj"
        ok, sec, out = run(["dotnet", "build", "-nologo", "-v", "q"], root)
        return ("ok" if ok else "fail"), sec, out
    if lang == "java":
        pom = find_root(app, "pom.xml")
        if pom and shutil.which("mvn"):
            ok, sec, out = run("mvn -q -B -DskipTests package", pom)
            return ("ok" if ok else "fail"), sec, out
        gradle = find_root(app, "build.gradle") or find_root(app, "build.gradle.kts")
        if gradle and shutil.which("gradle"):
            ok, sec, out = run("gradle -q build -x test", gradle)
            return ("ok" if ok else "fail"), sec, out
        if not shutil.which("javac"):
            return "n/a", 0, "javac not installed"
        if pom or gradle:
            return "n/a", 0, "build tool not installed"
        out_dir = app.parent / "javac-out"
        ok, sec, out = run(["javac", "-d", str(out_dir)] + [str(p) for p in srcs], app)
        return ("ok" if ok else "fail"), sec, out
    return "n/a", 0, ""


def scanner_findings(app):
    proc = subprocess.run([sys.executable, "-I", str(SCANNER), "--json", str(app)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None
    findings = [f for f in data["findings"] if not SKIP_DIRS.intersection(pathlib.Path(f["file"]).parts)]
    return {sev: sum(1 for f in findings if f["severity"] == sev) for sev in ("HIGH", "MEDIUM", "LOW")}


def semgrep_findings(app):
    if not shutil.which("semgrep"):
        return None
    proc = subprocess.run(["semgrep", "scan", "--config", "p/default", "--json", "--quiet",
                           "--metrics", "off", str(app)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None
    sev = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for item in data.get("results", []):
        level = item.get("extra", {}).get("severity", "INFO")
        sev[level] = sev.get(level, 0) + 1
    return sev


def password_hashing(app, lang):
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files_of(app, SOURCE_EXT[lang]))
    if STRONG_HASH.search(text):
        return "strong"
    if WEAK_HASH.search(text):
        return "weak"
    return "none found"


def measure(run_dir):
    record = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    app = run_dir / "app"
    lang = record["lang"]
    srcs = list(files_of(app, SOURCE_EXT[lang]))
    web = list(files_of(app, WEB_EXT))
    all_files = [p for p in app.rglob("*") if p.is_file() and not SKIP_DIRS.intersection(p.relative_to(app).parts)]
    lines, code = count_lines(srcs)
    status, seconds, detail = build_check(lang, app)
    answer = record.get("final_answer") or ""
    record.update({
        "files": len(all_files),
        "source_files": len(srcs),
        "source_lines": lines,
        "source_code_lines": code,
        "web_lines": count_lines(web)[0],
        "build": status, "build_seconds": seconds, "build_detail": detail,
        "scanner": scanner_findings(app),
        "semgrep": semgrep_findings(app),
        "password_hashing": password_hashing(app, lang),
        "answer_words": len(answer.split()),
    })
    record.pop("final_answer", None)
    return record


def mean(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.mean(values), 1) if values else None


def aggregate(records):
    groups = {}
    for r in records:
        groups.setdefault((r["lang"], r["condition"]), []).append(r)
    rows = []
    for (lang, cond), rs in sorted(groups.items()):
        rows.append({
            "lang": lang, "condition": cond, "runs": len(rs),
            "timed_out": sum(1 for r in rs if r.get("timed_out")),
            "skill_used": sum(1 for r in rs if r.get("skill_used")),
            "wall_seconds": mean(r["wall_seconds"] for r in rs),
            "output_tokens": mean(r.get("output_tokens") for r in rs),
            "input_tokens_total": mean((r.get("input_tokens") or 0) + (r.get("cache_creation_input_tokens") or 0)
                                       + (r.get("cache_read_input_tokens") or 0) for r in rs),
            "cost_usd": mean(r.get("cost_usd") for r in rs),
            "num_turns": mean(r.get("num_turns") for r in rs),
            "files": mean(r["files"] for r in rs),
            "source_code_lines": mean(r["source_code_lines"] for r in rs),
            "build_ok": f'{sum(1 for r in rs if r["build"] == "ok")}/{sum(1 for r in rs if r["build"] != "n/a")}',
            "scanner_high": mean((r["scanner"] or {}).get("HIGH") for r in rs),
            "semgrep_findings": mean(sum((r["semgrep"] or {}).values()) if r["semgrep"] is not None else None for r in rs),
            "strong_password_hash": f'{sum(1 for r in rs if r["password_hashing"] == "strong")}/{len(rs)}',
            "answer_words": mean(r["answer_words"] for r in rs),
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", required=True)
    parser.add_argument("--results", default=str(ROOT / "benchmark" / "results"))
    args = parser.parse_args()
    records = [measure(p.parent) for p in sorted(pathlib.Path(args.runs).rglob("run.json"))]
    out = pathlib.Path(args.results)
    out.mkdir(parents=True, exist_ok=True)
    (out / "runs.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    rows = aggregate(records)
    (out / "summary.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
