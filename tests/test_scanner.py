"""Behavior of the pre-delivery scanner (scripts/revisar_codigo.py).

Run: python -m unittest discover -s tests
Author: Alex Camacho Castilho
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCANNER = ROOT / "skills" / "principal-secops-dev-token-optimizer" / "scripts" / "revisar_codigo.py"
SECRET = "hunter2hunter2"


def scan(*paths, json_output=False):
    args = [sys.executable, "-I", str(SCANNER)]
    if json_output:
        args.append("--json")
    args.extend(str(p) for p in paths)
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_insecure_php_exits_1_with_expected_rules(self):
        path = self.write("bad.php", (
            "<?php\n"
            "$r = $pdo->query(\"SELECT * FROM users WHERE id = $id\");\n"
            f"$password = \"{SECRET}\";\n"
            "echo $_GET['q'];\n"
        ))
        result = scan(path, json_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        rules = {f["rule"] for f in json.loads(result.stdout)["findings"]}
        self.assertTrue({"sql-interp-php", "secret-atribuido", "echo-sem-escape"} <= rules, rules)

    def test_secret_value_never_printed(self):
        path = self.write("leak.py", f"x = eval(tok); password = \"{SECRET}\"\n")
        for json_output in (False, True):
            result = scan(path, json_output=json_output)
            self.assertNotIn(SECRET, result.stdout + result.stderr)

    def test_safe_php_exits_0(self):
        path = self.write("good.php", (
            "<?php\n"
            "$stmt = $pdo->prepare(\"SELECT * FROM users WHERE id = ?\");\n"
            "$stmt->execute([$_GET['id']]);\n"
            "echo htmlspecialchars($_GET['q'], ENT_QUOTES, 'UTF-8');\n"
            "$msg = sprintf(\"Total: %d\", $n);\n"
        ))
        result = scan(path)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_env_file_is_where_secrets_belong(self):
        path = self.write(".env", "DB_PASSWORD=supersecret123\n")
        result = scan(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("supersecret123", result.stdout)

    def test_missing_path_is_not_a_pass(self):
        result = scan(self.dir / "does-not-exist.php")
        self.assertEqual(result.returncode, 2)

    def test_parent_folder_named_build_still_scanned(self):
        project = self.dir / "build" / "projeto"
        project.mkdir(parents=True)
        (project / "bad.php").write_text("<?php\necho $_GET['q'];\n", encoding="utf-8")
        result = scan(project)
        self.assertEqual(result.returncode, 1, result.stdout)


if __name__ == "__main__":
    unittest.main()
