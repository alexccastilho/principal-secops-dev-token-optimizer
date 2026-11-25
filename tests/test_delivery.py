"""The --entrega mode of the scanner: does the project have the pieces to run as delivered?

Each failing case reproduces a defect measured in the 2.2.0 benchmark, with the correct
project next to it, so the check never flags working code.

Run: python -m unittest discover -s tests
Author: Alex Camacho Castilho
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCANNER = ROOT / "skills" / "principal-secops-dev-token-optimizer" / "scripts" / "revisar_codigo.py"


def deliver(folder):
    return subprocess.run([sys.executable, "-I", str(SCANNER), "--entrega", "--json", str(folder)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def problems(self):
        result = deliver(self.dir)
        data = json.loads(result.stdout)
        return result.returncode, sum(data["delivery"].values(), [])

    def test_launcher_calling_a_script_never_written_fails(self):
        self.write("index.php", "<?php echo 'ok';\n")
        self.write("iniciar.bat", "@echo off\r\nphp bin\\criar-usuario.php\r\nphp -S localhost:8000\r\n")
        code, problems = self.problems()
        self.assertEqual(code, 1)
        self.assertTrue(any("criar-usuario.php" in p for p in problems), problems)
        self.write("bin/criar-usuario.php", "<?php echo 'criado';\n")
        code, problems = self.problems()
        self.assertEqual((code, problems), (0, []))

    def test_go_without_go_mod_fails(self):
        self.write("main.go", "package main\nfunc main() {}\n")
        code, problems = self.problems()
        self.assertEqual(code, 1)
        self.assertTrue(any("go.mod" in p for p in problems), problems)
        self.write("go.mod", "module contatos\n\ngo 1.22\n")
        self.assertEqual(self.problems(), (0, []))

    def test_node_package_used_but_not_declared_fails(self):
        self.write("server.js", "const express = require('express');\nconst fs = require('node:fs');\n"
                                "const path = require('path');\nconst db = require('./db');\n")
        self.write("db.js", "module.exports = {};\n")
        self.write("package.json", json.dumps({"name": "x", "scripts": {"start": "node server.js"}}))
        code, problems = self.problems()
        self.assertEqual(code, 1)
        self.assertEqual(problems, ["Pacote 'express' e usado no codigo mas nao esta no package.json."])
        self.write("web/package.json", json.dumps({"name": "web"}))
        self.write("web/app.js", "import x from 'https://esm.sh/x';\nimport y from '@/util';\nimport z from 'vue';\n")
        code, problems = self.problems()
        self.assertIn("Pacote 'vue' e usado no codigo mas nao esta no web%spackage.json." % os.sep, problems)
        self.assertFalse(any("esm.sh" in p or "'@/util'" in p for p in problems), problems)
        (self.dir / "web" / "app.js").unlink()
        self.write("package.json", json.dumps({"name": "x", "scripts": {"start": "node server.js"},
                                               "dependencies": {"express": "^5.0.0"}}))
        self.assertEqual(self.problems(), (0, []))

    def test_readme_command_pointing_to_a_missing_file_fails_but_prose_does_not(self):
        self.write("app.py", "print('ok')\n")
        self.write("README.md", "Para rodar:\n\n```\npython app.py\npython criar_admin.py\n```\n\n"
                                "Um arquivo como exemplo.py pode ser criado depois.\n")
        code, problems = self.problems()
        self.assertEqual(code, 1)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("criar_admin.py", problems[0])

    def test_file_names_with_spaces_in_subfolders_and_product_names_pass(self):
        self.write("contatos/db.py", "x = 1\n")
        self.write("Abrir Contatos.bat", "@echo off\r\npython -m contatos\r\n")
        self.write("LEIA-ME.md", "Clique em `Abrir Contatos.bat`. O banco fica em `db.py`. Precisa do `Node.js`.\n")
        self.write("rodar.bat", "@echo off\r\nstart Node.js\r\n")
        self.assertEqual(self.problems(), (0, []))

    def test_csharp_without_project_file_fails(self):
        self.write("Program.cs", "Console.WriteLine(1);\n")
        code, problems = self.problems()
        self.assertEqual(code, 1)
        self.write("Contatos.csproj", "<Project Sdk=\"Microsoft.NET.Sdk\"></Project>\n")
        self.assertEqual(self.problems(), (0, []))

    def test_placeholders_urls_and_generated_folders_are_ignored(self):
        self.write("app.js", "console.log(1);\n")
        self.write("README.md", "`node <arquivo>.js` e `https://exemplo.com/a.js` e `node_modules/x/y.js` e `node app.js`\n")
        self.assertEqual(self.problems(), (0, []))

    def test_without_flag_delivery_is_not_checked(self):
        self.write("main.go", "package main\nfunc main() {}\n")
        result = subprocess.run([sys.executable, "-I", str(SCANNER), str(self.dir)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
