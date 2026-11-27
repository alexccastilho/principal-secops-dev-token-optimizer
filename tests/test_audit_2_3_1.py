"""Defects found in the external audit of 2.3.0, each with the case that proves it fixed.

Run: python -m unittest discover -s tests
Author: Alex Camacho Castilho
"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "principal-secops-dev-token-optimizer" / "scripts"
SCANNER = SCRIPTS / "revisar_codigo.py"

spec = importlib.util.spec_from_file_location("fontes_audit", SCRIPTS / "fontes.py")
fontes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fontes)


def scan(*args):
    return subprocess.run([sys.executable, "-I", str(SCANNER), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TempDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def rules(self, *paths):
        result = scan("--json", *(paths or [self.dir]))
        return {f["rule"] for f in json.loads(result.stdout)["findings"]}

    def delivery(self):
        result = scan("--entrega", "--json", self.dir)
        data = json.loads(result.stdout)
        return result.returncode, sum(data["delivery"].values(), [])


class SourceHygieneTest(unittest.TestCase):
    def test_no_python_file_holds_a_control_character(self):
        # A literal backspace (0x08) where "\b" was meant silenced a whole rule.
        for path in list((ROOT / "skills").rglob("*.py")) + list((ROOT / "benchmark").rglob("*.py")) \
                + list((ROOT / "tests").rglob("*.py")) + list((ROOT / "tools").rglob("*.py")):
            data = path.read_bytes()
            bad = [i for i, c in enumerate(data) if c < 32 and c not in (9, 10, 13)]
            self.assertEqual(bad, [], f"{path.relative_to(ROOT)} has control bytes at {bad[:5]}")


class ScannerAuditTest(TempDir):
    def test_android_cleartext_traffic_is_flagged(self):
        self.write("AndroidManifest.xml", '<application android:usesCleartextTraffic="true">\n')
        self.write("res/xml/network_security_config.xml", '<base-config cleartextTrafficPermitted="true">\n')
        result = json.loads(scan("--json", self.dir).stdout)["findings"]
        self.assertEqual(sorted(f["rule"] for f in result), ["tls-desligado", "tls-desligado"])

    def test_android_cleartext_off_is_not_flagged(self):
        self.write("AndroidManifest.xml", '<application android:usesCleartextTraffic="false">\n')
        self.assertNotIn("tls-desligado", self.rules())

    def test_groovy_extensions_are_read_when_scanning_a_folder(self):
        self.write("build.gvy", "def x = Eval.me(entrada)\n")
        self.write("deploy.jenkinsfile", 'sh "deploy ${params.alvo}"\n')
        result = json.loads(scan("--json", self.dir).stdout)
        files = {pathlib.Path(f["file"]).name for f in result["findings"]}
        self.assertEqual(files, {"build.gvy", "deploy.jenkinsfile"})

    def test_short_lowercase_password_is_flagged(self):
        for value in ("minhasenha", "adminadmin", "supersecret", "admin123"):
            with self.subTest(value=value):
                path = self.write("conf.py", f'password = "{value}"\n')
                self.assertIn("secret-atribuido", self.rules(path))

    def test_short_password_in_test_data_is_not_flagged(self):
        # Test fixtures create users with throwaway passwords; flagging them buried real findings.
        for name in ("tests/usuarios.test.js", "test/apoio.js", "src/__tests__/login.js",
                     "app/test_login.py", "login_test.go", "LoginTest.java", "login.spec.ts"):
            with self.subTest(name=name):
                path = self.write(name, "criar({ login: 'paula', senha: 'abacaxi' });\n")
                self.assertNotIn("secret-atribuido", self.rules(path))
        path = self.write("tests/conf.js", "const k = { senha: 'abacaxi123' };\n")
        self.assertIn("secret-atribuido", self.rules(path))

    def test_screen_labels_are_still_not_secrets(self):
        path = self.write("pt.js", 'const t = { password: "Senha", forgot_password: "Esqueceu?",\n'
                                   '  secret: "Segredo:", token: "Token" };\n')
        self.assertNotIn("secret-atribuido", self.rules(path))

    def test_same_rule_in_two_languages_keeps_each_fix(self):
        # shell-montado and codigo-dinamico exist for Lua and for Clipper, with a different fix each.
        self.write("a.lua", 'local h = io.popen("ls " .. dir)\nlocal f = loadstring(texto)\n')
        self.write("a.prg", 'RUN ("del " + cArquivo)\nx := &(cExpr)\n')
        result = json.loads(scan("--json", self.dir).stdout)["findings"]
        fixes = {(f["rule"], f["fix"]) for f in result if f["rule"] in ("shell-montado", "codigo-dinamico")}
        self.assertEqual(len(fixes), 4, fixes)
        text = scan(self.dir).stdout
        for _, fix in fixes:
            self.assertIn(fix, text)


class DeliveryAuditTest(TempDir):
    def test_from_inside_a_string_or_comment_is_not_an_import(self):
        self.write("package.json", json.dumps({"name": "x", "dependencies": {}}))
        self.write("app.js", "const msg = \"copy from 'somewhere'\";\n"
                             "const q = \"select * from 'users'\";\n"
                             "// import x from 'comentado'\n"
                             "/*\n * import y from 'bloco'\n */\n")
        self.assertEqual(self.delivery(), (0, []))

    def test_real_imports_are_still_checked(self):
        self.write("package.json", json.dumps({"name": "x", "dependencies": {"express": "^4"}}))
        self.write("app.js", "import express from 'express';\nimport {\n  a,\n  b\n} from 'lodash';\n"
                             "import 'dotenv/config';\nconst k = require('knex');\n"
                             "export { c } from 'zod';\nconst m = await import('chalk');\n")
        code, problems = self.delivery()
        self.assertEqual(code, 1)
        missing = sorted(p.split("'")[1] for p in problems)
        self.assertEqual(missing, ["chalk", "dotenv", "knex", "lodash", "zod"])

    def test_jsx_tsx_and_module_extensions_are_checked(self):
        self.write("package.json", json.dumps({"name": "x", "dependencies": {}}))
        for i, ext in enumerate((".jsx", ".tsx", ".mts", ".cts")):
            self.write(f"m{i}{ext}", f"import p{i} from 'pkg{i}';\n")
        code, problems = self.delivery()
        self.assertEqual(code, 1)
        self.assertEqual(sorted(p.split("'")[1] for p in problems), ["pkg0", "pkg1", "pkg2", "pkg3"])

    def test_python_import_inside_a_docstring_is_ignored(self):
        self.write("app.py", '"""Exemplo de uso:\n\nimport foo\nfrom bar import baz\n"""\nprint(1)\n')
        self.assertEqual(self.delivery(), (0, []))

    def test_python_check_runs_without_stdlib_module_names(self):
        # Python 3.8 and 3.9 have no sys.stdlib_module_names; the check must not go silent.
        self.write("app.py", "import os\nimport json\nimport requests\n")
        code = ("import sys, runpy; del sys.stdlib_module_names; sys.argv = %r; "
                "runpy.run_path(%r, run_name='__main__')"
                % (["revisar_codigo.py", "--entrega", "--json", str(self.dir)], str(SCANNER)))
        result = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        problems = sum(json.loads(result.stdout)["delivery"].values(), [])
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("requests", problems[0])
        self.assertNotIn("json", problems[0])

    def test_entrega_on_a_single_file_is_not_a_silent_pass(self):
        path = self.write("app.py", "print(1)\n")
        result = scan("--entrega", path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("pasta", result.stderr + result.stdout)


class FontesAuditTest(unittest.TestCase):
    def test_oldest_stale_cache_date_is_chronological(self):
        cache = pathlib.Path(tempfile.mkdtemp())
        fetch = fontes.Fetcher(cache, offline=True)
        stamps = {"https://endoflife.date/api/v1/products/php/": (2026, 12, 1),
                  "https://endoflife.date/api/v1/products/python/": (2026, 11, 25)}
        for url, day in stamps.items():
            t = time.mktime(day + (12, 0, 0, 0, 0, -1))
            fetch._key(url, None).write_text(json.dumps({"t": t, "data": {}}), encoding="utf-8")
            fetch.get_json(url, "eol")
        self.assertEqual(fetch.oldest_stale(), "25/11/2026")

    def test_kev_flag_uses_the_record_id_when_it_is_a_cve(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        (tmp / "package-lock.json").write_text(json.dumps({"lockfileVersion": 3, "packages": {
            "node_modules/lodash": {"version": "4.17.20",
                                    "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.20.tgz"}}}),
            encoding="utf-8")

        class Fake(fontes.Fetcher):
            def get_json(self, url, kind, body=None):
                if url == fontes.OSV_BATCH:
                    return {"results": [{"vulns": [{"id": "CVE-2021-23337"}]}]}
                if url.startswith("https://api.osv.dev/v1/vulns/"):
                    return {"id": "CVE-2021-23337", "aliases": [], "summary": "x"}
                if url == fontes.KEV_URL:
                    return {"vulnerabilities": [{"cveID": "CVE-2021-23337"}]}
                raise fontes.Unchecked("fora")

        _, out, _ = fontes.cmd_deps(type("A", (), {"pasta": str(tmp)})(), Fake(tmp, offline=False), {})
        row = out["falhas"][0]
        self.assertTrue(row["explorada_ativamente"])
        self.assertEqual(row["cve"], ["CVE-2021-23337"])

    def test_go_mod_exclude_and_replace_blocks_are_not_dependencies(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        (tmp / "go.mod").write_text(
            "module github.com/empresa/app\n\ngo 1.22\n\n"
            "require (\n\tgithub.com/gin-gonic/gin v1.9.1\n)\n\n"
            "require github.com/google/uuid v1.6.0\n\n"
            "exclude (\n\tgolang.org/x/net v0.1.0\n)\n\n"
            "replace (\n\tgithub.com/velho/lib v1.0.0 => ../lib\n)\n\n"
            "exclude golang.org/x/text v0.3.0\n", encoding="utf-8")
        found, _ = fontes.read_locks(tmp)
        self.assertEqual(sorted(n for _, n, _, _ in found),
                         ["github.com/gin-gonic/gin", "github.com/google/uuid"])

    def test_pre_release_sorts_below_the_final_release(self):
        older_newer = [("1.2.3-rc1", "1.2.3"), ("1.2.3-alpha.2", "1.2.3-beta.1"), ("1.2.3b1", "1.2.3"),
                       ("1.2.3.rc1", "1.2.3"), ("2.0.0-beta", "2.0.0"), ("1.2.3", "1.2.3.post1"),
                       ("1.2.3", "1.2.4-rc1"), ("4.0.0.0", "4.0.0.1"), ("1.2.3", "1.2.10"),
                       ("v0.0.0-20230101000000-abcdef123456", "v0.1.0")]
        for old, new in older_newer:
            with self.subTest(old=old, new=new):
                self.assertLess(fontes._vkey(old), fontes._vkey(new))
        self.assertEqual(fontes._vkey("1.2.3"), fontes._vkey("v1.2.3"))

    def test_fixed_version_above_an_installed_pre_release_is_found(self):
        vuln = {"affected": [{"package": {"name": "pkg"}, "ranges": [{"events": [
            {"introduced": "0"}, {"fixed": "1.2.3"}]}]}]}
        self.assertEqual(fontes._fixed(vuln, "pkg", "1.2.3-rc1"), "1.2.3")
        self.assertIsNone(fontes._fixed(vuln, "pkg", "1.2.3"))


if __name__ == "__main__":
    unittest.main()
