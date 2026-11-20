# C, C++ and CMake: ISO standards, CERT C, C++ Core Guidelines

Version policy: follow `versoes-e-fontes.md`. Read the standard from the build file (`CMAKE_CXX_STANDARD`, `CMAKE_C_STANDARD`, `-std=`, MSVC `/std:`) and the compiler versions from CI. Check feature support at en.cppreference.com/w/cpp/compiler_support and the compiler's release notes; GCC releases at gcc.gnu.org/releases.html. Use the newest standard every target compiler fully supports, never a draft mode in a shipped build. Older than C++17 is a finding to plan an upgrade for. Anything that parses a file or a network message also needs `native-app-security.md`.

## Contents
- Standards status
- Language and style
- Documentation
- Security: hostile input
- Exceptional conditions
- Build: hardening, CMake, portability
- Testing native code
- Supply chain
- Tuning
- Traps and fixes
- Legacy code and memory-safety roadmap

## Standards status (checked 2026-11-20)
* C: C23 is ISO/IEC 9899:2024. GCC spells it `-std=c23` (old alias `c2x` deprecated); C2y is experimental (`-std=c2y`), never for shipped code.
* C++: C++23 is ISO/IEC 14882:2024, the current published edition. C++26 technical work finished in March 2026; ISO publication was pending at the check date. Use C++26 features only as "(C++26+)" and only when every target compiler lists them.
* C++26 safety features, when the compilers support them: reading an uninitialized local is no longer undefined behavior; standard library hardening (bounds checks on `vector`, `span`, `string` and similar); contracts (`pre`, `post`, `contract_assert`). Compiler support was partial at the check date (GCC ahead, Clang and MSVC behind).
* C++ safety profiles are NOT in C++26. The committee targets C++29. Never promise profiles as a protection today.
* Compiler defaults move between versions (recent GCC defaults to `gnu23` for C and `gnu++20` for C++). Always set the standard explicitly.
* MSVC: `/std:c++20` is the newest stable mode; `/std:c++23preview` and `/std:c++latest` are preview and not ABI-stable. MSVC C modes are `/std:c11`, `/std:c17`, `/std:clatest`; no C23 mode was documented. MSVC keeps `__cplusplus` at `199711L` unless `/Zc:__cplusplus` is passed.

## Language and style
* Rules: C++ Core Guidelines for C++, SEI CERT C for C. `.clang-format` committed. `clang-tidy` clean with `bugprone-*`, `cppcoreguidelines-*`, `cert-*`.
* C++: no owning raw pointers. `std::unique_ptr`, RAII for every resource, rule of zero. No `new` or `delete` in application code.
* C++: `std::span` and `std::string_view` so a length travels with the pointer. `enum class`, `[[nodiscard]]` on anything returning a status, `constexpr` where it can run at build time.
* C: every buffer parameter carries an explicit length. Never `strcpy`, `strcat`, `sprintf`, `gets`, `alloca`, `atoi`. Use `snprintf` and check the return, `strtol` and check `errno` and the end pointer.
* Fixed-width types (`uint32_t`, `size_t`) at every boundary. `int` only for local counters.
* Never rely on struct layout or `#pragma pack` for a file or wire format. Serialize field by field.
* Warnings are errors in CI only: `-Wall -Wextra -Wformat=2 -Wconversion -Wimplicit-fallthrough -Werror=format-security`, or `/W4 /permissive- /WX` on MSVC. C code also: `-Werror=implicit -Werror=incompatible-pointer-types -Werror=int-conversion`.

## Documentation
* Doxygen block on every public function, in the header: what it does, who owns and frees each pointer, valid range of each parameter, every failure mode, what is returned in each case.
* A function that allocates says so in the first line and names the release function.
* Public headers carry an SPDX identifier line. See `compliance-licencas.md`.
* Any file format the project defines gets a written spec, versioned with the code.

## Security: hostile input
Anything read from a file, a socket, the clipboard, the environment or a command line is attacker-controlled.

