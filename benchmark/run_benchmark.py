"""Run the same requests through Claude Code with and without the skill.

Two suites:
  create    the same small app built from an empty folder (one request per language);
  refactor  existing code in benchmark/refactor/fixtures/<lang>: review it, fix one bug,
            and refactor the whole project (three requests per language).

Each run starts in an empty folder, in a clean Claude Code configuration (no user
plugins, skills, memory or CLAUDE.md), so the only difference between the two
conditions is the plugin loaded with --plugin-dir.

Usage:
  python benchmark/run_benchmark.py --config-dir <clean CLAUDE_CONFIG_DIR> --out <folder>
      [--suite create|refactor] [--langs php,python,node,java,csharp,go]
      [--tasks review,bugfix,refactor] [--reps 3] [--model sonnet] [--jobs 3]

The clean config dir must hold only the login (.credentials.json). Everything
the runs produce goes to --out, never into the repository.
Author: Alex Camacho Castilho
"""
import argparse
import concurrent.futures
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent

LANGS = {
    "php": "PHP",
    "python": "Python",
    "node": "JavaScript com Node.js",
    "java": "Java",
    "csharp": "C# com .NET",
    "go": "Go",
}

# The intake questions of projeto-do-zero.md are answered up front, so both
# conditions can deliver code in one non-interactive turn.
PROMPT = (
    "Preciso de um sistema simples em {lang} para cadastrar meus contatos (nome, e-mail e "
    "telefone), com login de usuário e senha, salvando num banco SQLite. Vai rodar só no meu "
    "computador com Windows, é tudo do zero, só eu vou usar, e guarda dado pessoal (nome, "
    "e-mail e telefone). Crie os arquivos nesta pasta e me diga como rodar. Não sou programador."
)

REFACTOR_DIR = ROOT / "benchmark" / "refactor"
REFACTOR_LANGS = ("python", "node")

# Requests of the refactor suite, as a project owner would write them. The refactor
# request says the project is already in Git with a clean tree, which the skill's
# refactor mode checks before it starts; it does not pre-answer anything else.
TASK_PROMPTS = {
    "review": ("Revise o código deste projeto e me diga quais problemas ele tem, do mais grave "
               "para o menos grave. Não altere nenhum arquivo."),
    "bugfix": ("Um cliente fez um pedido de exatamente R$ 500,00 e não recebeu o desconto de 10% "
               "que a regra da loja promete. Corrija isso."),
    "refactor": ("Refatore este projeto inteiro para ficar mais fácil de manter, sem mudar o "
                 "comportamento. O projeto já está no Git, com a árvore limpa."),
}

# When a session ends on a question (the skill's refactor mode asks for "pode" before it
# starts, before the plan and before deleting tests), the harness answers with this text.
# Both conditions get the same reply under the same rule, up to MAX_REPLIES times.
AUTO_REPLY = ("Pode seguir com tudo o que você propôs, sem as adições opcionais. "
              "Não precisa me perguntar mais nada; decida você.")
MAX_REPLIES = 3

# Extra commands the refactor suite needs: the project's own tests and the git steps a
# refactor uses. No git command that rewrites history or talks to a remote.
REFACTOR_TOOLS = (" Bash(node --test:*) Bash(node cli.js:*) Bash(git status:*) Bash(git diff:*) "
                  "Bash(git log:*) Bash(git show:*) Bash(git add:*) Bash(git commit:*) "
                  "Bash(git checkout -b:*) Bash(git switch -c:*) Bash(git branch:*) "
                  "Bash(git mv:*) Bash(git rm:*)")

# On Windows "claude" is often a .cmd shim, which a list argv cannot start by name.
CLAUDE = shutil.which("claude") or "claude"


def _commit():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "skills"],
                               capture_output=True, text=True).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None


SKILL_COMMIT = _commit()

# Both conditions may look a version up (the skill's rules require it) and run the language's
# own quick checks; neither may install packages, so the build check stays comparable.
# The published 2.2.0 numbers were measured at commit b723084, which also allowed
# Bash(curl:*), unrestricted WebFetch and Bash(go vet:*). This narrower list keeps network
# fetches to version sources. It narrows, but does not enforce, outbound traffic: the
# interpreters stay allowed (the generated apps are tested with them) and can open
# connections. Run unattended benchmarks in a sandbox or VM with egress limited to the
# Anthropic API and these hosts, holding no credentials other than the benchmark login.
ALLOWED_TOOLS = ("Read Write Edit Glob Grep Skill WebSearch WebFetch(domain:endoflife.date) "
                 "WebFetch(domain:registry.npmjs.org) WebFetch(domain:pypi.org) WebFetch(domain:packagist.org) "
                 "WebFetch(domain:www.php.net) WebFetch(domain:go.dev) WebFetch(domain:learn.microsoft.com) "
                 "WebFetch(domain:www.nuget.org) WebFetch(domain:search.maven.org) "
                 "Bash(python:*) Bash(py:*) Bash(python3:*) Bash(node --version) Bash(node -v) "
                 "Bash(php -v) Bash(php -l:*) Bash(go version) Bash(dotnet --version) Bash(dotnet --list-sdks) "
                 "Bash(java -version) Bash(javac -version)")

