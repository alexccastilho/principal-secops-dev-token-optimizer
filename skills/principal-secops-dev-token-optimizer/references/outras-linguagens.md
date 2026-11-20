# Other application languages: Go, .NET, Ruby, Kotlin, Swift, Dart, Scala, BEAM, Clojure, Haskell, OCaml, Groovy, Crystal, mobile

Version policy: follow `versoes-e-fontes.md`. Read the version from the manifest (`go.mod`, `<TargetFramework>` and `global.json`, `.ruby-version` or `Gemfile`, Gradle files, `Package.swift`, `pubspec.yaml` `environment.sdk`, `build.sbt`, `mix.exs`, `deps.edn`, `*.cabal`, `*.opam`, `shard.yml`) and check the lifecycle at endoflife.date (products `go`, `dotnet`, `dotnetfx`, `ruby`, `rails`, `kotlin`, `scala`, `elixir`, `erlang`, `ghc`, `apache-groovy`, `android`, `ios`, `react-native`) or the maintainer page named in each section.

Rule for any stack not covered by a dedicated reference: apply the security baseline, then follow the official style guide of that language's maintainers. State which guide is being followed, in one pt-BR line, only if the user asks.

PowerShell, shell scripts and other automation scripts: see `scripts-e-automacao.md`.

## Contents
- Go
- C# / .NET (F#, VB.NET)
- Ruby and Rails
- Kotlin
- Swift
- Dart and Flutter app code
- Scala
- Elixir, Erlang, Phoenix
- Clojure
- Haskell
- OCaml
- Groovy
- Crystal
- Mobile (Android, iOS, Flutter, React Native)

## Go
Lifecycle: go.dev/doc/devel/release. Each major release is supported until two newer majors ship; older ones get no security fixes.
* Style: `gofmt`, Effective Go, Go Code Review Comments. `go vet` and Staticcheck in CI.
* SQL: `database/sql` with placeholders. `fmt.Sprintf` or `+` into a query is injection.
* HTML: `html/template` (contextual escaping), never `text/template` for pages. `template.HTML(x)` is output verbatim, so only for trusted constants.
* Commands: `exec.Command(name, args...)` with separate arguments. Never `sh -c` with external text.
* Paths: `os.OpenRoot` / `os.Root` (1.24+) to keep file access inside one directory, symlinks included. Before 1.24: resolve symlinks first, then check the result is still inside the base directory; a plain prefix test on the raw string is not enough.
* Random: `crypto/rand` for tokens (`rand.Text`, 1.24+). `math/rand` is not for secrets. Passwords: `golang.org/x/crypto/bcrypt` or `argon2`.
* Errors: every `err` checked and returned with context (`fmt.Errorf("...: %w", err)`). Never `_ =` on an error that matters. A failed auth check returns a denial, not a zero value that passes.
* Network: `context` with timeout on every outbound call. Server and client timeouts set explicitly; no unbounded request reads.
* Supply chain: `go.sum` committed, `govulncheck ./...` in CI (`go install golang.org/x/vuln/cmd/govulncheck@latest`). Builds do not rewrite `go.mod` (read-only mode is the default). Track tool deps with the `tool` directive (1.24+) instead of a `tools.go` file.
* Tuning: measure with the built-in profiler before optimizing; one query with a join beats a query per row; reuse one HTTP client.
* Traps: goroutine leaks (no cancel path); a `nil` map write panics; `defer` inside a loop holds resources until the function returns.

