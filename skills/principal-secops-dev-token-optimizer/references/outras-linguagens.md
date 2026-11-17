# Outras linguagens — Go, C#, Ruby, Rust, mobile, shell

Rule for any stack not covered by a dedicated reference: apply the security baseline, then follow the official style guide of that language's maintainers. State which guide is being followed, in one pt-BR line, only if the user asks.

## Go
* Style: `gofmt`, Effective Go, Go Code Review Comments. Errors returned and handled, never `_ =` on an error that matters.
* SQL: `database/sql` with placeholders. `fmt.Sprintf` into a query is injection.
* HTML output: `html/template`, never `text/template`, because only the former escapes by context.
* Commands: `exec.Command` with separate arguments. Never through a shell.
* Dependencies: `go.sum` committed, `govulncheck` in the build.
* Context with timeout on every outbound call.

## C# / .NET
* Style: Microsoft C# coding conventions. Target the current LTS of .NET.
* SQL: parameterized `SqlCommand` or Entity Framework with LINQ. Raw SQL only with `FromSqlInterpolated`, never string concatenation.
* Passwords: ASP.NET Core Identity's hasher, or Argon2 through a maintained package.
* Validation: data annotations plus explicit model validation. Never bind an entity straight from a request.
* Secrets: user-secrets in dev, environment or Key Vault in production. Never `appsettings.json` in the repo.
* Antiforgery tokens on every state-changing form. Authorization policies rather than scattered role checks.
* Dependencies: `dotnet list package --vulnerable` in the build.

## Ruby
* Style: the community Ruby Style Guide, plus Rails conventions when Rails is present.
* SQL: ActiveRecord with placeholders (`where("x = ?", v)`). String interpolation into `where` is injection.
* Mass assignment: strong parameters, always. Never `permit!`.
* Output: ERB escapes by default; `html_safe` and `raw` turn that off, so treat both as red flags.
* `bundle audit` on every dependency change. `Gemfile.lock` committed.
* Never `eval`, `send` with a user-supplied method name, or `Marshal.load` on untrusted data.

## Rust
Has its own reference: `rust.md`. Read that instead.

## C and C++
Have their own reference: `c-cpp.md`. For a desktop binary or a file parser, also `native-app-security.md`.

## Mobile (Android / iOS / Flutter / React Native)
* No secrets in the app binary. Anything shipped to a device is extractable.
* Sensitive data in the platform keystore or keychain, never in shared preferences or plist.
* Certificate pinning for APIs handling money or personal data.
* All authorization decisions server-side. The app is a client, not a source of truth.
* Permissions requested at the moment they are needed, with an explanation.

## Kotlin
* Style: the official Kotlin coding conventions (kotlinlang.org) and Android Kotlin style guide; `ktlint` or `detekt` in the build.
* Null safety: no `!!` on data that came from outside. Coroutines: structured concurrency, no `GlobalScope`, cancellation respected.
* SQL on Android: Room with `@Query` parameters. Secrets in the Android Keystore, never in `SharedPreferences` or the APK.

## PowerShell (Windows)
* Start scripts with `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'`. Follow the PowerShell Practice and Style guide: `Verb-Noun` names, `[CmdletBinding()]`, typed parameters with `[ValidateNotNullOrEmpty()]`, comment-based help.
* Never `Invoke-Expression` with text that came from outside, never `-ExecutionPolicy Bypass` in an instruction to the user, never `irm ... | iex` or `iwr ... | iex` (download and run).
* Secrets through `Read-Host -AsSecureString`, `SecretManagement` or environment variables, never inside the script.
* Build paths with `Join-Path` and always quote them. Use `-LiteralPath` when a name may contain `[` or `]`.
* For the non-programmer: say to open "Terminal" (not "cmd"), paste one command at a time, and what should appear. Before `Remove-Item -Recurse -Force`, show the full path and ask for the "pode" (see the destructive-actions rule in `SKILL.md`).
* Lint with `PSScriptAnalyzer` (`Invoke-ScriptAnalyzer -Path .`).

## Shell scripts
* `set -euo pipefail` at the top. Quote every variable expansion.
* Never build a command from unvalidated input. Never `curl ... | bash`.
* `mktemp` for temporary files. Trap for cleanup.
* For anything beyond about 50 lines, switch to Python. Shell error handling gets fragile fast.

## SQL other than MySQL (PostgreSQL, SQL Server, SQLite, Oracle, MongoDB, Redis)
Has its own reference: `bancos-outros.md`. The generic rules in `mysql.md` (parameterization, least privilege, indexing, `EXPLAIN` before tuning, backup before `ALTER`) still apply; the engine-specific syntax, security settings and tuning are in `bancos-outros.md`.