# Only what Claude Code and the toolchains need; tokens and keys in the caller's
# environment are not handed to the run.
ENV_KEEP = {"PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP",
            "USERPROFILE", "USERNAME", "HOMEDRIVE", "HOMEPATH", "HOME", "APPDATA", "LOCALAPPDATA",
            "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA", "PROGRAMW6432", "COMMONPROGRAMFILES",
            "JAVA_HOME", "GOPATH", "GOROOT", "DOTNET_ROOT", "LANG", "LC_ALL", "TERM", "SHELL", "OS",
            "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS"}


def long_path(path):
    """Expand Windows 8.3 short names (ALEXCA~1): Claude Code asks for approval to write
    to a path containing "~", which a non-interactive run can never give."""
    path = str(pathlib.Path(path).resolve())
    if os.name == "nt" and "~" in path:
        import ctypes
        buf = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.kernel32.GetLongPathNameW(path, buf, len(buf)):
            path = buf.value
    return path


def export_plugin(out):
    """Copy only the plugin (manifest, commands, skill) to a folder outside the repository,
    so the skill condition cannot reach the benchmark's fixtures, answer key or results."""
    dest = pathlib.Path(long_path(out)) / "_plugin"
    if dest.exists():
        shutil.rmtree(dest)
    for part in (".claude-plugin", "commands", "skills"):
        shutil.copytree(ROOT / part, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def prepare_fixture(lang, app):
    """Copy the fixture and make it a Git repository with one commit, under a generic
    identity so no personal name or e-mail lands in the run's history."""
    shutil.copytree(REFACTOR_DIR / "fixtures" / lang, app, dirs_exist_ok=True)
    ident = ["-c", "user.name=Loja", "-c", "user.email=loja@example.invalid", "-c", "commit.gpgsign=false"]
    for step in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "Versão atual"]):
        subprocess.run(["git", *ident, *step], cwd=app, check=True, capture_output=True)


def ends_with_question(text):
    tail = (text or "").strip().split("\n\n")[-1]
    return "?" in tail