## C# / .NET (F#, VB.NET)
Lifecycle: dotnet.microsoft.com/platform/support/policy. Even releases are LTS (3 years), odd are STS (2 years). .NET Framework (`dotnetfx`) follows Microsoft's Component Lifecycle Policy, tied to the Windows version it ships with (learn.microsoft.com/lifecycle); maintenance only, never the target for new code.
* Style: Microsoft C# coding conventions, `dotnet format`, `.editorconfig`. Roslyn analyzers are on by default for .NET 5+; raise with `<AnalysisMode>Recommended</AnalysisMode>` and `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>`. Nullable reference types on (`<Nullable>enable</Nullable>`).
* SQL: parameterized `SqlCommand`, or EF Core LINQ. Raw SQL only through `FromSql` / `ExecuteSql` (EF Core 7.0+) or `FromSqlInterpolated` / `ExecuteSqlInterpolated` (3.0+), which turn `{value}` into parameters. `FromSqlRaw` / `ExecuteSqlRaw` with `$"..."` or `+` is injection.
* Deserialization: `BinaryFormatter` cannot be made safe and throws from .NET 9 on; same family: `SoapFormatter`, `NetDataContractSerializer`, `LosFormatter`, `ObjectStateFormatter`. Use `System.Text.Json`. Json.NET: `TypeNameHandling` stays `None` (analyzer CA2326), or a restricting `ISerializationBinder`.
* Passwords: ASP.NET Core Identity's password hasher, or Argon2 through a maintained package. Never a bare SHA hash.
* CSRF: `[AutoValidateAntiforgeryToken]` globally for MVC and Razor Pages; minimal APIs with form binding validate antiforgery by default (ASP.NET Core 8+), so never add `.DisableAntiforgery()` to a cookie-authenticated form endpoint.
* Secrets: `dotnet user-secrets` in development only (stored unencrypted in the user profile). Production: environment or a vault (Azure Key Vault). Never passwords in `appsettings.json`.
* Validation: data annotations plus explicit checks. Bind to DTOs, never an entity straight from the request (over-posting). Authorization policies, not scattered role checks.
* Errors: generic error page or response in production, never the developer exception page. `catch (Exception)` only at the top boundary, logged.
* Supply chain: NuGet audit runs on `restore` (.NET 8 SDK+); set `<NuGetAuditMode>all</NuGetAuditMode>` for transitive packages on targets before net10.0 (default there is `direct`). `dotnet list package --vulnerable --include-transitive`. Central Package Management (`Directory.Packages.props`) for multi-project solutions. `packages.lock.json` (`RestorePackagesWithLockFile`) and `dotnet restore --locked-mode` in CI.
* F#: Fantomas formatter. Same .NET rules for SQL, serialization and secrets. Type providers that build SQL from strings follow the same injection rule.
* VB.NET: `Option Strict On` and `Option Explicit On` in every project (the IDE default is Off). Legacy WinForms or Web Forms: fix in place and migrate in stages; never a rewrite of a working system.
* Tuning: measure first with a profiler; read-only EF queries without change tracking; load related data in one query, not one per row.
* Traps: `async void` outside event handlers; `.Result` / `.Wait()` deadlocks; a new `HttpClient` per request; swallowed exceptions in `catch {}`.

## Ruby and Rails
Lifecycle: ruby-lang.org/en/downloads/branches (normal, legacy maintenance with security fixes only, EOL) and endoflife.date/rails.
* Style: community Ruby Style Guide with RuboCop (or Standard). Rails conventions when Rails is present.
* SQL: ActiveRecord hash conditions or placeholders (`where("x = ?", v)`, `where("x = :v", v: v)`). Interpolation into `where`, `order`, `pluck`, `find_by_sql` is injection. Outside models, `sanitize_sql`.
* Mass assignment: strong parameters, `params.expect(user: [...])` (Rails 8.0+), `params.require(...).permit(...)` before. `expect(user: {})` permits everything, so list the keys. Never `permit!`.
* Output: ERB escapes by default; `html_safe` and `raw` switch it off. Use `sanitize` with an allowlist when HTML is needed.
* Code and data: never `eval`, `instance_eval`, `send` or `public_send` with a user-chosen name, `Marshal.load` on untrusted data. YAML from outside: `YAML.safe_load`. `Kernel#open` and `IO` methods with a leading `"|"` run commands up to 3.4 (deprecated in 3.3, removed in 4.0); use `File.open` on every version. Backticks and `system("string")` with external text are injection; pass separate arguments.
* Secrets: Rails encrypted credentials (`config/credentials.yml.enc`); the key file and `secret_key_base` never in Git. `bin/rails secret` to generate.
* Errors: `rescue => e` only where it can be handled; never `rescue Exception`. Detailed error pages only in development.
* Supply chain: `Gemfile.lock` committed, `bundle-audit check --update` (bundler-audit), Brakeman for Rails code, both in CI.
* Tuning: fix N+1 queries first (`includes`), add database indexes for frequent filters, cache only measured hot spots.
* Traps: callbacks hiding side effects, `update_attribute` skipping validations, open redirects with `redirect_to params[:url]`.