* **Never trust a length or count field.** Validate it against the bytes actually remaining before allocating: `count > (file_size - header_size) / entry_size`. A fixed `MAX_ENTRIES` is not that check; a 30-byte file can still trigger a huge allocation.
* **Every arithmetic operation on an untrusted number is checked.** C23 `ckd_add`, `ckd_mul` from `<stdckdint.h>` (C23+), or `__builtin_add_overflow` / `__builtin_mul_overflow` on GCC and Clang. Silent wraparound on `count * sizeof(entry)` is the classic heap overflow.
* **Signed overflow is undefined behavior**, so the compiler may delete your check. Never `if (a + b < a)` on signed values; use the checked builtins.
* **Explicit endianness at every serialization point.** Read byte by byte and shift. Never `fread` into a struct.
* Validate offset and length against the buffer size, with overflow-checked addition, before every index and pointer arithmetic on parsed data.
* One owner per allocation. Free once, then null the pointer.
* `memcpy` with an input-derived length needs the destination size in the same expression.
* Wipe secrets with `memset_explicit` (C23+), `explicit_bzero` (glibc, BSD) or `SecureZeroMemory` (Windows). A plain `memset` is optimized away.
* Commands: `execve`/`posix_spawn` with an argument array, never `system()` or `popen()` with input in the string. Windows: `CreateProcessW` with a quoted application path.
* Format strings: never `printf(user_text)`; always `printf("%s", user_text)`. `-Werror=format-security` catches it.
* Paths built from data: canonicalize and check containment; open with `openat` relative to a trusted directory fd. `O_NOFOLLOW` only refuses a symlink in the last path component, not in earlier ones. Details in `native-app-security.md`.
* Secrets never in source or in the binary's strings; read from the environment or the OS keychain.
* Crypto: a maintained library (libsodium, OpenSSL, the OS API). Never hand-rolled. Passwords: libsodium `crypto_pwhash_str` (Argon2id by default since libsodium 1.0.15). TLS: never disable certificate verification (`SSL_VERIFY_NONE`, `CURLOPT_SSL_VERIFYPEER 0`).

## Exceptional conditions
* C: every fallible function returns a status and every call site checks it. A `(void)` cast on an ignored return needs a comment saying why.
* C++: exceptions or `std::expected` (C++23+), decided once for the project. Destructors never throw. `noexcept` on move operations.
* No leak on any error path. C++ gets it from RAII; C uses one cleanup label per function (`goto cleanup`).
* Allocation failure is a real path when sizes come from input. Check every `malloc`.
* An auth or validation function initializes its result to "denied" and only sets "allowed" at the end of the success path.

## Build: hardening, CMake, portability
* **Never `-march=native` in a distributed build.** The binary dies with an illegal instruction on older CPUs. Compile a portable baseline (`-march=x86-64-v2`) and dispatch at run time with `__builtin_cpu_supports`.
* **Optimization flags are not hardening flags.** `-O3 -flto` says nothing about security.

GCC and Clang release baseline (OpenSSF Compiler Options Hardening Guide):
```
-O2 -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3
-D_GLIBCXX_ASSERTIONS                                 # libstdc++
-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST  # libc++
-fstrict-flex-arrays=3
-fstack-clash-protection -fstack-protector-strong
-fPIE -pie                                            # executables (-fPIC -shared for libraries)
-Wl,-z,nodlopen -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now
-Wl,--as-needed -Wl,--no-copy-dt-needed-entries
# x86-64:  -fcf-protection=full
# AArch64: -mbranch-protection=standard
# production: -fno-delete-null-pointer-checks -fno-strict-overflow -fno-strict-aliasing -ftrivial-auto-var-init=zero
```
* GCC 14+ on GNU/Linux: `-fhardened` enables the core set (FORTIFY 3, GLIBCXX assertions, auto-var-init zero, PIE, full RELRO, stack protector strong, stack clash, CET on x86). It never overrides an option already given.
* `_FORTIFY_SOURCE` needs `-O1` or higher and is incompatible with ASan; leave it out of sanitizer builds.
* MSVC release: `/O2 /sdl /guard:cf /guard:ehcont /utf-8`, linked with `/DYNAMICBASE /HIGHENTROPYVA /NXCOMPAT /CETCOMPAT`. `/sdl` turns key security warnings into errors and enables strict `/GS`. `/guard:ehcont` (VS 2019 16.7+, 64-bit only) must reach compiler and linker.

CMake:
* `cmake_minimum_required(VERSION <min>...<max>)`. CMake 4.0+ errors on a minimum below 3.5; 3.31+ warns below 3.10.
* `set(CMAKE_CXX_STANDARD 20)`, `CMAKE_CXX_STANDARD_REQUIRED ON`, `CMAKE_CXX_EXTENSIONS OFF` (extensions are ON by default). C++23 needs CMake 3.20+, C++26 needs 3.25+, C23 needs 3.21+.
* PIE: `POSITION_INDEPENDENT_CODE ON` plus `include(CheckPIESupported)` and `check_pie_supported()`, or the executable is not linked as PIE.
* Warnings as errors per target with `COMPILE_WARNING_AS_ERROR` (3.24+), set in CI, never forced on people building your source release.
* Flags go on targets (`target_compile_options`), never in global `CMAKE_CXX_FLAGS` strings edited by hand.

## Testing native code
A parser without a fuzzer is untested, however many unit tests it has.

