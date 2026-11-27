"""The benchmark analyzers measure what they claim to measure.

Run: python -m unittest discover -s tests
Author: Alex Camacho Castilho
"""
import importlib.util
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "benchmark" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyze = load("analyze")
analyze_refactor = load("analyze_refactor")


class RefactorAnalyzerTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_node_tests_in_a_tests_folder_are_run(self):
        # "node --test tests/" fails with MODULE_NOT_FOUND on Node 24 (the benchmark machine); that zeroed every Node row.
        project = pathlib.Path(tempfile.mkdtemp())
        (project / "tests").mkdir()
        (project / "tests" / "apoio.js").write_text("module.exports = { dois: 2 };\n", encoding="utf-8")
        (project / "tests" / "soma.test.js").write_text(
            "const test = require('node:test');\nconst assert = require('node:assert');\n"
            "const { dois } = require('./apoio');\n"
            "test('soma', () => assert.strictEqual(1 + 1, dois));\n"
            "test('outra', () => assert.ok(true));\n", encoding="utf-8")
        try:
            self.assertEqual(analyze_refactor.visible_tests("node", project), (2, 0))
        finally:
            shutil.rmtree(project, ignore_errors=True)


class CreateAnalyzerTest(unittest.TestCase):
    def test_cost_keeps_three_decimals(self):
        self.assertEqual(analyze.mean([0.4401, 0.4399], digits=3), 0.44)
        self.assertEqual(analyze.mean([0.5531, 0.5529], digits=3), 0.553)

    def test_dotnet_runtime_without_sdk_is_not_a_failed_build(self):
        app = pathlib.Path(tempfile.mkdtemp())
        (app / "Program.cs").write_text("class P { static void Main() {} }\n", encoding="utf-8")
        (app / "app.csproj").write_text("<Project Sdk=\"Microsoft.NET.Sdk\"></Project>\n", encoding="utf-8")
        no_sdk = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(analyze.shutil, "which", return_value="dotnet"), \
                mock.patch.object(analyze.subprocess, "run", return_value=no_sdk):
            status, _, detail = analyze.build_check("csharp", app)
        shutil.rmtree(app, ignore_errors=True)
        self.assertEqual(status, "n/a")
        self.assertIn("SDK", detail)


class PublishedResultsTest(unittest.TestCase):
    def test_every_published_result_is_utf8(self):
        for path in (ROOT / "benchmark" / "results").rglob("*"):
            if path.is_file() and path.suffix in (".txt", ".json", ".md", ".py"):
                with self.subTest(path=path.name):
                    path.read_bytes().decode("utf-8")

    def test_activation_summary_prints_utf8_whatever_the_console(self):
        text = (ROOT / "benchmark" / "results" / "2.3.0" / "resumo_ativacao.py").read_text(encoding="utf-8")
        self.assertIn('reconfigure(encoding="utf-8")', text)


if __name__ == "__main__":
    unittest.main()
