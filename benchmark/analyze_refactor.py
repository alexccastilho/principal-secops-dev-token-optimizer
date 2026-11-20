"""Measure the runs of the refactor suite (benchmark/run_benchmark.py --suite refactor).

For each run it checks, against the pristine fixture and the hidden tests:
  - the project's tests as the agent left them, and the original visible tests;
  - the hidden contract tests (public API unchanged) and the hidden bug-fix test;
  - the size of the change (files and lines against the pristine fixture);
  - the scanner's HIGH findings before and after;
  - tokens, cost, time, turns and how much of the project and of the skill was read.
It also writes anonymized review answers for a blind grader (review_packets/).

Usage:
  python benchmark/analyze_refactor.py --runs <out folder> [--results benchmark/results/refactor]
Author: Alex Camacho Castilho
"""
import argparse
import json
import os
import pathlib
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFACTOR = ROOT / "benchmark" / "refactor"
SCANNER = ROOT / "skills" / "principal-secops-dev-token-optimizer" / "scripts" / "revisar_codigo.py"
SKIP = {".git", "__pycache__", "node_modules"}
SOURCE_EXT = {"python": {".py"}, "node": {".js", ".cjs", ".mjs"}}


def run(cmd, cwd, env=None, timeout=600):
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        return proc.returncode, proc.stdout + proc.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, repr(exc)


def counts(lang, rc, out):
    """(passed, failed) from unittest or node:test output; None when nothing ran."""
    if lang == "python":
        ran = re.search(r"Ran (\d+) tests?", out)
        if not ran:
            return None
        total = int(ran.group(1))
        bad = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", out))
        return total - bad, bad
    passed = re.search(r"^# pass (\d+)", out, re.M)
    failed = re.search(r"^# fail (\d+)", out, re.M)
    if not passed:
        return None
    return int(passed.group(1)), int(failed.group(1)) if failed else 0


def project_copy(app):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="refbench-"))
    dest = tmp / "app"
    shutil.copytree(app, dest, ignore=shutil.ignore_patterns(*SKIP, "*.db", "*.sqlite*"))
    return dest