**The sanitizer build goes inside the delivered build file, not into a sentence next to it.** A `CMakeLists.txt` for code that parses untrusted input is incomplete without it:

```cmake
option(SANITIZE "Build with ASan and UBSan" OFF)
if(SANITIZE AND NOT MSVC)
  target_compile_options(<target> PRIVATE -fsanitize=address,undefined -fno-sanitize-recover=all -O1 -g)
  target_link_options(<target> PRIVATE -fsanitize=address,undefined)
elseif(SANITIZE AND MSVC)
  target_compile_options(<target> PRIVATE /fsanitize=address /Zi)
endif()
```

* ASan and MSan cannot be combined. Run TSan separately for threaded code.
* MSVC ASan (VS 2019 16.9+, x86 and x64): incompatible with `/RTC`, `/ZI` (edit and continue) and incremental linking. MSVC has no UBSan.
* Test builds: `_LIBCPP_HARDENING_MODE_DEBUG` or `_GLIBCXX_DEBUG` (the latter changes ABI, so rebuild every dependency).
* Fuzz every entry point that takes bytes: libFuzzer (`-fsanitize=fuzzer,address`; bug-fix maintenance only, still usable) or AFL++. Commit the corpus. Every crash becomes a regression test.
* Differential fuzzing when reimplementing an existing format: same input to your code and the reference, any difference is a bug.
* CI runs the sanitizer build on every commit and the fuzzer on a schedule.
* Full UBSan runtime never ships. If UB checks must stay in production, Clang `-fsanitize-minimal-runtime` or `-fsanitize-trap=all` only.

## Supply chain
* vcpkg manifest mode: `vcpkg.json` with `builtin-baseline` (a registry commit) so every machine resolves the same versions; exact pins through `overrides`.
* Conan 2: `conan lock create .`, commit `conan.lock`, pass `--lockfile=conan.lock` in CI.
* Vendored or `FetchContent` code: pin a commit hash or a release archive with `URL_HASH SHA256=`, never a branch name.
* Check each dependency against osv.dev on every change and record it in the SBOM (`compliance-licencas.md`).

## Tuning
* Profile before optimizing: `perf record` on Linux, Windows Performance Analyzer or VTune on Windows.
* Benchmark with a harness that reports variance (Google Benchmark), fixed corpus, pinned core.
* Memory layout beats instruction count: contiguous arrays, struct-of-arrays in hot loops.
* Cache misses dominating: batch and prefetch.
* SIMD only after the profile names the loop, behind run-time dispatch with a scalar fallback. Intrinsics, not inline assembly.
* PGO (`-fprofile-generate`, then `-fprofile-use`) often beats hand tuning. LTO in release, then measure.

## Traps and fixes
* `-march=native` in a release: crash on other CPUs. Fix: portable baseline plus run-time dispatch.
* `_FORTIFY_SOURCE` in a `-O0` build: silently does nothing. Fix: release flags with `-O2`.
* Overflow check written as `a + b < a` on `int`: deleted by the optimizer. Fix: `ckd_add` or `__builtin_add_overflow`.
* `fread(&header, sizeof header, 1, f)`: padding and endianness bugs. Fix: read bytes and decode each field.
* `CMAKE_CXX_STANDARD` set without `CMAKE_CXX_EXTENSIONS OFF`: builds with `gnu++` and hides portability bugs.
* `POSITION_INDEPENDENT_CODE ON` alone: executable may not be PIE. Fix: `check_pie_supported()`.
* `-Werror` in a source release: breaks the build on the next compiler. Fix: CI only.
* `#if __cplusplus >= 201703L` on MSVC: false without `/Zc:__cplusplus`. Fix: add the flag or test `_MSVC_LANG`.
* `strncpy` used as a safe copy: does not terminate on truncation. Fix: `snprintf` and check the result.
* `realloc` result assigned straight back to the pointer: leaks on failure. Fix: assign to a temporary, check, then swap.

## Legacy code and memory-safety roadmap
* CISA and FBI "Product Security Bad Practices" (v2.0, January 2025) call for a published memory-safety roadmap for existing products in memory-unsafe languages (by end of 2025, exempt if support ends before 2030-01-01) and memory-safe languages for new product lines. CISA and NSA "Memory Safe Languages" (June 2025) says adoption does not require rewriting existing code.
* Applied here: never rewrite a working C or C++ system. Stage it. First the hardening flags and the sanitizer build, then fuzzing of every parser, then new components (especially network-facing and parsing code) in a memory-safe language behind a narrow C ABI (`rust.md`), replacing one module at a time with differential tests.
* Upgrading the standard: one step at a time (for example 14 to 17), full test suite and sanitizer build green before the next step.
