# Scripts and automation: Lua, Perl, VBA, Apps Script, PowerShell, shell, batch, AutoHotkey, Tcl

Version policy: follow `versoes-e-fontes.md`. Read the version from the host, not from memory: `lua -v` or the embedding app's docs, `perl -v` and `use v5.x` in the code, Office build in File > Account, `runtimeVersion` in `appsscript.json`, `$PSVersionTable`, `bash --version`, `#Requires AutoHotkey` in the script, `info patchlevel` in Tcl. Lifecycles: endoflife.date (`lua`, `perl`, `powershell`), lua.org/versions.html, the PowerShell Support Lifecycle page on learn.microsoft.com, tcl-lang.org/software/tcltk, autohotkey.com/download, Microsoft 365 Apps release notes for VBA.

## Contents
- Running scripts safely on Windows (all stacks)
- Lua (5.x, LuaJIT, Luau, embedded)
- Perl
- VBA and Office macros (Excel, Access)
- Google Apps Script
- PowerShell
- Bash and POSIX shell
- Windows batch (.bat, .cmd)
- AutoHotkey v2
- Tcl
- File extensions

## Running scripts safely on Windows (all stacks)
* Files that arrive by browser or e-mail carry Mark of the Web (MOTW), a `Zone.Identifier` stream. Office blocks macros in them and PowerShell `RemoteSigned` refuses them unsigned. `curl.exe`, `Invoke-WebRequest` and `Invoke-RestMethod` may not set the mark, so a missing mark proves nothing.
* Unblock only after reading the file: right click > Propriedades > Desbloquear, or `Unblock-File -LiteralPath <arquivo>`. Never tell the user to unblock a file nobody has read.
* No administrator by default. Ask for "Executar como administrador" only when the task needs it, and say why in one line.
* Never hand the user a download-and-run line (`irm ... | iex`, `curl ... | bash`). Download, read, then run.
* Put the script in a folder of its own (`C:\Scripts\nome-do-script\`), never in Downloads or on the Desktop, and keep a copy before editing.
* Sample sentence: "Salve o arquivo em `C:\Scripts\relatorio\`, abra o Terminal nessa pasta e cole só esta linha. Se aparecer texto em vermelho, me mande o texto inteiro."
* Any batch file (`.bat`, `.cmd`) started with arguments from another program goes through `cmd.exe`, whose quoting rules differ from every runtime's escaping (BatBadBut, 2024: Rust, PHP, Node.js, Haskell and others fixed CVEs). Never pass untrusted text as an argument to a batch file; call the `.exe` directly and always give the file extension.

## Lua (5.x, LuaJIT, Luau, embedded)
Which Lua: PUC Lua (lua.org) 5.1 to 5.5; LuaJIT is upward-compatible with 5.1 plus selected 5.2 and 5.3 features; Luau (Roblox) is its own dialect. Ask which host runs the script; the host decides the version and the available libraries.
* Standards and style: StyLua formats 5.1 to 5.4, LuaJIT and Luau (config `stylua.toml` or `.stylua.toml`); confirm it parses 5.5 syntax before using it there. Luacheck (lunarmodules fork, supports 5.4) for unused and undefined globals. `local` by default; in 5.5 a `global` declaration makes every other name need a declaration (5.5+).
* Security, sandboxing `load`:
  * `load(chunk, name, "t", env)`: mode `"t"` accepts only source text. The default `"bt"` also accepts binary chunks, and the manual warns that crafted binary chunks can crash the interpreter. Same for `loadfile`. LuaJIT accepts `mode` and `env` too.
  * `env` is a fresh table holding only what the script may use (`{ math = { floor = math.floor, max = math.max }, print = safe_print }`). Never pass `_G`. Never expose `io`, `os`, `package`, `require`, `debug`, `load`, `loadfile`, `dofile`, `string.dump` or `collectgarbage` to untrusted code.
  * 5.1 code uses `setfenv`; 5.2+ removed `setfenv` and `getfenv`, the environment is `_ENV` or the `env` argument of `load` (LuaJIT also accepts `load` with `env`).
  * Library tables are shared. Hand the sandbox copies, or a script can replace `string.format` for everyone.
  * `os.execute` and `io.popen` run a shell command: never with text from outside.
* Embedded Lua (games, apps), on the host side in C:
  * Open only the libraries the scripts need. A separate `lua_State` per untrusted script, or per mod.
  * CPU limit: `lua_sethook` with `LUA_MASKCOUNT` to stop a script after N instructions. Memory limit: a custom `lua_Alloc` that returns `NULL` past the budget.
  * Luau already removes `io`, `package`, `load`, `string.dump`, most of `os` and `debug`, marks built-in tables read-only, and offers an interrupt callback for timeouts. It has no default memory limit, and `getfenv`/`setfenv` still exist and weaken isolation.
  * Bytecode from an untrusted source is never safe (PUC Lua, LuaJIT or Luau). Load source text only, or bytecode you signed.
* Exceptional conditions: `pcall` or `xpcall` around every untrusted call; on error, deny and log. Lua 5.5 replaces a `nil` error object with a message string (5.5+).
* Supply chain: LuaRocks. `luarocks build --pin` (or `make --pin`) writes `luarocks.lock`, which later builds treat as authoritative. Commit it.
* Tuning: locals over globals in hot loops; build strings with `table.concat`, not `..` in a loop; LuaJIT is the fast path only where its 5.1 dialect is acceptable.
* Traps and fixes:
  * 5.5 makes `global` a reserved word and the `for` control variable read-only. Code from 5.4 that uses either breaks; declare a local copy inside the loop.
  * Code written for 5.1 (`setfenv`, `loadstring`) fails on 5.2+. Keep the host's dialect, do not "upgrade" syntax.
  * A mod or config "is just data" but runs as code. Load it in a sandbox, never with plain `dofile`.
* Running on Windows: inside the host app (game console, editor plugin) whenever possible. For a standalone interpreter, ask which one the user already has before suggesting any download.

## Perl
* Standards and style: `use v5.36` or later turns on warnings and enables signatures (5.36+); still write `use strict;` explicitly. Lexical filehandles (`open(my $fh, ...)`), never barewords.
* Security:
  * Taint mode: `#!perl -T` for anything that takes outside input (CGI, server, setuid). Untaint only through a regex capture that matches known-good characters (`/^([-\@\w.]+)$/`), never "everything but bad characters".
  * Before `system` or `exec` under taint: set `$ENV{PATH}` to absolute, non-writable directories and `delete @ENV{qw(IFS CDPATH ENV BASH_ENV)}`.
  * Commands: list form only, `system('cmd', $arg1, $arg2)`, which skips the shell. Backticks and one-string `system` go through the shell. For output, `open(my $fh, '-|', 'cmd', @args)` (works on Windows from Perl 5.22).
  * Files: three-argument `open(my $fh, '<:encoding(UTF-8)', $path)`. Two-argument `open` treats `<`, `>` and `|` in the name as instructions.
  * SQL with DBI: `prepare` with `?` placeholders, values in `execute(@values)`. A placeholder is one scalar value, never a table or column name; pick identifiers from a fixed allowlist. `undef` binds NULL, and `= ?` never matches NULL rows (use `IS NULL`).
  * Never `eval` a string built from input. Regexes from user input can take exponential time; do not interpolate user text into a pattern without `\Q...\E`.
* Exceptional conditions: `DBI->connect` with `RaiseError => 1` and an explicit `AutoCommit` value. `eval { ...; 1 } or do { log; deny }`. Check every `open ... or die`.
* Supply chain: Carton with a committed `cpanfile.snapshot`. `cpan-audit deps .` (or `cpan-audit installed`) checks against a database bundled in CPAN::Audit, so update CPAN::Audit itself before trusting a clean result.
* Tuning: do not rely on hash key order (randomized per process); `List::Util::shuffle` for shuffling. Prepare a statement once and execute it many times.
* Traps and fixes: CGI script without `-T` that shells out with a form field: add `-T`, untaint, list-form `system`. Legacy two-argument `open` on uploaded file names: convert to three-argument, one call at a time.
* Running on Windows: perl.org points Windows users to Strawberry Perl. Run with `perl script.pl` from Terminal in the script's folder.

## VBA and Office macros (Excel, Access)
* Standards and style: `Option Explicit` at the top of every module. Save as `.xlsm`, `.xlam`, `.docm` or `.accdb`; `.xlsx` and `.docx` cannot hold macros.
* Macro security:
  * Office for Windows blocks VBA macros in files with MOTW (Access, Excel, PowerPoint, Project, Publisher, Visio, Word); the banner has no Enable button. The user unblocks a file they trust in Propriedades or with `Unblock-File`.
  * Trusted Locations bypass the check. Use one local folder that only the user can write to; Microsoft does not recommend network Trusted Locations.
  * Signing: sign the VBA project and install the certificate as Trusted Publisher; the strongest common setting is "Disable all except digitally signed macros" with "Require macros to be signed by a trusted publisher". A SelfCert certificate is trusted only on the machine that has it, so it is for personal use and testing. Signed `.xlam` add-ins that still carry MOTW stay blocked: unblock or use a Trusted Location.
  * Keep "Trust access to the VBA project object model" off; turn it on only for the run of a macro that needs it.
  * Keep "Enable Excel 4.0 macros when VBA macros are enabled" unchecked. XLM is legacy; migrate it to VBA.
  * Opening other workbooks from code: where the host offers `Application.AutomationSecurity`, set `msoAutomationSecurityForceDisable` before `Workbooks.Open` on files you did not create, and restore the old value after.
* SQL injection:
  * ADO: a `Command` object with parameters made by `CreateParameter(Name, Type, Direction, Size, Value)` and appended to `.Parameters`; variable-length types need `Size`. Never build `CommandText` with `&` and a cell value.
  * Access DAO: a parameter query (`PARAMETERS` clause) or a temporary `QueryDef` (`CreateQueryDef("")`), set `qdf.Parameters(...)` before `Execute dbFailOnError`, which rolls back on error.
  * SQL Server or other ODBC servers: DAO pass-through text goes to the server as written, so do not concatenate values into it; use the ADO `Command` with parameters above.
* Secrets: Microsoft's guidance is no hard-coded passwords; prompt for the password at run time or use Windows authentication on the database.
* Exceptional conditions: `On Error GoTo Handler` per procedure, `Exit Sub` before the handler, and a handler that logs, tells the user in plain words and leaves data unchanged. `On Error Resume Next` only around one object call, followed by a check of `Err.Number`, then `On Error GoTo 0`. DLL calls do not raise errors: check the return value and `Err.LastDLLError`.
* Traps and fixes:
  * Number concatenated into SQL on a pt-BR machine: `"PRECO > " & 125.5` becomes `125,50` and Access SQL fails, since it accepts only `.` as decimal separator. Parameters fix both this and injection.
  * VBScript is being deprecated in Windows. Office Version 2508+ includes RegExp classes in VBA by default, and late binding `CreateObject("VBScript.RegExp")` works there regardless of Windows version; early-bound references to the VBScript RegExp library break on older Office once VBScript is removed; calling `.vbs` files from VBA will no longer be supported. Check the Office build before touching regex code.
  * 32 vs 64-bit Office (64-bit is the default since Office 2019 and Microsoft 365): every `Declare` needs `PtrSafe`, and pointers and handles need `LongPtr`; adding `PtrSafe` alone compiles but truncates handles. Keep `#If VBA7 Then` branches for old Office.
* Safe maintenance and staged migration: export modules to text (`.bas`, `.cls`, `.frm`) and keep them in a folder or Git before changing anything; change one module at a time and test on a copy of the file; move data out of the workbook to Access or a server database before moving logic; never rewrite a working workbook in another language in one step.
* Running on Windows: keep the file in the Trusted Location folder, open it, run from Desenvolvedor > Macros. Sample sentence: "Se aparecer a faixa vermelha RISCO DE SEGURANÇA, não clique em nada: me avise antes."

## Google Apps Script
* Standards and style: V8 runtime only. Set `"runtimeVersion": "V8"` explicitly in `appsscript.json`: the manifest reference describes an omitted value (`STABLE`) as Rhino, and `DEPRECATED_ES5` pins Rhino. The migration guide says Rhino was deprecated on 2026-01-31 and Rhino scripts must move to V8.
* Security:
  * Scopes: list explicit, narrowest `oauthScopes` in the manifest; `/** @OnlyCurrentDoc */` limits Sheets, Docs, Slides and Forms access to the open file. Users may grant only some scopes: call `ScriptApp.requireScopes(...)` in flows and installable-trigger setup that need them.
  * Web app: `access` and `executeAs` decide everything. `ANYONE_ANONYMOUS` with `USER_DEPLOYING` lets anyone on the internet act with the owner's permissions: authenticate and authorize inside `doGet`/`doPost`, or use `DOMAIN` or `MYSELF`.
  * `google.script.run` can call every top-level server function. End internal helpers with `_` (private, hidden from the client) and validate every argument on the server; the client is hostile.
  * HtmlService templates: `<?= ?>` escapes by context; `<?!= ?>` does not, so only for content the script itself produced.
  * JDBC: `conn.prepareStatement(sql)` with `?` and `setString`; never concatenate. Prefer `Jdbc.getCloudSqlConnection` for Cloud SQL MySQL, which needs no public IP allowlist.
  * Secrets: Script Properties (`PropertiesService`), never in code. Treat project edit access as access to the secret: share editing only with people who may see it.
* Exceptional conditions: `try/catch` around `UrlFetchApp`, JDBC and Drive calls; log with `console.error`; return a generic message to the web client.
* Supply chain: libraries pinned to a version number, never HEAD (development mode) in production; anyone with edit access can change HEAD.
* Running on Windows: nothing to install; it runs at script.google.com in the browser. The first run shows the Google consent screen: read the permissions with the user before accepting.

## PowerShell
* Versions: PowerShell 7 (`pwsh`) is installed side by side with Windows PowerShell 5.1 (`powershell.exe`), which is part of Windows and follows its lifecycle. Check `$PSVersionTable.PSVersion` and the Support Lifecycle page; only the latest patch of a supported release is supported.
* Standards and style: `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'` at the top. Verb-Noun names with approved verbs, `[CmdletBinding()]`, typed parameters with `[ValidateNotNullOrEmpty()]`, comment-based help. Lint with PSScriptAnalyzer (`Invoke-ScriptAnalyzer -Path .`).
* Security:
  * `Invoke-Expression` (alias `iex`) is a last resort and never takes outside text; run commands with the call operator `&` and an argument array.
  * Never `irm ... | iex` or `iwr ... | iex` in an instruction.
  * Execution policy is not a security boundary. Never tell the user `-ExecutionPolicy Bypass` or `Set-ExecutionPolicy Unrestricted`. If a script is blocked, read it, `Unblock-File` it, or use `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` (Windows PowerShell 5.1 defaults to `Restricted` on client Windows; PowerShell 7 defaults to `RemoteSigned`).
  * Secrets: `Read-Host -AsSecureString`, a `[PSCredential]` parameter or environment variables, never in the script. PSScriptAnalyzer flags `ConvertTo-SecureString -AsPlainText`, plain-text password parameters and hardcoded computer names. The SecretManagement and SecretStore modules are feature complete and archived (security fixes only): fine to keep, not a new dependency.
  * Paths: `Join-Path`, always quoted; `-LiteralPath` when a name may contain `[` or `]`.
* Exceptional conditions: `try { } catch { }` with a log entry, never an empty `catch`. Native programs do not throw by default: check `$LASTEXITCODE`, or set `$PSNativeCommandUseErrorActionPreference = $true` (7.4+), and switch it off around tools like `robocopy` whose non-zero codes are not errors.
* Supply chain: install modules with PSResourceGet, pinned: `Save-PSResource -Name X -Version <versao> -AuthenticodeCheck -Path .\modules` keeps an exact copy in the project. Never `-TrustRepository` on an unknown repository.
* Encoding: PowerShell 7 writes `utf8NoBOM`. Windows PowerShell 5.1 reads a BOM-less script as ANSI, so accents in strings break: save scripts with non-ASCII text as UTF-8 with BOM, and pass `-Encoding utf8` to `Out-File` and `Set-Content` in 5.1.
* Traps and fixes: `Remove-Item -Recurse -Force $path` with an empty `$path` (strict mode plus a `Test-Path` guard and the full path shown before the "pode"); aliases in scripts (`ls`, `%`) hide intent, write full cmdlet names.
* Running on Windows: install PowerShell 7 with `winget install --id Microsoft.PowerShell --source winget`. Open "Terminal" (not "cmd"), `cd` into the script folder, run `.\script.ps1`. Paste one command at a time and say what should appear. Before any `Remove-Item -Recurse -Force`, show the full path and ask for the "pode" (destructive-actions rule in `SKILL.md`).

## Bash and POSIX shell
* Standards and style: `#!/usr/bin/env bash` for Bash, `#!/bin/sh` only for code that is truly POSIX. ShellCheck on every script; it reads the shebang and warns about non-portable syntax.
* Security:
  * Quote every expansion: `"$var"`, `"$@"` (ShellCheck SC2086). Unquoted variables split on spaces and expand wildcards.
  * Never `eval` text from outside: `eval` joins its arguments and runs them as a command. Build commands as arrays: `cmd=(rsync -a -- "$src" "$dst"); "${cmd[@]}"`.
  * Never `curl ... | bash`. Never build a command from unvalidated input.
  * Temporary files: `tmp=$(mktemp)` or `mktemp -d` (unpredictable name, readable only by the owner), never `/tmp/fixed-name`.
  * Secrets from environment variables or a file readable only by the owner, never written in the script.
* Exceptional conditions:
  * `set -euo pipefail` at the top, knowing its limits: `-e` is ignored inside `if`, `while`, `until`, after `!` and in every part of an `&&`/`||` list except the last. Check critical commands explicitly.
  * `cd dir || exit` (SC2164); `read -r` (SC2162).
  * `trap 'rm -rf -- "$tmp"' EXIT` for cleanup; an `ERR` trap runs before `-e` exits.
* Supply chain: pin tool versions in the install instructions; verify downloaded binaries by checksum before running them.
* Tuning: beyond about 50 lines, or once arrays of records appear, switch to Python. Shell error handling gets fragile fast.
* Running on Windows: WSL (`wsl --install` in an administrator PowerShell, then restart) or Git Bash. ShellCheck: `winget install --id koalaman.shellcheck`.

## Windows batch (.bat, .cmd)
* Standards and style: start with `@echo off` and `setlocal`, which keeps variable changes local and restores them at the end. Beyond simple launchers, write PowerShell instead.
* Security:
  * Any argument is code. `cmd.exe` expands `%VAR%` and treats `&`, `|`, `<`, `>`, `^` as operators, even inside values that came from outside. Use `"%~1"` (strips the caller's quotes, then re-quote yourself), never bare `%1`.
  * In `set`, escape `< > | & ^` with `^`. Quotes after the `=` become part of the value, so they are not a substitute for escaping.
  * `set /p` reads user input: validate it against an allowlist before using it in any command.
  * Delayed expansion (`setlocal enabledelayedexpansion`, `!var!`) treats `!` in data as syntax. Enable it only in the block that needs it.
  * Call programs by full path with extension (`"%~dp0tool.exe"`), so a planted `tool.bat` in the current folder does not run instead.
* Exceptional conditions: check after each important command, `if errorlevel 1 goto :fail` (true when the code is 1 or more), and end with `exit /b <código>` so the caller sees the failure.
* Traps and fixes: `if errorlevel 0` is always true (it means 0 or more); `call` does not accept pipes or redirection; `%var%` is substituted once, so for a value changed inside a `( ... )` block use `!var!` with delayed expansion. Special characters in arguments (`& | ( ) ^ < >`) need `^` or quotes.
* Running on Windows: double-click closes the window on error. Run from Terminal in the folder (`.\script.cmd`) so the user can copy the error text.

## AutoHotkey v2
* Versions: the download page lists v2 as the stable release and v1.1 under other releases. Write new scripts in v2 and start every file with `#Requires AutoHotkey v2.0`; v1 syntax does not run on v2.
* Security:
  * `Run` hands the string to `CreateProcess`, which searches the application directory before `WorkingDir`. Use full quoted paths (`Run '"C:\Program Files\App\app.exe" "' arg '"'`), never a bare name.
  * `Run A_ComSpec ' /c ...'` goes through `cmd.exe`: never with clipboard, window titles, file contents or other outside text.
  * Typing text from a variable: `SendText` (or `{Text}`), so `^ + ! # { }` in the data are not read as hotkeys.
  * `*RunAs` asks for administrator; only when needed.
  * No passwords in the script.
* Exceptional conditions: wrap `Run`, file and COM calls in `try`/`catch`; show a plain message, and do not continue a hotkey sequence after a failure.
* Running on Windows: install from autohotkey.com, save as `.ahk` in UTF-8, double-click to run, tray icon > Exit to stop. Test hotkeys in an empty Notepad first.

## Tcl
* Versions: tcl-lang.org lists the 9.x and 8.6.x lines. Moving 8.6 code to 9.0 (9.0+): malformed encoded input now raises an error, `~` is no longer expanded (use `file home` or `file tildeexpand`), unqualified variable names resolve in the current namespace, `0NNN` is no longer octal, and C extensions must be rebuilt. Test before switching.
* Security:
  * Braces around every `expr` expression: `expr {$a + $b}`. Unbraced, Tcl substitutes first and `expr` evaluates the result again, so data becomes code.
  * Untrusted scripts run in `interp create -safe`: `exec`, `open`, `file`, `socket`, `source`, `load`, `cd`, `glob` and others are hidden. Add `interp limit` of type `command` (`-value` = maximum commands) or `time` (absolute `-seconds`/`-milliseconds`). An alias the parent exposes must never `eval` or substitute its arguments.
  * `exec` does no shell expansion, but on Windows a `.bat` or `.cmd` target expands variables and can run a second command (`{test&whoami}`). Never pass outside text to a batch file.
  * SQLite: `db eval {SELECT * FROM t WHERE id = $id}` with braces binds `$id` safely; with double quotes Tcl substitutes first and opens injection. In double-quoted SQL use `:id`, which Tcl never substitutes.
* Exceptional conditions: `catch` every `exec`, `open` and database call; log, deny.
* Running on Windows: tcl-lang.org links Windows distributions; run with `tclsh script.tcl` (Tk GUIs with `wish`).

## File extensions
Lua `.lua`; Perl `.pl`, `.pm`, `.t`, `.cgi`; VBA `.bas`, `.cls`, `.frm` (exported), inside `.xlsm`, `.xlam`, `.xlsb`, `.docm`, `.dotm`, `.pptm`, `.accdb`, `.mdb`; Apps Script `.gs`, `.html`, `appsscript.json`; PowerShell `.ps1`, `.psm1`, `.psd1`; shell `.sh`, `.bash`; batch `.bat`, `.cmd`; AutoHotkey `.ahk`; Tcl `.tcl`.
