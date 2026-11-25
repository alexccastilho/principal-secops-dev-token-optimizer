"""Tests of scripts/fontes.py, offline, over real responses recorded on 2026-11-25.

The fixtures in tests/fixtures/fontes/ were trimmed to a few entries. kev.json carries one
entry edited for the test (product "TEST-EDITED"), so the "actively exploited" flag can be
checked without depending on which CVEs the real catalog lists today.

Run: python -m unittest discover -s tests
Author: Alex Camacho Castilho
"""
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "principal-secops-dev-token-optimizer" / "scripts" / "fontes.py"
FIX = ROOT / "tests" / "fixtures" / "fontes"

spec = importlib.util.spec_from_file_location("fontes", SCRIPT)
fontes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fontes)


NPM = "https://registry.npmjs.org/x/-/x-1.0.0.tgz"


def fixture(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class FakeFetcher(fontes.Fetcher):
    """Answers from the recorded responses; any other URL is a source that is down."""

    def __init__(self):
        super().__init__(pathlib.Path(tempfile.mkdtemp()), offline=False)

    def get_json(self, url, kind, body=None):
        if url == fontes.EOL_URL.format(slug="php"):
            return fixture("eol-php.json")
        if url == fontes.OSV_BATCH:
            n = len(body["queries"])
            return {"results": [fixture("osv-batch.json")["results"][0]] + [{}] * (n - 1)}
        if url.startswith("https://api.osv.dev/v1/vulns/"):
            return fixture("osv-vuln.json")
        if url == fontes.KEV_URL:
            return fixture("kev.json")
        raise fontes.Unchecked("fonte fora do ar no teste")


def run(argv, fetcher=None):
    """Run main() with the fake fetcher; return (exit code, stdout)."""
    original = fontes.Fetcher
    if fetcher is not None:
        fontes.Fetcher = lambda cache, offline: fetcher
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = fontes.main(argv)
    finally:
        fontes.Fetcher = original
    return code, buf.getvalue()


class VersionTest(unittest.TestCase):
    def test_end_of_life_version_behind_its_patch_needs_action(self):
        code, out = run(["versao", "php", "--em-uso", "8.1.2"], FakeFetcher())
        self.assertEqual(code, fontes.ACT)
        self.assertIn("fim de vida", out)
        self.assertIn("8.1.34", out)

    def test_current_patch_of_a_supported_cycle_is_ok(self):
        latest = [r for r in fixture("eol-php.json")["result"]["releases"] if r["name"] == "8.4"][0]["latest"]["name"]
        code, out = run(["versao", "php", "--em-uso", latest], FakeFetcher())
        self.assertEqual(code, fontes.OK, out)
        self.assertNotIn("atrás do patch", out)

    def test_version_as_written_in_manifests_is_normalised(self):
        for raw, norm in (("v22.3.0", "22.3.0"), ("^8.1", "8.1"), (">=3.11", "3.11"), ("net8.0", "8.0"), ("8.1.2", "8.1.2")):
            self.assertEqual(fontes.normalize_version(raw), norm)
        code, out = run(["versao", "php", "--em-uso", "^8.1"], FakeFetcher())
        self.assertIn("ciclo 8.1", out)

    def test_cycle_matching_prefers_the_longest_name(self):
        releases = [{"name": "8"}, {"name": "8.1"}]
        self.assertEqual(fontes.match_cycle(releases, "8.1.9")["name"], "8.1")
        self.assertIsNone(fontes.match_cycle(releases, "9.0"))

    def test_tier_b_technology_is_reported_as_unchecked_not_guessed(self):
        code, out = run(["versao", "firebird"], FakeFetcher())
        self.assertEqual(code, fontes.UNCHECKED)
        self.assertIn("não verificado", out)

    def test_unknown_technology_is_a_usage_error(self):
        code, _ = run(["versao", "linguagem-inexistente"], FakeFetcher())
        self.assertEqual(code, fontes.USAGE)


class DepsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())

    def write(self, name, text):
        (self.tmp / name).write_text(text, encoding="utf-8")

    def test_lockfiles_are_read_and_private_packages_are_never_sent(self):
        self.write("package-lock.json", json.dumps({"lockfileVersion": 3, "packages": {
            "": {}, "node_modules/lodash": {"version": "4.17.20", "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.20.tgz"},
            "node_modules/interno": {"version": "1.0.0", "resolved": "https://npm.empresa.local/interno.tgz"}}}))
        self.write("requirements.txt", "django==4.2.1\nflask>=2\n# comentario\n")
        self.write("composer.lock", json.dumps({"packages": [
            {"name": "monolog/monolog", "version": "v3.5.0", "notification-url": "https://packagist.org/downloads/"},
            {"name": "empresa/interno", "version": "1.0.0", "dist": {"url": "https://github.com/empresa/interno/zipball/x"}}]}))
        self.write("go.mod", "module github.com/empresa/app\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n"
                             "\tgithub.com/empresa/lib-interna v0.1.0\n)\n")
        self.write("Cargo.lock", '[[package]]\nname = "serde"\nversion = "1.0.190"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\n\n'
                                 '[[package]]\nname = "crate-local"\nversion = "0.1.0"\n')
        found_list, _ = fontes.read_locks(self.tmp)
        found = {(e, n, v) for e, n, v, _ in found_list}
        self.assertNotIn("empresa/interno", {n for _, n, _ in found})
        self.assertNotIn("github.com/empresa/lib-interna", {n for _, n, _ in found})
        self.assertNotIn("crate-local", {n for _, n, _ in found})
        self.assertIn(("npm", "lodash", "4.17.20"), found)
        self.assertNotIn("interno", {n for _, n, _ in found})
        self.assertIn(("PyPI", "django", "4.2.1"), found)
        self.assertNotIn("flask", {n for _, n, _ in found})
        self.assertIn(("Packagist", "monolog/monolog", "3.5.0"), found)
        self.assertIn(("Go", "github.com/gin-gonic/gin", "v1.9.1"), found)
        self.assertIn(("crates.io", "serde", "1.0.190"), found)

    def test_files_that_mix_in_a_private_source_are_never_sent(self):
        cases = {
            "requirements.txt": "--extra-index-url https://pypi.empresa.local/simple\ninterno==1.0\n",
            "poetry.lock": '[[package]]\nname = "interno"\nversion = "1.0"\n\n[package.source]\ntype = "legacy"\nurl = "https://pypi.empresa.local/simple"\n',
            "uv.lock": '[[package]]\nname = "interno"\nversion = "1.0"\nsource = { registry = "https://pypi.empresa.local/simple" }\n',
            "Gemfile.lock": "GEM\n  remote: https://gems.empresa.local/\n  specs:\n    interno (1.0)\n\nPLATFORMS\n  ruby\n",
            "package-lock.json": json.dumps({"lockfileVersion": 3, "packages": {
                "node_modules/interno": {"version": "1.0.0"},
                "node_modules/ligado": {"version": "1.0.0", "link": True, "resolved": NPM}}}),
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                tmp = pathlib.Path(tempfile.mkdtemp())
                (tmp / name).write_text(text, encoding="utf-8")
                found, _ = fontes.read_locks(tmp)
                self.assertEqual(found, [], name)

    def test_requirements_are_skipped_when_pip_points_to_a_private_index(self):
        self.write("requirements.txt", "interno==1.0\n")
        old = os.environ.get("PIP_EXTRA_INDEX_URL")
        os.environ["PIP_EXTRA_INDEX_URL"] = "https://pypi.empresa.local/simple"
        try:
            found, skipped = fontes.read_locks(self.tmp)
        finally:
            if old is None:
                del os.environ["PIP_EXTRA_INDEX_URL"]
            else:
                os.environ["PIP_EXTRA_INDEX_URL"] = old
        self.assertEqual(found, [])
        self.assertTrue(skipped)

    def test_public_entries_of_the_same_formats_are_read(self):
        self.write("poetry.lock", '[[package]]\nname = "requests"\nversion = "2.31.0"\n')
        self.write("uv.lock", '[[package]]\nname = "flask"\nversion = "3.0.0"\nsource = { registry = "https://pypi.org/simple" }\n')
        self.write("Gemfile.lock", "GEM\n  remote: https://rubygems.org/\n  specs:\n    rack (3.0.8)\n\nPLATFORMS\n  ruby\n")
        found, _ = fontes.read_locks(self.tmp)
        names = {n for _, n, _, _ in found}
        self.assertEqual(names, {"requests", "flask", "rack"})

    def test_nuget_lock_is_skipped_when_a_private_feed_is_configured(self):
        self.write("packages.lock.json", json.dumps({"version": 1, "dependencies": {"net8.0": {
            "Interno.Lib": {"type": "Direct", "resolved": "1.0.0"}}}}))
        self.write("nuget.config", '<configuration><packageSources><add key="empresa" value="https://nuget.empresa.local/v3/index.json" /></packageSources></configuration>')
        found, skipped = fontes.read_locks(self.tmp)
        self.assertEqual(found, [])
        self.assertTrue(skipped)

    def test_known_flaw_is_reported_with_the_fix_and_the_kev_flag(self):
        self.write("package-lock.json", json.dumps({"lockfileVersion": 3, "packages": {
            "node_modules/lodash": {"version": "4.17.20", "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.20.tgz"}}}))
        code, out = run(["deps", str(self.tmp)], FakeFetcher())
        self.assertEqual(code, fontes.ACT)
        self.assertIn("lodash 4.17.20", out)
        self.assertIn("4.17.21", out)
        self.assertIn("EXPLORADA ATIVAMENTE", out)

    def test_no_lockfile_says_so_and_passes(self):
        code, out = run(["deps", str(self.tmp)], FakeFetcher())
        self.assertEqual(code, fontes.OK)
        self.assertIn("Nenhum arquivo de trava", out)

    def test_fixed_version_is_the_lowest_above_the_installed_one(self):
        vuln = {"affected": [{"package": {"name": "django"}, "ranges": [{"events": [
            {"introduced": "0"}, {"fixed": "2.2.28"}, {"introduced": "3.0"}, {"fixed": "3.2.14"},
            {"introduced": "4.0"}, {"fixed": "4.0.6"}]}]}]}
        self.assertEqual(fontes._fixed(vuln, "django", "3.2.0"), "3.2.14")
        self.assertIsNone(fontes._fixed(vuln, "django", "5.0"))


class SafetyTest(unittest.TestCase):
    def test_host_outside_the_allow_list_is_refused(self):
        fetch = fontes.Fetcher(pathlib.Path(tempfile.mkdtemp()), offline=False)
        for url in ("https://evil.example/x.json", "http://endoflife.date/api/v1/products/php/"):
            with self.assertRaises(fontes.Unchecked):
                fetch.get_json(url, "eol")

    def test_offline_without_cache_is_unchecked_never_a_guess(self):
        code, out = run(["--offline", "--cache-dir", tempfile.mkdtemp(), "versao", "php", "--em-uso", "8.4.1"])
        self.assertEqual(code, fontes.UNCHECKED)
        self.assertIn("não verificado", out)

    def test_stale_cache_is_used_offline_and_dated(self):
        cache = pathlib.Path(tempfile.mkdtemp())
        fetch = fontes.Fetcher(cache, offline=True)
        url = fontes.EOL_URL.format(slug="php")
        fetch._key(url, None).write_text(json.dumps({"t": 0, "data": {"ok": 1}}), encoding="utf-8")
        self.assertEqual(fetch.get_json(url, "eol"), {"ok": 1})
        self.assertTrue(fetch.stale_dates)

    def test_literal_plugin_data_placeholder_falls_back_to_a_real_folder(self):
        folder = fontes.cache_dir("${CLAUDE_PLUGIN_DATA}")
        self.assertNotIn("$", str(folder))
        self.assertTrue(folder.is_dir())

    def test_cache_is_never_inside_the_skill_folder(self):
        folder = fontes.cache_dir(None)
        self.assertNotIn(SCRIPT.parent.parent.resolve(), folder.resolve().parents)

    def test_free_text_is_cleaned_and_truncated(self):
        self.assertEqual(fontes._clean("a\x1b[31m b\nc" + "x" * 200, 10), "a [31m b c...")

    def test_text_output_respects_the_character_cap(self):
        code, out = run(["--max-chars", "120", "versao", "php", "--em-uso", "8.1.2"], FakeFetcher())
        self.assertLessEqual(len(out.strip().splitlines()[0]), 200)
        self.assertLessEqual(len(out), 120 + 80)


class RegistryTest(unittest.TestCase):
    def test_registry_entries_are_well_formed(self):
        reg = fontes.load_registry()
        self.assertEqual(reg["schema"], 1)
        for key, tech in reg["tecnologias"].items():
            self.assertIn(tech.get("camada"), ("A", "B", "C"), key)
            self.assertTrue(tech.get("nome"), key)
            if tech["camada"] == "A":
                self.assertTrue(tech.get("eol"), f"{key}: tier A needs an endoflife.date slug")
            for field in ("avisos", "notas", "migracao", "estilo"):
                if tech.get(field):
                    self.assertTrue(tech[field].startswith("https://"), f"{key}.{field}")

    def test_registry_holds_addresses_not_dated_facts(self):
        text = json.dumps(fontes.load_registry()["tecnologias"])
        self.assertNotRegex(text, r'"(latest|eolFrom|ultimo_patch|versao_atual)"')


if __name__ == "__main__":
    unittest.main()
