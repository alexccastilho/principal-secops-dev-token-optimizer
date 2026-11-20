"""Consistency of the repository: versions, skill wiring, evals, translations, docs style, package.

Run: python -m unittest discover -s tests
Author: Alex Camacho Castilho
"""
import importlib.util
import json
import pathlib
import re
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_NAME = "principal-secops-dev-token-optimizer"
SKILL_DIR = ROOT / "skills" / SKILL_NAME
SKILL_MD = SKILL_DIR / "SKILL.md"

LANG_DOCS = {
    "README": (ROOT / "README.md", ROOT / "docs" / "README.pt-BR.md", ROOT / "docs" / "README.es.md"),
    "CHANGELOG": (ROOT / "CHANGELOG.md", ROOT / "docs" / "CHANGELOG.pt-BR.md", ROOT / "docs" / "CHANGELOG.es.md"),
    "CONTRIBUTING": (ROOT / "CONTRIBUTING.md", ROOT / "docs" / "CONTRIBUTING.pt-BR.md", ROOT / "docs" / "CONTRIBUTING.es.md"),
}
STYLE_CHECKED = [p for trio in LANG_DOCS.values() for p in trio] + [
    ROOT / "SECURITY.md",
    SKILL_DIR / "THIRD_PARTY_NOTICES.md",
    SKILL_DIR / "SKILL.md",
    ROOT / "commands" / "secops-refatorar.md",
] + sorted((SKILL_DIR / "references").glob("*.md"))


def read(path):
    return path.read_text(encoding="utf-8")


def frontmatter(path):
    text = read(path)
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError(f"{path} has no frontmatter")
    return match.group(1)


def plugin_version():
    return json.loads(read(ROOT / ".claude-plugin" / "plugin.json"))["version"]


class VersionTest(unittest.TestCase):
    def test_skill_metadata_matches_plugin(self):
        match = re.search(r'^\s+version:\s*"([^"]+)"', frontmatter(SKILL_MD), re.M)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), plugin_version())

    def test_every_changelog_starts_with_current_version(self):
        for path in LANG_DOCS["CHANGELOG"]:
            first = re.search(r"^## \[([^\]]+)\]", read(path), re.M)
            self.assertIsNotNone(first, path)
            self.assertEqual(first.group(1), plugin_version(), path)

    def test_changelogs_list_the_same_versions(self):
        versions = [re.findall(r"^## \[([^\]]+)\]", read(p), re.M) for p in LANG_DOCS["CHANGELOG"]]
        self.assertEqual(versions[0], versions[1])
        self.assertEqual(versions[0], versions[2])


class SkillWiringTest(unittest.TestCase):
    def test_name_matches_folder(self):
        self.assertRegex(frontmatter(SKILL_MD), rf"(?m)^name: {SKILL_NAME}$")

    def test_description_fits_the_limit(self):
        block = frontmatter(SKILL_MD).split("description:", 1)[1].split("\nlicense:", 1)[0]
        description = " ".join(block.replace(">", "", 1).split())
        self.assertLessEqual(len(description), 1024)

    def test_every_reference_is_routed_and_exists(self):
        text = read(SKILL_MD)
        routed = set(re.findall(r"references/([\w.-]+\.md)", text))
        present = {p.name for p in (SKILL_DIR / "references").glob("*.md")}
        self.assertEqual(routed - present, set(), "SKILL.md points to missing files")
        self.assertEqual(present - routed, set(), "reference files SKILL.md never routes to")

    def test_references_mentioned_inside_references_exist(self):
        present = {p.name for p in (SKILL_DIR / "references").glob("*.md")}
        for path in (SKILL_DIR / "references").glob("*.md"):
            for name in re.findall(r"`([a-z0-9-]+\.md)`", read(path)):
                self.assertIn(name, present, f"{path.name} mentions {name}")

    def test_refactor_command_points_to_the_skill(self):
        command = ROOT / "commands" / "secops-refatorar.md"
        self.assertIn("description:", frontmatter(command))
        text = read(command)
        self.assertIn(SKILL_NAME, text)
        self.assertIn("$ARGUMENTS", text)
        self.assertIn("/secops-refatorar", read(SKILL_MD))

    def test_third_party_notice_is_complete(self):
        text = read(SKILL_DIR / "THIRD_PARTY_NOTICES.md")
        self.assertIn("Copyright (c) 2026 Maze", text)
        self.assertIn("https://github.com/caldoai/skills", text)
        self.assertIn("The above copyright notice and this permission notice", text)
        for name in ("estrutura.md", "refatoracao-completa.md"):
            self.assertIn("caldoai/skills", read(SKILL_DIR / "references" / name), name)


