# Other systems languages: Zig, Ada/SPARK, Assembly, Objective-C, D, Nim

Version policy: follow `versoes-e-fontes.md`. Read the pinned compiler from the project (`build.zig.zon` `minimum_zig_version`, `alire.toml`, `dub.json`/`dub.sdl`, `.nimble`, Xcode project, CI). Releases: ziglang.org/download, alire.ada.dev, dlang.org/changelog, nim-lang.org/install.html, Apple developer release notes. Pair with `c-cpp.md` for the C side of any interop and with `native-app-security.md` for any parser. V and Odin were left out: neither had a stable release at the check date (V 0.x, Odin monthly `dev-YYYY-MM` builds); treat a project in either as pre-release tooling and say so.

## Shared rules for C interop
* The C ABI has no lengths, no ownership and no error type. Every crossing passes pointer plus length, names who frees, and maps the C status to the language's error type at the boundary.
* Bounds are checked before the call, never after (see `rust.md`, FFI section; the rule is the same here).
* Memory allocated on one side is freed on the same side, with its own free function.
* Never let a language exception, panic or unwind cross into C; catch at the boundary and return a status.
* Fuzz and run ASan on the combined binary; each language's own checker cannot see the other side.

## Zig
* Pre-1.0: the language and the standard library change between 0.x releases. Pin the exact compiler version in CI and record it in `build.zig.zon` `minimum_zig_version` (advisory only, the compiler does not enforce it); upgrade as a planned task with the release notes open.
* Style: `zig fmt` on commit. Build with `zig build`.
* Optimize modes: Debug and ReleaseSafe keep runtime safety checks (overflow, bounds, null unwrap, invalid casts); ReleaseFast and ReleaseSmall remove them and turn those cases into undefined behavior. Ship ReleaseSafe for anything that reads untrusted input.
* `@setRuntimeSafety(false)` only in a measured hot loop, with a comment stating why every index is in range.
* Arithmetic: plain `+` traps on overflow in safe modes; use `+%` (wrapping) or `+|` (saturating) only when that is the intended semantics, and `@addWithOverflow` / `@mulWithOverflow` (result plus overflow bit) on untrusted sizes.
* Memory: no hidden allocations; every allocating function takes an allocator. Pair each allocation with `defer` or `errdefer` free. `std.heap.DebugAllocator` (named `GeneralPurposeAllocator` before 0.14) in tests to catch leaks and double frees.
* Errors: error unions and `try`; never `catch unreachable` on a path reachable from input.
* C interop: `@cImport` reads C headers directly; `export fn` exposes a C ABI function. Zig is also a C compiler (`zig cc`), useful for cross-compiling C, but the C code keeps every C risk.
* Commands: spawn the program with an argument list, never a shell string built from input.
* Supply chain: dependencies in `build.zig.zon` with `url` plus `hash`; the hash is the identity. Add with `zig fetch --save <url>`. Point at a release tarball or commit archive, never a branch URL. When changing a URL, delete the old hash.

## Ada and SPARK
* Standard: Ada 2022 is ISO/IEC 8652:2023. GNAT (GCC) is the free compiler; Alire (`alr`) is the package manager and toolchain installer.
* Style: GNAT style checks (`-gnaty`) in the project file, warnings reviewed in CI.
* Safety: GNAT runtime checks (range, bounds, overflow) are on by default. Never ship with `-gnatp` or `pragma Suppress (All_Checks)` on code that reads input; an unchecked Ada build is as unsafe as C.
* Use strong typing as the validation layer: range-constrained subtypes (`subtype Port is Integer range 1 .. 65535`) at every boundary.
* Exceptions: handle `Constraint_Error` at the input boundary, log, deny. A handler `when others => null;` is a fail-open bug.
* SPARK: a provable subset of Ada. Adoption levels: Stone (valid SPARK), Bronze (initialization and data flow), Silver (proved absence of run-time errors), Gold (key integrity properties), Platinum (full functional proof). Silver is the realistic target for a parser or protocol handler; GNATprove does the proof.
* C interop: `pragma Import`/`Export` or `with Import, Convention => C`; types from `Interfaces.C`. Keep the binding package thin and the checks on the Ada side.
* Supply chain: `alr with <crate>` records dependencies in `alire.toml`; pin versions there, and `alr update` only as a deliberate change.
* Legacy Ada (83/95): upgrade the compiler first with the same language mode, then turn on the newer mode file by file. Never rewrite it into another language; it is already memory-safe when checks are on.

## Assembly (x86-64, ARM64)
* Justified only for: a measured hot loop where intrinsics fail, constant-time crypto primitives from a vetted library, boot or context-switch code, instructions the compiler cannot emit. Everything else is C, Rust or intrinsics.
* Prefer intrinsics or a vetted library (for crypto) over hand-written assembly. If asm is unavoidable, keep a C reference implementation and test both against each other.
* Calling conventions (break them and the bug appears far from the cause):
  * System V AMD64 (Linux, macOS, BSD): integer args in `rdi, rsi, rdx, rcx, r8, r9`; return in `rax`; callee-saved `rbx, rbp, r12-r15`; stack 16-byte aligned at the `call`; 128-byte red zone below `rsp` for leaf functions.
  * Microsoft x64 (Windows): integer args in `rcx, rdx, r8, r9`; caller reserves 32 bytes of shadow space; nonvolatile `rbx, rbp, rdi, rsi, rsp, r12-r15, xmm6-xmm15`; stack 16-byte aligned; non-leaf functions need unwind data (prolog/epilog rules), or exceptions and stack walks break.
  * AAPCS64 (ARM64): args in `x0-x7` and `v0-v7`; callee-saved `x19-x28` and the low 64 bits of `v8-v15`; `x29` frame pointer, `x30` link register; `x18` is reserved on some platforms, so never use it; `sp` 16-byte aligned.
