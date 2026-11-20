"""Offline proof that the refactor fixtures, hidden tests, references and answer key agree.

Usage: python benchmark/refactor/validate.py [python,node]
Exit code 0 when every check passes for every language.
Author: Alex Camacho Castilho
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze_refactor as ar  # noqa: E402

TELLS = re.compile(r"vulner|inseguro|benchmark|planted|TODO|FIXME|\bbug", re.I)


def check(lang):
    fx = HERE / "fixtures" / lang
    refs = {"bugfix": HERE / "reference" / lang / "bugfix", "refactor": HERE / "reference" / lang / "refactor"}
    problems = []

    vis = ar.visible_tests(lang, fx)
    if not ar.ok(vis) or not 25 <= sum(vis) <= 40:
        problems.append(f"visible tests on fixture: {vis} (need all passing, 25-40)")
    for name, folder in [("fixture", fx)] + list(refs.items()):
        res = ar.hidden_test(lang, folder, "contract")
        if not ar.ok(res):
            problems.append(f"contract on {name}: {res}")
    res = ar.hidden_test(lang, fx, "bugfix")
    if ar.ok(res) or res is None:
        problems.append(f"bugfix should fail on fixture: {res}")
    res = ar.hidden_test(lang, refs["bugfix"], "bugfix")
    if not ar.ok(res):
        problems.append(f"bugfix on reference/bugfix: {res}")
    contract_count = ar.hidden_test(lang, fx, "contract")
    if contract_count and not 30 <= sum(contract_count) <= 50:
        problems.append(f"contract has {sum(contract_count)} tests (need 30-50)")

    for p in ar.files_of(fx, lang):
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if TELLS.search(line):
                problems.append(f"tell word in {p.relative_to(fx)}:{n}: {line.strip()[:80]}")

    size = ar.source_lines(fx, lang)
    if not 2500 <= size <= 3500:
        problems.append(f"source lines {size} (need 2500-3500)")
    if ar.source_lines(refs["refactor"], lang) == size and ar.change_size(lang, refs["refactor"])["files_touched"] < 5:
        problems.append("reference/refactor is barely restructured")

    manifest = json.loads((HERE / "manifest" / f"{lang}.json").read_text(encoding="utf-8"))
    ids = {m["id"] for m in manifest}
    need = {f"S{i}" for i in range(1, 9)} | {f"Q{i}" for i in range(1, 5)} | {"B1"}
    if need - ids:
        problems.append(f"manifest missing {sorted(need - ids)}")
    rc, out = ar.run([sys.executable, "-I", str(ar.SCANNER), "--json", str(fx)], fx)
    findings = json.loads(out[out.index("{"):])["findings"]
    for m in manifest:
        hit = any(pathlib.Path(f["file"]).as_posix().endswith(loc["path"]) and
                  loc["lines"][0] <= f["line"] <= loc["lines"][1]
                  for f in findings for loc in m["files"])
        if hit != bool(m["scanner_detectable"]):
            problems.append(f"{m['id']}: scanner_detectable={m['scanner_detectable']} but scanner hit={hit}")
    return size, problems


def main():
    langs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["python", "node"]
    failed = False
    for lang in langs:
        size, problems = check(lang)
        print(f"{lang}: {size} source lines, {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
        for p in problems:
            print("  -", p)
        failed = failed or bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