class EvalsTest(unittest.TestCase):
    def test_evals_are_well_formed(self):
        data = json.loads(read(SKILL_DIR / "evals" / "evals.json"))
        self.assertEqual(data["skill_name"], SKILL_NAME)
        ids = [e["id"] for e in data["evals"]]
        self.assertEqual(ids, list(range(1, len(ids) + 1)))
        for case in data["evals"]:
            for key in ("prompt", "expected_output", "assertions", "files"):
                self.assertIn(key, case, case["id"])
            self.assertTrue(case["prompt"].strip(), case["id"])
            self.assertGreaterEqual(len(case["assertions"]), 2, case["id"])


class ManifestTest(unittest.TestCase):
    def test_marketplace_lists_this_plugin(self):
        market = json.loads(read(ROOT / ".claude-plugin" / "marketplace.json"))
        names = [p["name"] for p in market["plugins"]]
        self.assertIn(SKILL_NAME, names)

    def test_plugin_icon_exists(self):
        plugin = json.loads(read(ROOT / ".claude-plugin" / "plugin.json"))
        self.assertTrue((ROOT / plugin["icon"]).is_file())


class TranslationsTest(unittest.TestCase):
    def test_each_document_exists_in_three_languages(self):
        for trio in LANG_DOCS.values():
            for path in trio:
                self.assertTrue(path.is_file(), path)

    def test_language_switchers_resolve(self):
        for trio in LANG_DOCS.values():
            for path in trio:
                for target in re.findall(r"\]\(([^)#\s]+\.md)\)", read(path)):
                    if target.startswith("http"):
                        continue
                    self.assertTrue((path.parent / target).resolve().is_file(), f"{path}: {target}")

    def test_readmes_have_the_same_sections(self):
        counts = [len(re.findall(r"(?m)^## ", read(p))) for p in LANG_DOCS["README"]]
        self.assertEqual(len(set(counts)), 1, counts)


class DocsStyleTest(unittest.TestCase):
    """The docs read like a person wrote them: no dash asides, no ellipsis character, no curly quotes."""

    FORBIDDEN = {"—": "em dash", "–": "en dash", "…": "ellipsis character",
                 "“": "curly quote", "”": "curly quote"}

    def test_no_forbidden_characters(self):
        for path in STYLE_CHECKED:
            for number, line in enumerate(read(path).splitlines(), 1):
                for char, name in self.FORBIDDEN.items():
                    self.assertNotIn(char, line, f"{path.relative_to(ROOT)}:{number} has an {name}")


class PackageTest(unittest.TestCase):
    def test_zip_carries_the_whole_skill_and_the_notice(self):
        spec = importlib.util.spec_from_file_location("build_zip", ROOT / "tools" / "build_zip.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            out = module.build(pathlib.Path(tmp))
            self.assertEqual(out.name, f"{SKILL_NAME}-v{plugin_version()}.zip")
            with zipfile.ZipFile(out) as zf:
                names = set(zf.namelist())
        expected = {f"{SKILL_NAME}/{p.relative_to(SKILL_DIR).as_posix()}"
                    for p in SKILL_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        self.assertEqual(names, expected)
        self.assertIn(f"{SKILL_NAME}/THIRD_PARTY_NOTICES.md", names)


if __name__ == "__main__":
    unittest.main()