## Kotlin
Lifecycle: endoflife.date/kotlin (only the newest language release line is maintained). JVM target follows `java.md`.
* Style: Kotlin coding conventions (kotlinlang.org), Android Kotlin style guide on Android. ktlint for formatting, detekt for static analysis.
* Null safety: no `!!` on data that came from outside. Validate at the boundary with explicit types.
* Coroutines: structured concurrency, no `GlobalScope` (a delicate API: nothing can cancel or await it); never swallow `CancellationException` in a broad `catch`.
* SQL: Room `@Query` with `:param` bindings on Android; JDBC or Exposed with parameters on the server. String templates (`"... $x"`) inside SQL are injection.
* Server (Ktor, Spring): same rules as `java.md` for deserialization, CSRF and secrets.
* Errors: catch specific exceptions; a failed permission or token check returns a denial, never a default that passes.
* Supply chain: Gradle version catalog, lockfiles or dependency verification (`./gradlew --write-verification-metadata sha256` writes `gradle/verification-metadata.xml`). Never a `+` or `latest.release` version.

## Swift
Lifecycle: swift.org (releases and install page). Apple platforms: Xcode version decides the toolchain; endoflife.date/ios for OS support.
* Style: Swift API Design Guidelines. `swift format` (bundled with the Swift 6 toolchain) and SwiftLint.
* Concurrency: Swift 6 language mode turns data-race checks into errors. Migrate in stages (`-strict-concurrency=complete` as warnings in Swift 5 mode first), module by module; never silence checks just to compile.
* Secrets and tokens: Keychain with the strictest accessibility that works (`kSecAttrAccessibleWhenUnlockedThisDeviceOnly` when background access is not needed). Never `UserDefaults`, plist or source code.
* Crypto: platform crypto frameworks; never hand-rolled crypto.
* Commands (macOS, server): `Process` with an arguments array, never `/bin/sh -c` with external text.
* Errors: `throws` and `do/catch`; no `try!` or force unwrap `!` on external data.
* Supply chain: `Package.resolved` committed for apps; pin versions in `Package.swift`, never a branch for release builds.
* Traps: retain cycles in closures (`[weak self]`), UI work off the main actor, `NSAllowsArbitraryLoads` left on (see Mobile).

## Dart and Flutter app code
Lifecycle: docs.flutter.dev/release/archive and dart.dev; no long-term support line is published, so stay on a recent stable. Flutter ships with a pinned Dart SDK.
* Style: Effective Dart, `dart format`, `dart analyze` with `package:lints` (`recommended`) or `flutter_lints`, configured in `analysis_options.yaml`.
* SQL (local databases): `?` arguments, never interpolation (`'$x'`) into SQL.
* Secrets: nothing secret in Dart code, `--dart-define` values or assets; all of it ships in the app. Tokens in platform secure storage (`flutter_secure_storage`: Keychain on iOS, encrypted storage on Android).
* HTTP: never accept every certificate in shipped code.
* Errors: `try/on SpecificException catch`; a failed auth call leaves the user logged out, never logged in by default. Keep heavy work off the UI isolate.
* Supply chain: `pubspec.lock` committed for apps. `dart pub get` shows security advisories; `ignored_advisories` in `pubspec.yaml` only with a written reason. `dart pub outdated` to plan upgrades.
* Release: `flutter build <target> --obfuscate --split-debug-info=<dir>` renames symbols only; it does not protect secrets or resources.

