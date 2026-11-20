# Scanner suggestions collected from the writers (v2.2.0)

## legado
- Delphi/Pascal (.pas .dpr .dpk .dfm .pp .lpr .inc): SQL.Text/SQL.Add built with `+` and a control/var (`'... = ''' + Edit1.Text + ''''`) vs safe `:c` + ParamByName. Literal `Password=` in Params/connection strings vs LoadSecret(). Cert check handler setting `Accepted := True` unconditionally.
- Harbour/Clipper/VFP (.prg .ch): macro `&(cVar)` / `&cVar` on input vs Eval(block). SQL concat `"SELECT ... '" + cVal + "'"` into exec; VFP `SQLEXEC(h, "... '" + var + "'")` vs `?var`.
- VB6/VBA (.bas .frm .cls): `.Open "SELECT ... '" & txt.Text & "'"` / `.Execute "..." & var` vs CreateParameter. `Pwd=`/`Password=` literal in connection string.
- COBOL (.cob .cbl .cpy): EXECUTE IMMEDIATE of STRING-built text vs static host vars.
- RPG (.rpgle .sqlrpgle): `EXECUTE IMMEDIATE :stmt` built with `+ %trim(input)` vs PREPARE ? USING.
- PowerBuilder: EXECUTE IMMEDIATE :ls_sql concatenated vs PREPARE SQLSA ? USING.
- ABAP (.abap): `WHERE (lv_where)` built with && / CONCATENATE without cl_abap_dyn_prg vs `@lv`. `IF sy-uname = '...'` as authorization.
- OpenEdge: QUERY-PREPARE("... '" + cInput + "'") vs static FOR EACH.
- Collisions: .prg (Harbour/VFP, same xBase rules), .cls (VB6/OpenEdge/Apex), .inc/.p generic.

## dados
- R (.R .r .Rmd .qmd): dbGetQuery/dbExecute/dbSendQuery(con, paste0/paste/sprintf(...)) vs params=list(). eval(parse(text = var)). system(paste...) vs system2+shQuote.
- Julia (.jl): eval(Meta.parse(var)); run(`sh -c $x`) / bash -c with interpolation.
- MATLAB/Octave (.m, collides with Objective-C: detect @interface/#import): eval([... var]) ; system([... var]) / strcat.
- Fortran (.f90 .f95 .f03 .f08 .f .for .F90): execute_command_line('...' // var).
- SAS (.sas): x "...&macro..."; / call system with macro var.
- pandas (.py): df.query/df.eval(f"...{x}...") vs "@var"; pd.read_pickle(var) MEDIUM.
- Jupyter (.ipynb): run secret rules on JSON cell sources.
- DuckDB (.py): con.execute(f"...{x}") / duckdb.sql(f"...") vs ? params.

## nativo
- C/C++: system()/popen() with non-literal arg (existing rule? check). printf/syslog with variable format. CURLOPT_SSL_VERIFYPEER 0 / SSL_VERIFY_NONE. gets(.
- Rust (.rs): sqlx::query(&format!(...)) ; Command::new("sh"|"bash").arg("-c").arg(format!) ; danger_accept_invalid_certs(true) / tls_danger_accept_invalid_certs(true).
- Zig (.zig): @setRuntimeSafety(false) MEDIUM.
- Ada (.adb .ads .gpr): pragma Suppress (All_Checks) / -gnatp.
- Objective-C (.m .mm): NSLog(var) ; stringWithFormat SQL into sqlite3_exec ; Info.plist NSAllowsArbitraryLoads true.
- D (.d): executeShell/spawnShell("..." ~ var).
- Nim (.nim): execProcess/execCmd("..." & var) ; sql("..." & var & "...").

## outras
- Go (.go): db.Query/Exec/QueryRow(fmt.Sprintf(...)|"..."+x) ; exec.Command("sh"|"bash","-c",...+x) ; InsecureSkipVerify: true.
- C# (.cs .cshtml .razor): FromSqlRaw/ExecuteSqlRaw($"...{x}" or + x) (do NOT flag FromSql($ / FromSqlInterpolated($) ; new SqlCommand("..." + x ; ServerCertificateCustomValidationCallback = ... => true ; new BinaryFormatter(.
- F# (.fs .fsx), VB.NET (.vb).
- Ruby (.rb .rake .erb): where(/find_by_sql(/order("...#{...}") vs ? ; backticks/system/exec/%x with #{} ; eval(params / Marshal.load(.
- Kotlin (.kt .kts): rawQuery("...$name...") ; trust-all checkServerTrusted {} / hostnameVerifier { _, _ -> true } ; Runtime.getRuntime().exec("sh -c " + x).
- Swift (.swift): literal apiKey/password ; Process /bin/sh -c interpolation ; .useCredential without trust check.
- Dart (.dart): rawQuery("...$id") ; badCertificateCallback = ... => true ; Process.run('sh', ['-c', "...$x"]).
- Scala (.scala .sc .sbt): Fragment.const(s"...$x") (fr"" safe) ; executeQuery(s"...$x") ; Seq("sh","-c",s"...").!.
- Elixir/Erlang (.ex .exs .erl): String.to_atom(params / list_to_atom ; :erlang.binary_to_term( without :safe ; :os.cmd( with #{} . Ecto ^ safe.
- Clojure (.clj .cljs .cljc): (read-string on req ; jdbc/execute! [(str "select..." id)] ; (eval.
- Haskell (.hs): fromString ("SELECT..." ++ ; callCommand/system ("..." ++ ; password literal.
- OCaml (.ml): Sys.command/Unix.system with ^ or sprintf ; Marshal.from_channel ; sprintf SQL.
- Groovy/Jenkins (.groovy .gradle Jenkinsfile): sh "...${params.|${env." ; sql.rows("..." + id) (GString safe) ; Eval.me( / GroovyShell().evaluate(.
- Crystal (.cr): db.exec/query "...#{x}" ; Process.run(..., shell: true) with #{} ; backticks #{}.
- Mobile: AndroidManifest usesCleartextTraffic="true" / base-config cleartextTrafficPermitted="true" ; Info.plist NSAllowsArbitraryLoads true ; EXPO_PUBLIC_*SECRET|PRIVATE_KEY.

## scripts
- PowerShell (.ps1 .psm1 .psd1): Invoke-Expression/iex with variable or "...$x..." vs & cmd -LiteralPath ; ConvertTo-SecureString "literal" -AsPlainText ; irm/iwr ... | iex.
- Bash (.sh .bash): eval "$var" ; curl/wget ... | bash|sh ; curl -k / --insecure.
- Perl (.pl .pm .t .cgi): prepare/do/selectall_*("...'$name'...") vs '?' ; system("... $x") one-string / backticks with $ ; open(FH, $path) two-arg.
- Lua (.lua, comment --): loadstring( / load(x) single arg vs load(x,"n","t",env) ; os.execute/io.popen(".." .. x).
- VBA (.bas .cls .frm, comment '): CommandText =/.Execute "/OpenRecordset("/.SQL = with "..." & var vs Parameters.
- Tcl (.tcl): expr $a without braces ; db eval "...$id" vs {...}.
- AutoHotkey (.ahk, comment ;): Run A_ComSpec ' /c ...' var.
- Apps Script (.gs .html): <?!= x ?> ; sql-concat already.
- Batch (.bat .cmd, comment rem/::): set password=... literal.
