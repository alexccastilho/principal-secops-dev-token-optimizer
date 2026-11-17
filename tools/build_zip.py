"""Build the claude.ai upload ZIP: dist/<skill>-v<version>.zip with the skill folder at the ZIP root.

Usage: python tools/build_zip.py
Author: Alex Camacho Castilho
"""
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = "principal-secops-dev-token-optimizer"
SKILL_DIR = ROOT / "skills" / SKILL
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def main() -> None:
    version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / f"{SKILL}-v{version}.zip"
    files = sorted(
        p for p in SKILL_DIR.rglob("*")
        if p.is_file()
        and not EXCLUDE_DIRS.intersection(p.relative_to(SKILL_DIR).parts)
        and p.suffix not in EXCLUDE_SUFFIXES
    )
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            arcname = f"{SKILL}/{p.relative_to(SKILL_DIR).as_posix()}"
            zf.write(p, arcname)
    print(f"{out} ({len(files)} files, {out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