## Scala
Lifecycle: scala-lang.org/development. Scala 3 LTS line for libraries, Scala Next for applications; 2.13 maintained, 2.12 minimal maintenance (tied to sbt 1.x).
* Style: Scala style guide, scalafmt.
* SQL: doobie `sql"..."` / `fr"..."` bind interpolated values as parameters; `Fragment.const` does no escaping, so never with user input. Slick: lifted queries or `sql"..."` interpolation, never raw splicing of input.
* Deserialization: Java serialization of untrusted data is unsafe (see `java.md`). Use a JSON library with explicit codecs.
* Errors: `Either`, `Try` or effect-type errors; never a catch-all `case _: Throwable` that hides fatal errors.
* Supply chain: pin versions in `build.sbt`, scan with the build's dependency audit; Scala libraries share the Maven ecosystem advisories.

## Elixir, Erlang, Phoenix
Lifecycle: Elixir fixes bugs only on the latest minor and gives security patches to the last 5 minors (elixir.hexdocs.pm "Compatibility and deprecations", which also lists supported OTP versions). OTP releases at erlang.org/downloads; endoflife.date `elixir`, `erlang`.
* Style: `mix format`, Credo.
* Atoms are never garbage collected: never `String.to_atom`, `List.to_atom`, `Module.concat`, `list_to_atom`, `binary_to_atom` or `:"x_#{input}"` on external data. Prefer a lookup table; `String.to_existing_atom` as fallback.
* Deserialization: `:erlang.binary_to_term(bin, [:safe])` on untrusted input, and `Plug.Crypto.non_executable_binary_to_term(bin, [:safe])` to refuse functions. Validate the result anyway. Never `file:consult` on untrusted files.
* SQL: Ecto queries with `^value`. In `fragment("... ?", ^value)` every `?` is a parameter; never build the fragment string from input.
* Commands: `System.cmd(cmd, args)` (argument list); never `:os.cmd/1` with external text, never wrap in `sh -c`. Pass `env:` to keep secrets out of children.
* Output: HEEx and Phoenix.HTML escape by default; `raw/1` disables it.
* TLS (Erlang `ssl`, `:httpc`): clients set `verify: :verify_peer` with `cacerts: :public_key.cacerts_get()` (OTP 25+); do not rely on the default.
* Distribution: never expose EPMD or distribution ports to the internet; the cookie is a full-access credential.
* Errors: let it crash inside supervisors, but validate at the boundary; never `rescue` everything in a controller.
* Supply chain: `mix.lock` committed, `mix hex.audit` (retired and advised packages), `mix deps.audit` (mix_audit), Sobelow for Phoenix code.

## Clojure
Lifecycle: clojure.org/releases/downloads (minimum and recommended Java listed there); JDK per `java.md`.
* Style: Clojure community style guide, clj-kondo linter.
* Code and data: `read-string` can execute code (controlled by `*read-eval*`); for data use `clojure.edn/read-string`. Never `eval` on input.
* SQL: next.jdbc vectors `["select ... where id = ?" id]`; never `str` into SQL.
* Errors: catch specific exceptions; an exception in an auth check denies.
* Supply chain: exact versions in `deps.edn` or `project.clj`; git deps pinned by `:git/sha` (branches are not supported). JVM dependency advisories apply.

## Haskell
Lifecycle: haskell.org/ghc and the GHC Status wiki (gitlab.haskell.org/ghc/ghc/wikis/GHC%20Status); endoflife.date `ghc`.
* Style: HLint; Ormolu or Fourmolu formatter.
* SQL: postgresql-simple `query conn "... ?" (Only x)`; the `Query` type exists to stop string concatenation, so never build it with `fromString` from input. Other libraries: `?` parameters only.
* Errors: total functions on external data (no `head`, `fromJust`, `read`); use `readMaybe`, `Either`. No `unsafePerformIO` around security state.
* Supply chain: `cabal freeze` (`cabal.project.freeze`) or a Stack resolver snapshot committed.

