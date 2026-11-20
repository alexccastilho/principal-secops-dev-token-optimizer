"""Run the same small app request through Claude Code with and without the skill.

Each run starts in an empty folder, in a clean Claude Code configuration (no user
plugins, skills, memory or CLAUDE.md), so the only difference between the two
conditions is the plugin loaded with --plugin-dir.

Usage:
  python benchmark/run_benchmark.py --config-dir <clean CLAUDE_CONFIG_DIR> --out <folder>
      [--langs php,python,node,java,csharp,go] [--reps 3] [--model sonnet] [--jobs 3]

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


def run_one(lang, condition, rep, args):
    work = pathlib.Path(long_path(args.out)) / lang / condition / f"r{rep}"
    app = work / "app"
    app.mkdir(parents=True, exist_ok=True)
    transcript = work / "transcript.jsonl"
    if (work / "run.json").exists():
        return json.loads((work / "run.json").read_text(encoding="utf-8"))
    cmd = [
        CLAUDE, "-p", PROMPT.format(lang=LANGS[lang]),
        "--output-format", "stream-json", "--verbose",
        "--no-session-persistence", "--strict-mcp-config",
        "--model", args.model,
        "--permission-mode", "acceptEdits",
        "--allowedTools", ALLOWED_TOOLS,
    ]
    if condition == "skill":
        cmd += ["--plugin-dir", str(ROOT)]
    # The account also syncs skills uploaded to claude.ai (an older copy of this skill among
    # them) into any config dir. Turning off non-essential traffic stops that sync, so the
    # baseline sees no copy of the skill and the skill condition sees only --plugin-dir.
    base_env = {k: v for k, v in os.environ.items() if k.upper() in ENV_KEEP}
    env = dict(base_env, CLAUDE_CONFIG_DIR=long_path(args.config_dir),
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    started = time.monotonic()
    timed_out = False
    with transcript.open("w", encoding="utf-8") as out:
        try:
            proc = subprocess.run(cmd, cwd=app, env=env, stdout=out, stderr=subprocess.PIPE,
                                  text=True, encoding="utf-8", errors="replace", timeout=args.timeout)
            exit_code, stderr = proc.returncode, proc.stderr
        except subprocess.TimeoutExpired as exc:
            # A run that hits the limit stays in the results, marked, instead of vanishing.
            timed_out, exit_code = True, None
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
    wall = time.monotonic() - started
    record = {"lang": lang, "condition": condition, "rep": rep, "exit_code": exit_code,
              "timed_out": timed_out, "skill_commit": SKILL_COMMIT,
              "wall_seconds": round(wall, 1), "stderr_tail": (stderr or "")[-500:]}
    record.update(parse_transcript(transcript))
    (work / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{lang:7} {condition:8} r{rep} exit={exit_code} {wall:6.0f}s "
          f"skill_used={record.get('skill_used')} out_tokens={record.get('output_tokens')}", flush=True)
    return record


def parse_transcript(path):
    result, skill_used, tools, init_skills, skill_names = {}, False, {}, None, []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tools[block["name"]] = tools.get(block["name"], 0) + 1
                    if block["name"] == "Skill" and "principal-secops" in json.dumps(block.get("input", {})):
                        skill_used = True
                        skill_names.append(block.get("input", {}).get("skill"))
        if event.get("type") == "system" and event.get("subtype") == "init":
            init_skills = [s for s in (event.get("skills") or []) if "secops" in str(s)]
        if event.get("type") == "result":
            result = event
    usage = result.get("usage", {})
    return {
        "skill_used": skill_used,
        "secops_skills_loaded": init_skills,
        "skill_names_called": skill_names,
        "tool_calls": tools,
        "duration_ms": result.get("duration_ms"),
        "num_turns": result.get("num_turns"),
        "cost_usd": result.get("total_cost_usd"),
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
    args = parser.parse_args()
    pathlib.Path(args.out).mkdir(parents=True, exist_ok=True)
    if pathlib.Path(args.out).resolve().is_relative_to(ROOT):
        sys.exit("--out must be outside the repository")
    if "~" in long_path(args.out):
        sys.exit("--out must not contain '~' (Windows short name); pass the long path")
    jobs = [(lang, cond, rep) for rep in range(1, args.reps + 1)
            for lang in args.langs.split(",") for cond in ("baseline", "skill")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, *job, args) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:  # one failed run must not stop the others
                print(f"run failed: {exc!r}", flush=True)


if __name__ == "__main__":
    main()
