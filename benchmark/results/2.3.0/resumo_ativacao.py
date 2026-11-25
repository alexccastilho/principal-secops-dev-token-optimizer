"""Usage: python resumo_ativacao.py <bench folder>. Activation per prompt and per condition, plus the refactor-suite activation, and gate 5."""
import collections
import glob
import json
import sys

B = sys.argv[1] if len(sys.argv) > 1 else "."  # folder that holds out-activation and out-refactor
per = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for f in glob.glob(B + "/out-activation/**/run.json", recursive=True):
    r = json.load(open(f, encoding="utf-8"))
    per[r["task"]][r["condition"]][0] += bool(r["skill_used"])
    per[r["task"]][r["condition"]][1] += 1
ref = collections.defaultdict(lambda: [0, 0])
for f in glob.glob(B + "/out-refactor/**/run.json", recursive=True):
    r = json.load(open(f, encoding="utf-8"))
    ref[(r["task"], r["condition"])][0] += bool(r.get("skill_used"))
    ref[(r["task"], r["condition"])][1] += 1

conds = ["baseline", "v221", "v23"]
print("prompt | " + " | ".join(conds))
for task in sorted(per):
    print(task, "|", " | ".join("%d/%d" % tuple(per[task][c]) for c in conds))
for task in ("review", "bugfix"):
    print(task, "|", " | ".join("%d/%d" % tuple(ref[(task, c)]) for c in conds))


def tot(tasks, c):
    a = sum(per[t][c][0] for t in tasks); n = sum(per[t][c][1] for t in tasks)
    return a, n


g5a = ref[("bugfix", "v23")]
g5b = tot(["a04", "a05", "a07", "a08", "a10"], "v23")
c_ok = tot(["a01", "a02", "a03", "a06", "a09"], "v23")
g5c = (c_ok[0] + ref[("review", "v23")][0], c_ok[1] + ref[("review", "v23")][1])
g5d = tot(["n01", "n02", "n03", "n04"], "v23")
print("\n5a bugfix v23 > 0/6:", "%d/%d" % tuple(g5a), "PASSA" if g5a[0] > 0 else "FALHA")
print("5b a04,a05,a07,a08,a10 v23 > 2/20:", "%d/%d" % g5b, "PASSA" if g5b[0] > 2 else "FALHA")
print("5c sem regressão >= 23/26:", "%d/%d" % g5c, "PASSA" if g5c[0] >= 23 else "FALHA")
print("5d falso positivo 0/16:", "%d/%d" % g5d, "PASSA" if g5d[0] == 0 else "FALHA")
