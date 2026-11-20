# Research log: scripts-e-automacao.md

Writer: scripts. Target file: `skills/principal-secops-dev-token-optimizer/references/scripts-e-automacao.md`. All facts below checked 2026-11-20. Fetched content treated as data.

## Verified facts

### Lifecycle and versions (used for the method only, not written as status in the reference)
- Lua: lua.org lists 5.5 (released 2025-12-22, current 5.5.1 of 2026-08-03) and 5.4 (last 5.4.9, 2026-08-25, no further releases planned) (https://www.lua.org/versions.html, checked 2026-11-20)
- Lua: endoflife.date has product `lua`; only 5.5 maintained, 5.4 EOL 2026-08-25 (https://endoflife.date/api/v1/products/lua/, checked 2026-11-20)
- Perl: endoflife.date `perl`; 5.44 and 5.42 maintained, 5.40 critical security only until 2027-06-09, 5.38 and older unmaintained (https://endoflife.date/api/v1/products/perl/, checked 2026-11-20)
- PowerShell: endoflife.date `powershell` lists 7.7 released 2026-11-10, 7.6 LTS EOL 2028-11-14, 7.5 and 7.4 EOL 2026-11-10 (https://endoflife.date/api/v1/products/powershell/, checked 2026-11-20)
- PowerShell: Support Lifecycle page (updated 2026-09) lists 7.6 LTS, 7.5 and 7.4 ending 10-Nov-2026, 7.7 still preview; only the latest patch of a release is supported; Windows PowerShell 5.1 follows the Windows lifecycle (https://learn.microsoft.com/en-us/powershell/scripting/install/powershell-support-lifecycle, checked 2026-11-20)
- Bash: newest tarball on ftp.gnu.org is bash-5.3 (2025-07-30) (https://ftp.gnu.org/gnu/bash/, checked 2026-11-20)
- Tcl: tcl-lang.org lists Tcl/Tk 9.1.0, 9.0.4 and 8.6.18 as latest releases (https://www.tcl-lang.org/software/tcltk/, checked 2026-11-20)
- AutoHotkey: download page "Latest Stable Version: 2.0.31"; v1.1 listed under Other Releases (https://www.autohotkey.com/download/, checked 2026-11-20)

### Shared Windows section
- Windows: MOTW added to files from Internet or Restricted zones, stored in `Zone.Identifier`; NTFS only (https://learn.microsoft.com/en-us/microsoft-365-apps/security/internet-macros-blocked, checked 2026-11-20)
- Windows: Unblock checkbox in Properties or `Unblock-File` removes the ZoneId (https://learn.microsoft.com/en-us/microsoft-365-apps/security/internet-macros-blocked, checked 2026-11-20)
- Windows: `curl.exe`, `Invoke-RestMethod`, `Invoke-WebRequest` may not mark files as Internet zone (https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies, checked 2026-11-20)
- Windows: BatBadBut: CreateProcess runs .bat/.cmd through cmd.exe whose escaping differs; advice to always specify the file extension and escape or avoid untrusted args (https://flatt.tech/research/posts/batbadbut-you-cant-securely-execute-commands-on-windows/, checked 2026-11-20)
- Windows: BatBadBut CVEs covered Rust (CVE-2024-24576), PHP, yt-dlp, Haskell; Node.js patched CVE-2024-27980 (https://www.securityweek.com/batbadbut-command-injection-vulnerability-affects-multiple-programming-languages/ via search summary, checked 2026-11-20)

### Lua
- Lua: 5.5 main features: global declarations, named vararg tables, compact arrays, incremental major GC (https://www.lua.org/versions.html, checked 2026-11-20)
- Lua: `load` mode "b", "t" or "bt", default "bt"; `env` sets the first upvalue (https://www.lua.org/manual/5.5/manual.html section 6.1, checked 2026-11-20)
- Lua: "maliciously crafted binary chunks can crash the interpreter" (https://www.lua.org/manual/5.5/manual.html, checked 2026-11-20)
- Lua: 5.5 `global` declarations; inside a `global` declaration all variables must be declared; `global` is a reserved word (compat `LUA_COMPAT_GLOBAL`); `for` control variable read-only; nil error object replaced by a string (https://www.lua.org/manual/5.5/manual.html sections 3.3.7 and 8, checked 2026-11-20)
- Lua: `os.execute`, `io.popen` (system dependent), `string.dump` exist in 5.5 (https://www.lua.org/manual/5.5/manual.html section 6, checked 2026-11-20)
- Lua: `lua_sethook` with `LUA_MASKCOUNT` called every count instructions; `lua_Alloc` returns NULL when it cannot fulfil a request (https://www.lua.org/manual/5.5/manual.html section 4, checked 2026-11-20)
- Lua: 5.2 removed `setfenv` and `getfenv`, deprecated `loadstring`; environments via `_ENV` or `load` (https://www.lua.org/manual/5.2/manual.html section 8, checked 2026-11-20)
- LuaJIT: rolling releases, v2.1 recommended for production (https://luajit.org/status.html, checked 2026-11-20)
- LuaJIT: fully upward-compatible with Lua 5.1, selected 5.2/5.3 features; `load` and `loadfile` accept mode and env, default "bt" (https://luajit.org/extensions.html, checked 2026-11-20)
- Luau: removes io, package, dofile/loadfile, string.dump and load; loadstring rejects bytecode; os trimmed; debug mostly removed; built-in tables readonly; interrupt callback for timeouts; no default memory limit; getfenv/setfenv kept; untrusted bytecode unsafe (https://luau.org/sandbox, checked 2026-11-20)
- StyLua: formats Lua 5.1 to 5.4, LuaJIT, Luau, CfxLua; config `stylua.toml` or `.stylua.toml`; 5.5 not mentioned (https://github.com/JohnnyMorganz/StyLua, checked 2026-11-20)
- Luacheck: maintained fork under lunarmodules, supports Lua 5.4 (https://github.com/lunarmodules/luacheck and Alpine packaging discussion via search, checked 2026-11-20)
- LuaRocks: `--pin` on build/make writes `luarocks.lock`, which later builds treat as authoritative (https://github.com/luarocks/luarocks/blob/main/docs/pinning_versions_with_a_lock_file.md, checked 2026-11-20)

### Perl
- Perl: `-T` taint mode, strongly suggested for server programs; untaint only via regex capture of known-good characters, example `/^([-\@\w.]+)$/` (https://perldoc.perl.org/perlsec, checked 2026-11-20)
- Perl: set `$ENV{PATH}` to known absolute dirs and `delete @ENV{qw(IFS CDPATH ENV BASH_ENV)}` (https://perldoc.perl.org/perlsec, checked 2026-11-20)
- Perl: list-form `system`/`exec` avoids the shell; hash order randomized; regex can take large time and memory; `List::Util::shuffle` (https://perldoc.perl.org/perlsec, checked 2026-11-20)
- Perl: three-argument open for arbitrary names; lexical filehandles; `<:encoding(UTF-8)`; list-form pipe open works on Windows with Perl 5.22+ (https://perldoc.perl.org/functions/open, checked 2026-11-20)
- Perl: DBI placeholders `?`, values in execute, not for table or column names, single scalar only, undef binds NULL and `= ?` does not match NULL; define AutoCommit explicitly; example uses `RaiseError => 1` (https://metacpan.org/pod/DBI, checked 2026-11-20)
- Perl: `use v5.36` enables warnings and signatures (https://perldoc.perl.org/perl5360delta and https://perldoc.perl.org/feature, checked 2026-11-20)
- Perl: CPAN::Audit `cpan-audit deps [dir]` reads cpanfile / Carton `cpanfile.snapshot`, `cpan-audit installed`; bundled database, no network, update often (https://github.com/briandfoy/cpan-audit and CPAN readme via search, checked 2026-11-20)
- Perl: perl.org points Windows users to Strawberry Perl (https://www.perl.org/get.html via search summary, checked 2026-11-20)

### VBA and Office
- VBA: macros in MOTW files blocked by default for Access, Excel, PowerPoint, Project, Publisher, Visio, Word on Windows; Security Risk banner without Enable content (https://learn.microsoft.com/en-us/microsoft-365-apps/security/internet-macros-blocked, checked 2026-11-20)
- VBA: Trusted Locations skip the MOTW check; manage sparingly; network Trusted Locations not recommended (https://learn.microsoft.com/en-us/microsoft-365-apps/security/internet-macros-blocked, checked 2026-11-20)
- VBA: signed macros with Trusted Publisher certificate open enabled; signature does not work for Excel add-ins with MOTW (https://learn.microsoft.com/en-us/microsoft-365-apps/security/internet-macros-blocked, checked 2026-11-20)
- VBA: recommended policy "Disable all except digitally signed macros" plus "Require macros to be signed by a trusted publisher" (https://learn.microsoft.com/en-us/microsoft-365-apps/security/internet-macros-blocked, checked 2026-11-20)
- VBA: "Trust access to the VBA project object model" is a hazard; check only for the duration of a macro that needs it; avoid hard-coded passwords (https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers, checked 2026-11-20)
- VBA: keep "Enable Excel 4.0 macros when VBA macros are enabled" unchecked; migrate XLM to VBA (https://learn.microsoft.com/microsoft-365/baseline-security-mode/disable-xl4-xlm-macros, checked 2026-11-20)
- VBA: `AutomationSecurity` with `msoAutomationSecurityForceDisable` disables macros in files opened programmatically (documented on https://learn.microsoft.com/office/vba/api/project.application.automationsecurity, checked 2026-11-20)
- VBA: SelfCert self-signed certificate trusted only on the machine where it is installed (https://support.microsoft.com/office/digitally-sign-your-macro-project-956e9cc8-bbf6-4365-8bfa-98505ecd1c01 via search summary, checked 2026-11-20)
- ADO: `CreateParameter(Name, Type, Direction, Size, Value)`; not appended automatically; variable-length types need Size (https://learn.microsoft.com/en-us/sql/ado/reference/ado-api/createparameter-method-ado, archived page, checked 2026-11-20)
- DAO: temporary QueryDef with zero-length name; set parameters before execution; `dbFailOnError` rolls back; concatenating a non-integer with a comma decimal separator makes Access SQL fail (https://learn.microsoft.com/office/client-developer/access/desktop-database-reference/querydef-sql-property-dao ; https://learn.microsoft.com/office/client-developer/access/desktop-database-reference/database-createquerydef-method-dao; https://learn.microsoft.com/office/client-developer/access/desktop-database-reference/querydef-execute-method-dao, checked 2026-11-20)
- VBA: macro-enabled formats .docm/.dotm (Word), .xlsm/.xltm/.xlam (Excel), .pptm/.potm/.ppam/.ppsm (PowerPoint) (https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers, checked 2026-11-20)
- VBA: Office 2508+ includes RegExp classes by default; late binding `CreateObject("VBScript.RegExp")` works on 2508+ regardless of Windows version; references to the VBScript RegExp library break unless Office is updated; calling .vbs from VBA no longer supported in Phase 3 (https://devblogs.microsoft.com/microsoft365dev/how-to-prepare-vba-projects-for-vbscript-deprecation/, checked 2026-11-20)
- VBA: 64-bit needs `PtrSafe` on every Declare plus `LongPtr`/`LongLong`; `PtrSafe` alone truncates; `#If VBA7`; 64-bit default since Office 2019 and Microsoft 365 (https://learn.microsoft.com/office/vba/language/concepts/getting-started/64-bit-visual-basic-for-applications-overview, checked 2026-11-20)
- VBA: `Option Explicit` forces declaration; `On Error GoTo`, `On Error Resume Next` preferable for object access with Err check, `On Error GoTo 0`, `Exit Sub` before handler; DLL errors via `LastDLLError` (https://learn.microsoft.com/office/vba/language/reference/user-interface-help/on-error-statement; https://learn.microsoft.com/office/vba/language/reference/user-interface-help/option-explicit-statement, checked 2026-11-20)

### Google Apps Script
- Apps Script: Rhino deprecated on January 31, 2026, migrate to V8; runtime checked via manifest `runtimeVersion` (https://developers.google.com/apps-script/guides/v8-runtime/migration, checked 2026-11-20)
- Apps Script: manifest `runtimeVersion` values `STABLE` (default when omitted, described as Rhino), `V8`, `DEPRECATED_ES5` (Rhino, prevents automatic migration) (https://developers.google.com/apps-script/manifest, checked 2026-11-20)
- Apps Script: `oauthScopes` manifest field, narrowest scopes; users can grant only some scopes; `ScriptApp.requireScopes`, `requireAllScopes`, `getAuthorizationInfo` (https://developers.google.com/apps-script/concepts/scopes, checked 2026-11-20)
- Apps Script: `@OnlyCurrentDoc` limits access to the current file (https://developers.google.com/apps-script/guides/services/authorization, checked 2026-11-20)
- Apps Script: webapp `access` MYSELF, DOMAIN, ANYONE, ANYONE_ANONYMOUS; `executeAs` USER_ACCESSING, USER_DEPLOYING (https://developers.google.com/apps-script/manifest/web-app-api-executable, checked 2026-11-20)
- Apps Script: functions ending with `_` are private and not callable by google.script; public names discoverable (https://developers.google.com/apps-script/guides/html/communication, checked 2026-11-20)
- Apps Script: `<?= ?>` contextual escaping, `<?!= ?>` no escaping (https://developers.google.com/apps-script/guides/html/templates, checked 2026-11-20)
- Apps Script: JDBC `prepareStatement` with `?` and `setString` against SQL injection; `getCloudSqlConnection` without IP allowlist (https://developers.google.com/apps-script/guides/jdbc, checked 2026-11-20)
- Apps Script: Script Properties for app-wide config such as DB credentials (https://developers.google.com/apps-script/guides/properties, checked 2026-11-20)
- Apps Script: libraries: share versioned deployments; anyone with editor access can use HEAD (https://developers.google.com/apps-script/guides/libraries, checked 2026-11-20)

### PowerShell
- PowerShell: execution policy is not a security boundary; RemoteSigned default for Windows in 7.6 docs; Restricted default for Windows clients in 5.1 docs; `-Scope CurrentUser`; `Unblock-File` (https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1; https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.6, checked 2026-11-20)
- PowerShell: Invoke-Expression last resort; call operator is safer (https://learn.microsoft.com/powershell/scripting/learn/deep-dives/avoid-using-invoke-expression; https://learn.microsoft.com/powershell/module/microsoft.powershell.utility/invoke-expression, checked 2026-11-20)
- PowerShell: PSScriptAnalyzer rules AvoidUsingInvokeExpression, AvoidUsingPlainTextForPassword, AvoidUsingConvertToSecureStringWithPlainText, AvoidUsingUsernameAndPasswordParams, AvoidUsingComputerNameHardcoded, AvoidUsingEmptyCatchBlock, AvoidUsingCmdletAliases, UseApprovedVerbs (https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/rules/readme, checked 2026-11-20)
- PowerShell: `Set-StrictMode -Version`, no extra rules above 3.0 (https://learn.microsoft.com/powershell/module/microsoft.powershell.core/set-strictmode, checked 2026-11-20)
- PowerShell: `$PSNativeCommandUseErrorActionPreference` default `$false`, added in 7.4; robocopy example (https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_preference_variables, checked 2026-11-20)
- PowerShell: SecretManagement and SecretStore feature complete, no longer actively developed, repository archived, security fixes only (https://learn.microsoft.com/powershell/module/microsoft.powershell.secretmanagement/set-secret, checked 2026-11-20)
- PowerShell: `Save-PSResource` with `-Version`, `-Path`, `-AuthenticodeCheck`, `-TrustRepository` (https://learn.microsoft.com/powershell/module/microsoft.powershell.psresourceget/save-psresource, checked 2026-11-20)
- PowerShell: 7 defaults to utf8NoBOM; 5.1 reads BOM-less scripts as ANSI; save non-ASCII scripts as UTF-8 with BOM (https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding, checked 2026-11-20)
- PowerShell: `-LiteralPath` treats brackets literally (https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_wildcards, checked 2026-11-20)
- PowerShell: `Read-Host -AsSecureString` returns a SecureString and masks input; recommended over `ConvertTo-SecureString -AsPlainText` (https://learn.microsoft.com/powershell/module/microsoft.powershell.utility/read-host; https://learn.microsoft.com/powershell/utility-modules/psscriptanalyzer/rules/avoidusingconverttosecurestringwithplaintext, checked 2026-11-20)
- PowerShell: `Join-Path` combines paths (https://learn.microsoft.com/powershell/module/microsoft.powershell.management/join-path, checked 2026-11-20)
- PowerShell: `winget install --id Microsoft.PowerShell --source winget` (https://learn.microsoft.com/powershell/scripting/install/install-powershell-on-windows, checked 2026-11-20)

### Bash and POSIX shell
- Shell: POSIX `-e` ignored in while/until/if/elif conditions, after `!`, and in AND-OR lists except the last; `-u` errors on unset parameters (https://man7.org/linux/man-pages/man1/set.1p.html, checked 2026-11-20)
- Bash: pipefail return status is that of the last command to exit non-zero (https://man7.org/linux/man-pages/man1/bash.1.html, checked 2026-11-20)
- Bash: trap on EXIT runs before the shell terminates; ERR trap runs before `-e` exits; `eval` concatenates args and executes (https://man7.org/linux/man-pages/man1/bash.1.html, checked 2026-11-20)
- ShellCheck: SC2086 "Double quote to prevent globbing and word splitting" (https://github.com/koalaman/shellcheck/wiki/SC2086, checked 2026-11-20)
- ShellCheck: SC2164 use `cd ... || exit` (https://github.com/koalaman/shellcheck/wiki/SC2164, checked 2026-11-20)
- ShellCheck: SC2162 read without -r mangles backslashes (https://github.com/koalaman/shellcheck/wiki/SC2162, checked 2026-11-20)
- ShellCheck: Windows install `winget install --id koalaman.shellcheck`; checks bash/sh with portability warnings by shebang (https://github.com/koalaman/shellcheck, checked 2026-11-20)
- coreutils: mktemp creates file or `-d` directory safely, owner-only by default (https://www.gnu.org/software/coreutils/manual/html_node/mktemp-invocation.html, checked 2026-11-20)
- WSL: `wsl --install` in administrator PowerShell, then restart (https://learn.microsoft.com/windows/wsl/install, checked 2026-11-20)

### Windows batch
- Batch: `setlocal` localizes environment until endlocal or end of file; enabledelayedexpansion option (https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/setlocal, checked 2026-11-20)
- Batch: `set /p` reads user input; `< > | & ^` need `^` or quotes, quotes become part of the value (https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1, checked 2026-11-20)
- Batch: `%~1` removes surrounding quotes, `%~dp0`-style modifiers; call does not accept pipes or redirection (https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/call, checked 2026-11-20)
- Batch: `exit /b <code>` sets ERRORLEVEL (https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/exit, checked 2026-11-20)
- Batch: `if errorlevel N` true when code is equal to or greater than N (https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/if, checked 2026-11-20)
- Batch: `/v:on` delayed expansion uses `!` at run time; `%var%` substitution not recursive; `& | ( )` need `^` or quotes (https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd, checked 2026-11-20)

### AutoHotkey
- AHK: `#Requires AutoHotkey v2.0` errors and quits when version not met (https://www.autohotkey.com/docs/v2/lib/_Requires.htm, checked 2026-11-20)
- AHK: `Run` passes target to CreateProcess, which checks the application directory before WorkingDir; quote paths; `A_ComSpec /c` for redirection; `*RunAs` (https://www.autohotkey.com/docs/v2/lib/Run.htm, checked 2026-11-20)
- AHK: `SendText` and `{Text}` send characters literally; `^+!#{}` special otherwise (https://www.autohotkey.com/docs/v2/lib/Send.htm, checked 2026-11-20)

### Tcl
- Tcl: `interp create -safe` hides cd, encoding, exec, exit, fconfigure, file, glob, load, open, pwd, socket, source, unload, zipfs; `interp limit` types `command` (set with `-value`) and `time` (absolute `-seconds`/`-milliseconds`); alias args must never be evaluated (https://www.tcl-lang.org/man/tcl9.0/TclCmd/interp.html, checked 2026-11-20)
- Tcl: brace `expr` expressions to avoid double substitution (https://www.tcl-lang.org/man/tcl9.0/TclCmd/expr.html, checked 2026-11-20)
- Tcl: `exec` does no shell expansion; on Windows .bat/.cmd expand variables, `{test&whoami}` example (https://www.tcl-lang.org/man/tcl9.0/TclCmd/exec.html, checked 2026-11-20)
- Tcl: SQLite `eval` binds `$var`, `:var`, `@var`; double quotes let Tcl substitute `$` and open injection; `:var` never substituted (https://www.sqlite.org/tclsqlite.html, checked 2026-11-20)
- Tcl: 9.0 incompatibilities: strict encoding errors, no `~` expansion (`file home`, `file tildeexpand`), namespace variable resolution, `0NNN` not octal, extensions must be rebuilt (https://www.tcl-lang.org/software/tcltk/9.0.html, checked 2026-11-20)

## Changed from the previous text
Source: PowerShell and Shell scripts sections of `references/outras-linguagens.md` (not edited; the lead should remove those two sections and point to the new file).
- PowerShell: kept every old rule (StrictMode, ErrorActionPreference Stop, Verb-Noun, CmdletBinding, ValidateNotNullOrEmpty, comment-based help, no Invoke-Expression, no Bypass, no irm/iwr | iex, secrets, Join-Path, LiteralPath, Terminal guidance, destructive "pode", PSScriptAnalyzer).
- PowerShell: SecretManagement no longer recommended as a new dependency (archived, feature complete).
- PowerShell: added version split (pwsh 7 vs Windows PowerShell 5.1), execution policy is not a security boundary, safe alternative to Bypass (`RemoteSigned -Scope CurrentUser`, `Unblock-File`).
- PowerShell: added native exit codes (`$LASTEXITCODE`, `$PSNativeCommandUseErrorActionPreference` 7.4+), module pinning via `Save-PSResource -Version -AuthenticodeCheck`, UTF-8 BOM trap for accents in 5.1, winget install line.
- Shell: kept `set -euo pipefail`, quoting, no command from unvalidated input, no `curl | bash`, mktemp, trap, the 50-line switch to Python.
- Shell: added the documented limits of `-e`, ShellCheck with three codes, arrays instead of eval, `cd || exit`, `read -r`, secrets handling, WSL and Git Bash on Windows.
- New sections: shared Windows safe-run rules, Lua, Perl, VBA and Office macros, Google Apps Script, Windows batch, AutoHotkey v2, Tcl, file extension list.

## Not verified (left out or worded without the identifier)
- Raku: rakudo.org and raku.org did not show a release, package manager or process APIs. Section dropped.
- Perl: `-t` switch, no-taint build symbols, `quote_identifier`, whether `use v5.36` enables strict (reference keeps `use strict;` explicit), Perl::Critic and Perl::Tidy (not written), Strawberry Perl current version.
- Lua: StyLua support for 5.5 syntax (reference says to confirm), `luaL_openselectedlibs` and other library-opening API names (not written), Windows standalone interpreter distributions.
- VBA: literal `?` marker in ADO CommandText and `ad*` constants (not written); VBScript phase dates (only the RegExp build and .vbs call change written).
- AutoHotkey: official v1.1 end-of-life post (forum returned 403); Ahk2Exe behavior and antivirus false positives.
- Shell: shfmt; GNU bash manual pages returned HTTP 429, so man7.org copies were used.
- Tcl: Windows distribution names (reference points to tcl-lang.org links only).
- Apps Script: clasp CLI; whether editors can read Script Properties (reference words it as edit access implies trust).
- Time-sensitive conflicts kept out of the reference: PowerShell 7.7 shown as released on endoflife.date but as preview on Learn (page updated 2026-09); VBScript phase dates differ between sources. Rhino: the reference states only what the official migration guide says (deprecated 2026-01-31, must migrate); the manifest page still calls the omitted default `STABLE` Rhino, so the reference tells to set `V8` explicitly.
- DAO pass-through parameters: not confirmed that pass-through QueryDefs accept parameters, so the reference points to the ADO Command route instead.
- Language basics written in the reference but not separately fetched today (stable, version-independent): Lua `pcall`, `xpcall`, `table.concat`, `lua -v`; Perl `\Q...\E`, `perl -v`, `eval { }` block form, Carton as a tool name (only its `cpanfile.snapshot` is in the CPAN::Audit docs); Apps Script `doGet`/`doPost`, `UrlFetchApp`, `console.error`, `ScriptApp`; Bash `bash --version`, arrays `"${cmd[@]}"`, `#!/usr/bin/env bash`; PowerShell `$PSVersionTable`, `[CmdletBinding()]`, `[ValidateNotNullOrEmpty()]`, `Test-Path`, `Out-File`/`Set-Content -Encoding`; Tcl `info patchlevel`, `tclsh`, `wish`, `catch`; batch `@echo off`; AutoHotkey `try`/`catch`, tray Exit; file extensions `.t`, `.cgi`, `.pm`, `.bas`, `.cls`, `.frm`, `.xlsb`, `.accdb`, `.mdb`, `.gs`, `.psd1`.