def run_one(lang, condition, rep, args, task=None):
    base = pathlib.Path(long_path(args.out)) / lang
    work = (base / task if task else base) / condition / f"r{rep}"
    app = work / "app"
    transcript = work / "transcript.jsonl"
    if (work / "run.json").exists():
        return json.loads((work / "run.json").read_text(encoding="utf-8"))
    if app.exists():
        shutil.rmtree(app)
    app.mkdir(parents=True)
    if task:
        prepare_fixture(lang, app)
        prompt, tools = TASK_PROMPTS[task], ALLOWED_TOOLS + REFACTOR_TOOLS
    else:
        prompt, tools = PROMPT.format(lang=LANGS[lang]), ALLOWED_TOOLS
    session = str(uuid.uuid4())
    cmd = [
        CLAUDE, "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        "--strict-mcp-config",
        "--model", args.model,
        "--permission-mode", "acceptEdits",
        "--allowedTools", tools,
    ]
    cmd += ["--session-id", session] if task else ["--no-session-persistence"]
    if condition == "skill":
        cmd += ["--plugin-dir", str(args.plugin_dir)]
    # The account also syncs skills uploaded to claude.ai (an older copy of this skill among
    # them) into any config dir. Turning off non-essential traffic stops that sync, so the
    # baseline sees no copy of the skill and the skill condition sees only --plugin-dir.
    base_env = {k: v for k, v in os.environ.items() if k.upper() in ENV_KEEP}
    env = dict(base_env, CLAUDE_CONFIG_DIR=long_path(args.config_dir),
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    started = time.monotonic()
    timed_out, replies = False, 0
    with transcript.open("w", encoding="utf-8") as out:
        while True:
            remaining = args.timeout - (time.monotonic() - started)
            try:
                proc = subprocess.run(cmd, cwd=app, env=env, stdout=out, stderr=subprocess.PIPE,
                                      text=True, encoding="utf-8", errors="replace",
                                      timeout=max(remaining, 1))
                exit_code, stderr = proc.returncode, proc.stderr
            except subprocess.TimeoutExpired as exc:
                # A run that hits the limit stays in the results, marked, instead of vanishing.
                timed_out, exit_code = True, None
                stderr = exc.stderr if isinstance(exc.stderr, str) else ""
                break
            out.flush()
            last = parse_transcript(transcript).get("final_answer", "")
            if not task or replies >= MAX_REPLIES or exit_code != 0 or not ends_with_question(last):
                break
            replies += 1
            cmd = [c for c in cmd if c not in ("--session-id", session)]
            cmd[2] = AUTO_REPLY
            cmd += ["--resume", session]
    wall = time.monotonic() - started
    record = {"lang": lang, "task": task, "condition": condition, "rep": rep, "exit_code": exit_code,
              "timed_out": timed_out, "auto_replies": replies, "skill_commit": SKILL_COMMIT,
              "wall_seconds": round(wall, 1), "stderr_tail": (stderr or "")[-500:]}
    record.update(parse_transcript(transcript, app=app, plugin=args.plugin_dir))
    (work / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{lang:7} {task or '':8} {condition:8} r{rep} exit={exit_code} {wall:6.0f}s replies={replies} "
          f"skill_used={record.get('skill_used')} out_tokens={record.get('output_tokens')}", flush=True)
    return record


def _where(path_text, app, plugin):
    """Classify a path an agent touched: the project, the skill, or somewhere else."""
    if not path_text:
        return "none"
    norm = os.path.normcase(os.path.abspath(path_text if os.path.isabs(path_text)
                                            else os.path.join(str(app or "."), path_text)))
    for name, root in (("project", app), ("skill", plugin)):
        if root and norm.startswith(os.path.normcase(os.path.abspath(str(root)))):
            return name
    return "outside"


def parse_transcript(path, app=None, plugin=None):
    results, skill_used, tools, init_skills, skill_names = [], False, {}, None, []
    pending, reads = {}, {"project": [0, 0], "skill": [0, 0], "outside": [0, 0], "none": [0, 0]}
    outside_paths = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tools[block["name"]] = tools.get(block["name"], 0) + 1
                    inp = block.get("input", {}) or {}
                    if block["name"] == "Skill" and "principal-secops" in json.dumps(inp):
                        skill_used = True
                        skill_names.append(inp.get("skill"))
                    if block["name"] in ("Read", "Grep", "Glob"):
                        where = _where(inp.get("file_path") or inp.get("path"), app, plugin)
                        pending[block.get("id")] = where
                        if where == "outside":
                            outside_paths.append(inp.get("file_path") or inp.get("path"))
        if event.get("type") == "user":
            content = event.get("message", {}).get("content")
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_result" and block.get("tool_use_id") in pending:
                    body = block.get("content")
                    size = len(body if isinstance(body, str) else json.dumps(body, ensure_ascii=False))
                    bucket = reads[pending.pop(block["tool_use_id"])]
                    bucket[0] += 1
                    bucket[1] += size
        if event.get("type") == "system" and event.get("subtype") == "init":
            init_skills = [s for s in (event.get("skills") or []) if "secops" in str(s)]
        if event.get("type") == "result":
            results.append(event)

    def total(key, sub=None):
        vals = [(r.get("usage", {}) if sub else r).get(key) for r in results]
        vals = [v for v in vals if v is not None]
        return sum(vals) if vals else None

    result = results[-1] if results else {}
    usage = {k: total(k, True) for k in ("input_tokens", "cache_creation_input_tokens",
                                         "cache_read_input_tokens", "output_tokens")}
    return {
        "skill_used": skill_used,
        "secops_skills_loaded": init_skills,
        "skill_names_called": skill_names,
        "tool_calls": tools,
        "duration_ms": total("duration_ms"),
        "num_turns": total("num_turns"),
        "cost_usd": total("total_cost_usd"),
        "sessions": len(results),
        "read_calls": {k: v[0] for k, v in reads.items()},
        "read_chars": {k: v[1] for k, v in reads.items()},
        "outside_paths": outside_paths[:20],
        "answers": [r.get("result", "") for r in results],
        "input_tokens": usage.get("input_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "final_answer": result.get("result", ""),
        "is_error": result.get("is_error"),
        "model_usage": result.get("modelUsage"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--langs", default=",".join(LANGS))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=1500)
    parser.add_argument("--suite", choices=("create", "refactor"), default="create")
    parser.add_argument("--tasks", default=",".join(TASK_PROMPTS))
    args = parser.parse_args()
    if args.suite == "refactor" and args.langs == ",".join(LANGS):
        args.langs = ",".join(REFACTOR_LANGS)
    pathlib.Path(args.out).mkdir(parents=True, exist_ok=True)
    if pathlib.Path(args.out).resolve().is_relative_to(ROOT):
        sys.exit("--out must be outside the repository")
    if "~" in long_path(args.out):
        sys.exit("--out must not contain '~' (Windows short name); pass the long path")
    args.plugin_dir = export_plugin(args.out)
    tasks = args.tasks.split(",") if args.suite == "refactor" else [None]
    jobs = [(lang, cond, rep, task) for rep in range(1, args.reps + 1) for task in tasks
            for lang in args.langs.split(",") for cond in ("baseline", "skill")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, lang, cond, rep, args, task) for lang, cond, rep, task in jobs]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:  # one failed run must not stop the others
                print(f"run failed: {exc!r}", flush=True)


if __name__ == "__main__":
    main()