def visible_tests(lang, project):
    cmd = ([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."]
           if lang == "python" else ["node", "--test", "--test-reporter=tap", "tests/"])
    return counts(lang, *run(cmd, project))


def original_tests(lang, app):
    """The fixture's visible tests, untouched, against the agent's code."""
    project = project_copy(app)
    if (project / "tests").exists():
        shutil.rmtree(project / "tests")
    shutil.copytree(REFACTOR / "fixtures" / lang / "tests", project / "tests")
    try:
        return visible_tests(lang, project)
    finally:
        shutil.rmtree(project.parent, ignore_errors=True)


def hidden_test(lang, app, name):
    hidden = REFACTOR / "hidden" / lang
    env = dict(os.environ, PROJECT_ROOT=str(app))
    cmd = ([sys.executable, "-B", "-m", "unittest", f"test_{name}"] if lang == "python"
           else ["node", "--test", "--test-reporter=tap", f"{name}.test.js"])
    return counts(lang, *run(cmd, hidden, env))


def files_of(folder, lang):
    for p in sorted(folder.rglob("*")):
        if p.is_file() and not SKIP.intersection(p.relative_to(folder).parts) \
                and not p.name.endswith((".db", ".sqlite", ".sqlite3")):
            yield p


def source_lines(folder, lang):
    total = 0
    for p in files_of(folder, lang):
        rel = p.relative_to(folder).parts
        if p.suffix in SOURCE_EXT[lang] and "tests" not in rel:
            total += sum(1 for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
    return total


def change_size(lang, app):
    """Files and lines changed against the pristine fixture (not the agent's own git state)."""
    before = {p.relative_to(REFACTOR / "fixtures" / lang).as_posix(): p
              for p in files_of(REFACTOR / "fixtures" / lang, lang)}
    after = {p.relative_to(app).as_posix(): p for p in files_of(app, lang)}
    import difflib
    touched, added, removed = 0, 0, 0
    for rel in sorted(set(before) | set(after)):
        a = before[rel].read_text(encoding="utf-8", errors="replace").splitlines() if rel in before else []
        b = after[rel].read_text(encoding="utf-8", errors="replace").splitlines() if rel in after else []
        if a == b:
            continue
        touched += 1
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
    return {"files_touched": touched, "lines_added": added, "lines_removed": removed,
            "files_created": len(set(after) - set(before)), "files_deleted": len(set(before) - set(after))}


def scanner_high(folder):
    rc, out = run([sys.executable, "-I", str(SCANNER), "--json", str(folder)], folder)
    try:
        data = json.loads(out[out.index("{"):])
    except ValueError:
        return None
    return sum(1 for f in data["findings"] if f["severity"] == "HIGH"
               and not SKIP.intersection(pathlib.Path(f["file"]).parts))


def measure(run_dir):
    rec = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    app = run_dir / "app"
    lang = rec["lang"]
    project = project_copy(app)
    try:
        rec["tests_as_left"] = visible_tests(lang, project)
    finally:
        shutil.rmtree(project.parent, ignore_errors=True)
    rec["tests_original"] = original_tests(lang, app)
    rec["contract"] = hidden_test(lang, app, "contract")
    rec["bugfix"] = hidden_test(lang, app, "bugfix")
    rec.update(change_size(lang, app))
    rec["source_lines"] = source_lines(app, lang)
    rec["scanner_high"] = scanner_high(app)
    rec["report_file"] = any((app / n).exists() for n in ("REFATORACAO.md", "REFACTORING.md"))
    rec["answer_words"] = len(" ".join(rec.get("answers") or []).split())
    return rec


def ok(result):
    return bool(result) and result[1] == 0 and result[0] > 0


def mean(values, digits=1):
    values = [v for v in values if v is not None]
    return round(statistics.mean(values), digits) if values else None


def aggregate(records):
    groups = {}
    for r in records:
        groups.setdefault((r["lang"], r["task"], r["condition"]), []).append(r)
    rows = []
    for (lang, task, cond), rs in sorted(groups.items()):
        rows.append({
            "lang": lang, "task": task, "condition": cond, "runs": len(rs),
            "skill_not_used": sum(1 for r in rs if cond == "skill" and not r.get("skill_used")),
            "contaminated": sum(1 for r in rs if cond == "baseline" and r.get("skill_used")),
            "read_outside": sum(1 for r in rs if r.get("outside_paths")),
            "timed_out": sum(1 for r in rs if r.get("timed_out")),
            "wall_seconds": mean(r["wall_seconds"] for r in rs),
            "output_tokens": mean(r.get("output_tokens") for r in rs),
            "input_tokens_total": mean(sum((r.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                                     "cache_read_input_tokens")) for r in rs),
            "cost_usd": mean((r.get("cost_usd") for r in rs), 3),
            "num_turns": mean(r.get("num_turns") for r in rs),
            "auto_replies": mean(r.get("auto_replies") for r in rs),
            "project_chars_read": mean(r["read_chars"]["project"] for r in rs),
            "skill_chars_read": mean(r["read_chars"]["skill"] for r in rs),
            "project_reads": mean(r["read_calls"]["project"] for r in rs),
            "files_touched": mean(r["files_touched"] for r in rs),
            "lines_changed": mean(r["lines_added"] + r["lines_removed"] for r in rs),
            "source_lines": mean(r["source_lines"] for r in rs),
            "scanner_high": mean(r["scanner_high"] for r in rs),
            "original_tests_pass": f"{sum(ok(r['tests_original']) for r in rs)}/{len(rs)}",
            "contract_pass": f"{sum(ok(r['contract']) for r in rs)}/{len(rs)}",
            "bugfix_pass": f"{sum(ok(r['bugfix']) for r in rs)}/{len(rs)}",
            "report_file": sum(1 for r in rs if r["report_file"]),
            "answer_words": mean(r["answer_words"] for r in rs),
        })
    return rows


def review_packets(records, out):
    """Anonymized review answers, one folder per language, for a blind grader."""
    rnd = random.Random(20261120)
    key = {}
    for lang in sorted({r["lang"] for r in records}):
        rs = [r for r in records if r["lang"] == lang and r["task"] == "review"]
        rnd.shuffle(rs)
        for i, r in enumerate(rs, 1):
            label = f"{lang}-{i:02d}"
            key[label] = {"condition": r["condition"], "rep": r["rep"]}
            path = out / "review_packets" / f"{label}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n\n".join(r.get("answers") or []), encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    (out / "review_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", required=True)
    parser.add_argument("--results", default=str(ROOT / "benchmark" / "results" / "refactor"))
    args = parser.parse_args()
    runs = sorted(pathlib.Path(args.runs).glob("*/*/*/r*/run.json"))
    records = [measure(p.parent) for p in runs]
    out = pathlib.Path(args.results)
    out.mkdir(parents=True, exist_ok=True)
    slim = [{k: v for k, v in r.items() if k not in ("answers", "final_answer", "model_usage")} for r in records]
    (out / "runs.json").write_text(json.dumps(slim, indent=1, ensure_ascii=False), encoding="utf-8")
    rows = aggregate(records)
    (out / "summary.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    review_packets(records, pathlib.Path(args.runs) / "_grading")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
