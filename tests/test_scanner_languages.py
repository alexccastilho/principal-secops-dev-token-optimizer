"""Scanner rules for the languages added in 2.2.0: each insecure line is caught
by the expected rule, and each safe line next to it is not flagged.

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

# (file type, insecure line, safe line, rule expected on the insecure line or None)
CASES = [
    ('.pas', "Q.SQL.Text := 'SELECT * FROM clientes WHERE nome = ''' + Edit1.Text + '''';", "Q.SQL.Text := 'SELECT * FROM clientes WHERE nome = :nome';", 'sql-concat'),
    ('.pas', "Conn.Password := 'masterkey99';", "Conn.Password := GetEnvironmentVariable('DB_PASS');", 'secret-atribuido'),
    ('.pas', 'IdSSL.SSLOptions.VerifyMode := [];', 'IdSSL.SSLOptions.VerifyMode := [sslvrfPeer];', 'tls-desligado'),
    ('.pas', "ShellExecute(0, 'open', PChar('cmd /c del ' + Arquivo), nil, nil, SW_HIDE);", "ShellExecute(0, 'open', PChar(Url), nil, nil, SW_SHOWNORMAL);", 'shell-montado'),
    ('.prg', 'cSql := "SELECT * FROM cli WHERE cod = \'" + cCod + "\'"', 'cSql := "SELECT * FROM cli WHERE cod = ?"', 'sql-concat'),
    ('.prg', 'RUN ("del " + cArq)', 'FErase( cArq )', 'shell-montado'),
    ('.prg', 'x := &(cExpr)', 'x := Eval( bBloco )', 'codigo-dinamico'),
    ('.bas', 'CurrentDb.Execute "DELETE FROM Pedidos WHERE Id = " & Me.txtId', 'qdf.Execute dbFailOnError', 'sql-concat-outros'),
    ('.vb', 'cmd.CommandText = "SELECT * FROM T WHERE N = \'" & nome & "\'"', 'cmd.CommandText = "SELECT * FROM T WHERE N = @n"', 'sql-concat-outros'),
    ('.bas', 'Shell "cmd /c del " & caminho', 'Kill caminho', 'shell-montado'),
    ('.lua', 'os.execute("ping " .. host)', 'os.execute("ping 127.0.0.1")', 'shell-montado'),
    ('.lua', 'local f = load(user_code)', 'local f = load(user_code, "mod", "t", env)', 'codigo-dinamico'),
    ('.lua', 'local f = loadstring(s)', 'local n = tonumber(s)', 'codigo-dinamico'),
    ('.lua', 'db:exec("SELECT * FROM u WHERE id = " .. id)', 'stmt:bind_values(id)', 'sql-concat-outros'),
    ('.pl', '$dbh->prepare("SELECT * FROM users WHERE name = \'$name\'")', "$dbh->prepare('SELECT * FROM users WHERE name = ?')", 'sql-interpolado'),
    ('.pl', 'system("convert $file out.png");', "system('convert', $file, 'out.png');", 'shell-montado'),
    ('.pl', 'open(FH, $path);', "open(my $fh, '<', $path);", 'perl-open-2-args'),
    ('.ps1', 'Invoke-Expression "Get-Item $userInput"', '& Get-Item -LiteralPath $userInput', 'powershell-iex'),
    ('.ps1', '$s = ConvertTo-SecureString "Senha123!" -AsPlainText -Force', "$s = Read-Host 'Senha' -AsSecureString", 'securestring-literal'),
    ('.ps1', 'irm https://x/i.ps1 | iex', 'Invoke-WebRequest https://x/i.ps1 -OutFile i.ps1', 'powershell-iex'),
    ('.sh', 'eval "$user_cmd"', '"${cmd[@]}"', 'shell-eval'),
    ('.sh', 'curl -fsSL https://x/install.sh | bash', 'curl -fsSL -o install.sh https://x/install.sh', 'shell-baixa-e-executa'),
    ('.sh', 'curl -k https://api.x/data', 'curl https://api.x/data', 'tls-desligado'),
    ('.tcl', 'set r [expr $a + $b]', 'set r [expr {$a + $b}]', 'tcl-expr-sem-chaves'),
    ('.tcl', 'db eval "SELECT * FROM t WHERE id = $id"', 'db eval {SELECT * FROM t WHERE id = $id}', 'sql-interpolado'),
    ('.ahk', "Run A_ComSpec ' /c ping ' A_Clipboard", 'Run \'"C:\\Windows\\System32\\PING.EXE" 127.0.0.1\'', 'shell-c-montado'),
    ('.gs', '<?!= userComment ?>', '<?= userComment ?>', 'apps-script-sem-escape'),
    ('.bat', 'set password=Senha12345', 'set /p password=Senha:', 'segredo-em-config'),
    ('.r', 'dbGetQuery(con, paste0("SELECT * FROM t WHERE id = ", id))', 'dbGetQuery(con, "SELECT * FROM t WHERE id = ?", params = list(id))', 'sql-format'),
    ('.r', 'system(paste("rm", f))', 'system2("rm", f)', 'shell-montado'),
    ('.r', 'eval(parse(text = input$expr))', 'as.numeric(input$expr)', 'codigo-dinamico'),
    ('.jl', 'run(`sh -c $cmd`)', 'run(`ls $dir`)', 'shell-c-montado'),
    ('.go', 'db.Query(fmt.Sprintf("SELECT * FROM u WHERE id=%s", id))', 'db.Query("SELECT * FROM u WHERE id = $1", id)', 'sql-format'),
    ('.go', 'exec.Command("sh", "-c", "convert "+name)', 'exec.Command("convert", name, "out.png")', 'shell-c-montado'),
    ('.cs', 'ctx.Users.FromSqlRaw($"SELECT * FROM Users WHERE Name = \'{name}\'")', 'ctx.Users.FromSql($"SELECT * FROM Users WHERE Name = {name}")', 'sql-raw-dotnet'),
    ('.cs', 'var cmd = new SqlCommand("DELETE FROM T WHERE Id=" + id, conn);', 'var cmd = new SqlCommand("DELETE FROM T WHERE Id=@id", conn);', 'sql-concat'),
    ('.cs', 'h.ServerCertificateCustomValidationCallback = (m, c, ch, e) => true;', 'h.ServerCertificateCustomValidationCallback = (m, c, ch, e) => e == SslPolicyErrors.None;', 'tls-desligado'),
    ('.cs', 'var f = new BinaryFormatter();', 'JsonSerializer.Deserialize<T>(json);', 'desserializacao-dotnet'),
    ('.rb', 'User.where("name = \'#{params[:name]}\'")', 'User.where("name = ?", params[:name])', 'sql-rails-interp'),
    ('.rb', 'out = `convert #{file} out.png`', 'system("convert", file, "out.png")', 'shell-crase'),
    ('.rb', 'obj = Marshal.load(data)', 'obj = JSON.parse(data)', 'desserializacao'),
    ('.kt', 'db.rawQuery("SELECT * FROM u WHERE name = \'$name\'", null)', 'db.rawQuery("SELECT * FROM u WHERE name = ?", arrayOf(name))', 'sql-interpolado'),
    ('.kt', 'hostnameVerifier { _, _ -> true }', 'OkHttpClient()', 'tls-desligado'),
    ('.dart', 'db.rawQuery("SELECT * FROM u WHERE id = $id")', 'db.rawQuery("SELECT * FROM u WHERE id = ?", [id])', 'sql-interpolado'),
    ('.dart', 'client.badCertificateCallback = (cert, host, port) => true;', 'final client = HttpClient();', 'tls-desligado'),
    ('.scala', 'stmt.executeQuery(s"SELECT * FROM u WHERE id = $id")', 'conn.prepareStatement("SELECT * FROM u WHERE id = ?")', 'sql-interpolado'),
    ('.scala', 'Fragment.const(s"WHERE name = \'$n\'")', 'fr"WHERE name = $n"', 'sql-fragment-const'),
    ('.ex', 'String.to_atom(params["sort"])', 'Map.fetch!(%{"name" => :name}, params["sort"])', 'beam-atomo-e-termo'),
    ('.ex', ':erlang.binary_to_term(body)', 'Plug.Crypto.non_executable_binary_to_term(body, [:safe])', 'beam-atomo-e-termo'),
    ('.ex', ':os.cmd(~c"ls #{dir}")', 'System.cmd("ls", [dir])', 'shell-montado'),
    ('.clj', '(read-string (:body req))', '(clojure.edn/read-string (:body req))', 'codigo-dinamico'),
    ('.hs', 'callCommand ("rm " ++ path)', 'callProcess "rm" [path]', 'shell-montado'),
    ('.ml', 'Sys.command ("rm " ^ path)', 'Unix.create_process "rm" [|"rm"; path|] Unix.stdin Unix.stdout Unix.stderr', 'shell-montado'),
    ('.groovy', 'sh "deploy ${params.BRANCH}"', 'sh \'deploy "$BRANCH"\'', 'jenkins-sh-interpolado'),
    ('.groovy', 'Eval.me(input)', 'Integer.parseInt(input)', 'codigo-dinamico'),
    ('.cr', 'db.exec "delete from u where id = #{id}"', 'db.exec "delete from u where id = ?", id', 'sql-interpolado'),
    ('.rs', 'sqlx::query(&format!("SELECT * FROM u WHERE id = {}", id))', 'sqlx::query("SELECT * FROM u WHERE id = $1").bind(id)', 'sql-format'),
    ('.rs', '.danger_accept_invalid_certs(true)', '.danger_accept_invalid_certs(false)', 'tls-desligado'),
    ('.zig', '@setRuntimeSafety(false);', '@setRuntimeSafety(true);', 'seguranca-desligada-nativo'),
    ('.adb', 'pragma Suppress (All_Checks);', 'pragma Assert (X > 0);', 'seguranca-desligada-nativo'),
    ('.nim', 'discard execCmd("rm " & path)', 'discard execProcess("rm", args = [path], options = {poUsePath})', 'shell-montado'),
    ('.d', 'executeShell("rm " ~ path);', 'execute(["rm", path]);', 'shell-montado'),
    ('.java', 'Runtime.getRuntime().exec("ping " + host);', 'new ProcessBuilder("ping", "-c", "1", host).start();', 'shell-montado'),
    ('.java', 'conn.setHostnameVerifier((h, s) -> true);', 'conn.setSSLSocketFactory(ctx.getSocketFactory());', 'tls-desligado'),
    ('.php', '$db->query("SELECT * FROM users WHERE id = $id");', '$stmt = $db->prepare("SELECT * FROM users WHERE id = ?");', 'sql-interp-php'),
    ('.php', "$data = unserialize($_COOKIE['cart']);", "$data = json_decode($_COOKIE['cart'], true);", 'desserializacao'),
    ('.py', 'requests.get(url, verify=False)', 'requests.get(url, timeout=10)', 'tls-desligado'),
    ('.js', "out.innerHTML = new URLSearchParams(location.search).get('q');", "out.textContent = new URLSearchParams(location.search).get('q');", 'innerhtml'),
    ('.f90', "call execute_command_line('rm ' // trim(fname))", "call execute_command_line('ls')", 'shell-montado'),
    ('.sas', "call execute('proc sql; delete from t where id=' || id || '; quit;');", 'proc sql; delete from t where id = &id_ok; quit;', 'sql-concat-outros'),
    ('.abap', 'SELECT * FROM (lv_tab) WHERE (lv_where) INTO TABLE @lt.', 'SELECT * FROM zt WHERE id = @lv_id INTO TABLE @lt.', 'sql-dinamico-legado'),
    ('.conf', 'host all all 0.0.0.0/0 trust', 'host all all 10.0.0.0/8 scram-sha-256', 'pg-hba-trust'),
    ('.conf', 'host all all 0.0.0.0/0 trust', 'host all all 127.0.0.1/32 trust', 'pg-hba-trust'),
    ('.rules', 'allow read, write: if true;', 'allow read, write: if request.auth != null && request.auth.uid == userId;', 'firebase-regra-aberta'),
    ('.js', 'await User.findOne(req.body);', 'await User.findOne({ email: String(req.body.email) });', 'mongo-filtro-cru'),
    ('.cs', 'var cs = "Server=db;Encrypt=True;TrustServerCertificate=True;";', 'var cs = "Server=db;Encrypt=True;TrustServerCertificate=False;";', 'tls-desligado'),
    ('.cob', 'EXEC SQL EXECUTE IMMEDIATE :WS-SQL END-EXEC', 'EXEC SQL SELECT NOME INTO :WS-NOME FROM T WHERE ID = :WS-ID END-EXEC', 'sql-dinamico-legado'),
    ('.ex', 'Repo.query("SELECT * FROM u WHERE id = #{id}")', 'Repo.query("SELECT * FROM u WHERE id = $1", [id])', 'sql-interpolado'),
    ('.jl', 'DBInterface.execute(db, "SELECT * FROM t WHERE id = $id")', 'DBInterface.execute(db, "SELECT * FROM t WHERE id = ?", (id,))', 'sql-interpolado'),
    ('.swift', 'sqlite3_exec(db, "DELETE FROM t WHERE id = \\(id)", nil, nil, nil)', 'sqlite3_prepare_v2(db, "DELETE FROM t WHERE id = ?", -1, &stmt, nil)', 'sql-interpolado'),
    ('.scala', 'sql"SELECT * FROM u WHERE id = $id"', 'sql"SELECT * FROM u WHERE id = $id"', None),
    ('.groovy', 'sql.rows("select * from u where id = " + id)', 'sql.rows("select * from u where id = ${id}")', 'sql-concat'),
    ('.dockerfile', 'RUN curl -fsSL https://x/setup.sh | bash -', 'RUN curl -fsSL -o setup.sh https://x/setup.sh', 'shell-baixa-e-executa'),
]

# Commented-out insecure code is not a finding.
COMMENTED = [
    (".lua", '-- os.execute("ping " .. host)'),
    (".bas", "' CurrentDb.Execute \"DELETE FROM T WHERE Id = \" & x"),
    (".f90", "! call execute_command_line('rm ' // trim(f))"),
    (".prg", "// RUN (\"del \" + cArq)"),
    (".prg", "&& RUN (\"del \" + cArq)"),
    (".bat", "rem set password=Senha12345"),
    (".pl", '# system("rm $f");'),
    (".hs", '-- callCommand ("rm " ++ path)'),
]

# Ordinary code in each newly covered language: logging, messages and string building
# that only look like a command or a query. None of it may produce a HIGH finding.
NEGATIVE = [
    (".java", 'System.out.println("Total: " + total);'),
    (".java", 'String msg = String.format("Select one from %d options", n);'),
    (".kt", 'run { println("Hi $name") }'),
    (".kt", 'println("Please select one from the list, $name")'),
    (".kt", 'val q = """SELECT * FROM u WHERE id = ?"""'),
    (".pas", "ShowMessage('System: ' + s);"),
    (".pas", "Caption := 'Total: ' + IntToStr(N);"),
    (".pas", "Memo1.Lines.Add('Shell: ' + Versao);"),
    (".rb", 'puts "Shell: #{x}"'),
    (".rb", 'logger.info("Select an item from the menu, #{user}")'),
    (".rb", 'system("bundle", "exec", "rake")'),
    (".ex", 'IO.puts("Shell: #{x}")'),
    (".ex", 'Logger.info("select one from #{list} where needed")'),
    (".sh", 'eval "$(ssh-agent -s)"'),
    (".sh", 'echo "select one from the list, $USER"'),
    (".bas", 'MsgBox "Please select a file from the list: " & nome'),
    (".bas", 'lbl.Caption = "Shell: " & versao'),
    (".go", 'fmt.Printf("Select a file from %s\\n", dir)'),
    (".go", 'log.Println("select from cache " + key)'),
    (".r", "x <- a &(b > 1)"),
    (".r", 'load("dados.RData")'),
    (".r", 'message(paste("Select one from", n, "options"))'),
    (".scala", 'sql"""SELECT * FROM u WHERE id = $id"""'),
    (".scala", 'println(s"Select one from $n items")'),
    (".jl", "x = rand(1:10)"),
    (".jl", 'println("select from where you are, $name")'),
    (".lua", 'print("select item from " .. menu)'),
    (".lua", 'local cfg = load_config(path)'),
    (".pl", 'print "Shell: $x\\n";'),
    (".pl", 'my $sth = $dbh->prepare("SELECT * FROM users WHERE name = ?");'),
    (".hs", 'putStrLn ("system " ++ x)'),
    (".hs", 'putStrLn ("Select one from " ++ show n)'),
    (".ml", 'print_endline ("Shell: " ^ s)'),
    (".nim", 'echo "execCmd output: " & s'),
    (".d", 'writeln("executeShell: " ~ s);'),
    (".prg", 'cMsg := "RUN this report: " + cNome'),
    (".prg", "x := Eval( bBloco )"),
    (".clj", '(println "read-string is unsafe")'),
    (".groovy", 'println "Running ${env.BUILD_ID}"'),
    (".tcl", "set r [expr {$a + $b}]"),
    (".ps1", 'Write-Host "select one from the list, $name"'),
    (".cs", 'Console.WriteLine($"Select one from {n} items");'),
    (".dart", 'print("Select one from the list, $name");'),
    (".swift", 'print("Select one from the list, \\(name)")'),
    (".cr", 'puts "select one from #{list}"'),
    (".f90", "print *, 'Select one from ' // trim(menu)"),
]


def scan_dir(folder, high_only=False):
    proc = subprocess.run([sys.executable, "-I", str(SCANNER), "--json", str(folder)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    findings = {}
    for f in json.loads(proc.stdout)["findings"]:
        if high_only and f["severity"] != "HIGH":
            continue
        findings.setdefault(pathlib.Path(f["file"]).name, set()).add(f["rule"])
    return findings


class LanguageRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(cls._tmp.name)
        base = root / "cases"
        base.mkdir()
        for i, (ext, bad, safe, _rule) in enumerate(CASES):
            (base / ("bad%02d%s" % (i, ext))).write_text(bad + "\n", encoding="utf-8")
            (base / ("safe%02d%s" % (i, ext))).write_text(safe + "\n", encoding="utf-8")
        for i, (ext, line) in enumerate(COMMENTED):
            (base / ("comment%02d%s" % (i, ext))).write_text(line + "\n", encoding="utf-8")
        # A folder scan must pick these file types up by extension.
        cls.findings = scan_dir(base)
        neg = root / "negative"
        neg.mkdir()
        for i, (ext, line) in enumerate(NEGATIVE):
            (neg / ("ordinary%02d%s" % (i, ext))).write_text(line + "\n", encoding="utf-8")
        cls.high_on_ordinary = scan_dir(neg, high_only=True)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_insecure_lines_are_caught_by_the_expected_rule(self):
        for i, (ext, bad, _safe, rule) in enumerate(CASES):
            if rule is None:
                continue
            with self.subTest(ext=ext, line=bad):
                self.assertIn(rule, self.findings.get("bad%02d%s" % (i, ext), set()))

    def test_safe_lines_are_not_flagged(self):
        for i, (ext, _bad, safe, _rule) in enumerate(CASES):
            with self.subTest(ext=ext, line=safe):
                self.assertEqual(self.findings.get("safe%02d%s" % (i, ext), set()), set())

    def test_commented_code_is_not_flagged(self):
        for i, (ext, line) in enumerate(COMMENTED):
            with self.subTest(ext=ext, line=line):
                self.assertEqual(self.findings.get("comment%02d%s" % (i, ext), set()), set())

    def test_ordinary_code_has_no_high_finding(self):
        for i, (ext, line) in enumerate(NEGATIVE):
            with self.subTest(ext=ext, line=line):
                self.assertEqual(self.high_on_ordinary.get("ordinary%02d%s" % (i, ext), set()), set())


if __name__ == "__main__":
    unittest.main()