* Security marks the compiler adds and hand-written asm lacks:
  * ELF: add `.section .note.GNU-stack,"",@progbits` to every `.S` file, or the linker (binutils 2.39+ warns) may give the whole program an executable stack.
  * x86 CET: `endbr64` at every indirect-branch target and a `.note.gnu.property` marking; check with `-Wl,-z,cet-report=error`.
  * ARM64: when the C code uses `-mbranch-protection=standard`, start each asm function with `bti c` (or `paciasp`, which is also a valid landing pad) and pair `paciasp` with `autiasp` before `ret`.
* Secrets: constant-time code means no branch and no memory index depends on a secret. Verify with a tool, not by reading.
* Inline asm in C: declare every clobbered register and `"memory"` when it touches memory; a missing clobber is a silent miscompile.

## Objective-C
* Style: Apple's coding guidelines, `clang-format`, Xcode static analyzer (`Analyze`) clean.
* Memory: ARC always (`-fobjc-arc`). Manual `retain`/`release` in new code is a defect. Core Foundation crossings use `__bridge`, `__bridge_transfer` or `__bridge_retained` so ownership is explicit. `__weak` for delegates and back-references to break cycles.
* Format strings: never `NSLog(userString)` or `[NSString stringWithFormat:userString]`; always `NSLog(@"%@", userString)`.
* Deserialization: `NSKeyedUnarchiver unarchivedObjectOfClass:fromData:error:` (macOS 10.13+, iOS 11+) with classes that adopt `NSSecureCoding` and decode with `decodeObjectOfClass:forKey:`. Never the old `unarchiveObjectWithData:` (deprecated since iOS 12 and macOS 10.14, ignores secure coding).
* SQL: SQLite with `sqlite3_prepare_v2` and `sqlite3_bind_*`, never `stringWithFormat` into SQL.
* Commands: `NSTask` with `executableURL` and an `arguments` array, never `/bin/sh -c` with input.
* Secrets: Keychain Services, never `NSUserDefaults` or a plist.
* Network: App Transport Security stays on. `NSAllowsArbitraryLoads = YES` disables it for every domain and needs App Store justification; use a narrow per-domain exception if a legacy server truly needs one.
* Legacy code: convert to ARC file by file (Xcode migration, `-fno-objc-arc` on files not yet converted). New features may go in Swift through a bridging header; do not rewrite working Objective-C wholesale.

## D
* Compilers: DMD (reference), LDC (LLVM), GDC (GCC). Package manager: `dub`; commit `dub.selections.json` so everyone builds the same dependency versions.
* Safety: mark code `@safe`; it forbids memory-corrupting operations. `@trusted` is a promise you make by hand: keep each one tiny, with a safe interface and a comment. `@system` code cannot be called from `@safe` without `@trusted`.
* Enable scope checking for `@safe` code (DIP1000; see `dmd -preview=h` for the exact preview name in your compiler version).
* `-release` drops asserts and contracts, makes a failed assert undefined behavior, and keeps bounds checks only in `@safe` code. Never `-boundscheck=off` on code that reads input; `-check` re-enables specific checks.
* Commands: `std.process.execute`/`spawnProcess` with an argument array; `executeShell`/`spawnShell` go through the shell, so input there needs `escapeShellCommand` or, better, the array form.
* C interop: `extern(C)` declarations; translate headers with ImportC (DMD compiles C files directly) or by hand, checking every length.
* Exceptions: catch at the input boundary, log, deny. Never let a D exception cross an `extern(C)` function.

## Nim
* Nim 2.x is the stable line. Default memory management is ORC (`--mm:orc`).
* Style: compiler hints and warnings reviewed in CI.
* Builds: `-d:release` turns on the optimizer; `-d:danger` turns off ALL runtime checks (bounds, overflow, nil). Never ship `-d:danger` for code that reads input.
* Commands: `osproc.startProcess` with an `args` list and without `poEvalCommand`. `execProcess` uses `poEvalCommand` (the shell) by default, so pass options explicitly; `poEvalCommand` only for trusted strings.
* SQL: `db_connector` (separate package since Nim 2, `import db_connector/db_sqlite`) with `?` parameters, never string `&` concatenation into SQL.
* C interop: `{.importc.}` and `{.exportc.}` pragmas; `cstring` has no length, so pass lengths explicitly and copy into `string` at the boundary.
* Supply chain: `nimble lock` writes `nimble.lock` with exact versions and checksums; commit it.
* Exceptions: catch specific types at the boundary; a bare `except: discard` is a fail-open bug.