## OCaml
Lifecycle: ocaml.org/releases (5.x current; 4.14 still receives fixes).
* Style: ocamlformat via `dune fmt`.
* Deserialization: `Marshal` is not type-safe; never on untrusted data. Use a typed format (JSON with explicit decoders).
* Commands: `Unix.create_process` with an argument array; never `Sys.command` or `Unix.system` (both run a shell) with external text.
* Errors: `result` types for expected failures; never `with _ ->` that turns an auth failure into success.
* SQL: the driver's parameterized queries; never `Printf.sprintf` into SQL.
* Supply chain: `opam lock` (`.opam.locked`) committed for applications.

## Groovy
Lifecycle: groovy.apache.org/download.html (stable line, previous lines); endoflife.date `apache-groovy`.
* Style: Groovy style guide.
* SQL: `groovy.sql.Sql` turns a GString (`"... where id = ${id}"`) into a prepared statement; string concatenation (`'...' + input`) is injection. Quoting the placeholder (`'${id}'`) disables binding and is rejected by default; do not turn that check off.
* Code: never `Eval.me` (runs a Groovy expression) or `GroovyShell` evaluation on input.
* Errors: catch specific exceptions; a failed permission check denies.
* Jenkins pipelines: never Groovy interpolation (`sh "... ${params.X}"`) with parameters or credentials. Use single quotes so the shell reads the environment: `sh 'echo "$X"'`, credentials through `withCredentials`.

## Crystal
Lifecycle: crystal-lang.org (1.x line, compatibility kept within the major version).
* Style: `crystal tool format`, Ameba.
* SQL: crystal-db with `?` or `$1` arguments, never interpolation.
* Commands: `Process.run(cmd, args: [...])` with `shell: false` (the default).
* Errors: `rescue ex : SpecificError`; a failed auth check denies.
* Supply chain: `shard.lock` committed for applications (libraries do not commit it).

## Mobile (Android, iOS, Flutter, React Native)
Standard: OWASP MASVS (groups STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE, PRIVACY) and MASTG for tests, at mas.owasp.org.
* Everything in the app package is public: no API secrets, private keys or admin endpoints in code, resources, `--dart-define`, `EXPO_PUBLIC_*` (inlined in plain text) or `BuildConfig`. Calls that need a secret go through your server.
* All authorization on the server. The app is a client, not a source of truth; a "premium" flag on the device is a suggestion.
* Storage: tokens in Keychain (iOS) or Android Keystore-backed storage. Never in `SharedPreferences`, `UserDefaults`, AsyncStorage (unencrypted) or logs. React Native: `react-native-keychain` or `expo-secure-store`. Jetpack `security-crypto` (`EncryptedSharedPreferences`) is deprecated; for new code use the Android Keystore directly, keep existing data readable while migrating.
* Network: HTTPS only. Android: cleartext is blocked by default for apps targeting API 28+; never `cleartextTrafficPermitted="true"` in `base-config`. iOS: keep ATS on; `NSAllowsArbitraryLoads` needs App Review justification, prefer a narrow `NSExceptionDomains` entry.
* Pinning: only for high-value APIs, always with a backup pin and a rotation plan (Android `pin-set` in network security config), or a certificate change locks users out.
* Android components: set `android:exported` explicitly; `false` unless another app must start it. Validate every intent and deep-link parameter against an allowlist; use App Links with `android:autoVerify="true"`. Never send tokens through custom URL schemes.
* WebView: JavaScript off unless needed; `addJavascriptInterface` only for your own HTTPS content, removed before loading anything else.
* Backups: exclude tokens and sensitive files with `android:dataExtractionRules` (12+) and `android:fullBackupContent` (11 and lower).
* Auth: OAuth 2 with PKCE through the system browser (`react-native-app-auth` or the platform SDK), never an embedded login WebView for third-party credentials.
* Integrity: Play Integrity verdicts checked on your server, never in the app.
* iOS privacy manifest (`PrivacyInfo.xcprivacy`) declares required-reason APIs and data collection; third-party SDKs on Apple's list must ship their own.
* Permissions requested at the moment of use, with a pt-BR explanation.
* Obfuscation (Android shrinking, Flutter `--obfuscate`) slows reverse engineering; it never protects a secret.
* Release checklist: debug flags off, logging of personal data off, `android:debuggable` false, test build pointing at production removed.
