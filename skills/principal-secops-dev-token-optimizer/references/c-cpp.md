# C and C++ — current ISO standards, CERT C, C++ Core Guidelines

Version policy: follow `versoes-e-fontes.md`. Use the newest ISO standard that every compiler the project targets supports (check en.cppreference.com/w/cpp/compiler_support and the compiler's release notes), with the previous standard as the fallback. The `-std=` flag spelling differs between compiler versions, so confirm it for the installed one, and declare the standard in the build file. A standard older than C++17 is a flag to plan the upgrade. Anything here that parses a file or a network message also needs `native-app-security.md`.

## Language and standards
* Rules: C++ Core Guidelines for C++, CERT C for C. `.clang-format` committed. `clang-tidy` clean with `bugprone-*`, `cppcoreguidelines-*`, `cert-*`.
* C++: no owning raw pointers. `std::unique_ptr`, RAII for every resource, rule of zero. No `new` or `delete` in application code.
* C++: `std::span` and `std::string_view` so a length always travels with the pointer. `enum class`, `[[nodiscard]]` on anything returning a status, `constexpr` where it can compute at build time.
* C: every buffer parameter carries an explicit length parameter. Never `strcpy`, `strcat`, `sprintf`, `gets`, `alloca`, `atoi`. Use `snprintf` and check the return, `strtol` and check `errno`.
* Fixed-width types (`uint32_t`, `size_t`) at every boundary. `int` only for local loop counters.
* Never rely on struct layout or `#pragma pack` for a file or wire format. Serialize field by field.
* Warnings are errors in CI: `-Wall -Wextra -Wconversion -Wformat=2 -Wimplicit-fallthrough -Werror`, or `/W4 /permissive- /WX` on MSVC.

## Documentation
* Doxygen block on every public function, in the header. It states what the function does, who owns and frees each pointer, the valid range of each parameter, every failure mode, and what is returned in each case.
* A function that allocates says so in the first line and names the release function.
* Public headers carry an SPDX identifier line. See `compliance-licencas.md`.
* Any file format the project defines gets a written spec document, versioned with the code. An undocumented format is unmaintainable within a year.

## Security: hostile input
Anything read from a file, a socket, the clipboard or a command line is attacker-controlled. This is where native code dies.

* **Never trust a length or count field.** Validate it against the bytes actually remaining before allocating: `count > (file_size - header_size) / entry_size`. An arbitrary `MAX_ENTRIES` constant is not that check, because it still lets a 30-byte file trigger a large allocation.
* **Every arithmetic operation on an untrusted number is checked.** C23 `ckd_mul` and `ckd_add` from `<stdckdint.h>`, or `__builtin_mul_overflow` on GCC and Clang. Silent wraparound on `count * sizeof(entry)` is the classic heap overflow.
* **Signed overflow is undefined behavior**, so the compiler is allowed to delete your check. Do the arithmetic in `size_t` or use the checked builtins. Never write `if (a + b < a)` on signed values.
* **Explicit endianness at every serialization point.** Read byte by byte and shift. Never `fread` into a struct, never `memcpy` a multi-byte integer out of a buffer. Host-endian parsing is both a portability bug and an ambiguity in your own format spec.
* Validate offset and length against the buffer size, with overflow-checked addition, before every index and every pointer arithmetic on parsed data.
* One owner per allocation. Free once, then null the pointer.
* `memcpy` with an input-derived length needs the destination size in the same expression.
* Wipe sensitive buffers with `explicit_bzero` or `SecureZeroMemory`. A plain `memset` gets optimized away.

## Exceptional conditions
* C: every fallible function returns a status and every call site checks it. A `(void)` cast on an ignored return needs a comment saying why.
* C++: exceptions or `std::expected`, decided once for the project and applied consistently. Destructors never throw. `noexcept` on move operations.
* No leak on any error path. C++ gets this from RAII; C needs a single cleanup label per function (`goto cleanup`) instead of repeating frees at every return.
* When sizes come from input, allocation failure is a real path. Check every `malloc`.

## Build: release, hardening, portability
Two mistakes here ship broken binaries.

* **Never `-march=native` in a distributed build.** It targets the build machine's CPU, so the binary dies with an illegal instruction on any older processor. Compile a portable baseline such as `-march=x86-64-v2` and select optimized paths at run time with `__builtin_cpu_supports` or a dispatch table.
* **Optimization flags are not hardening flags.** `-O3 -flto` says nothing about security.

GCC and Clang release:
```
-O2 -flto -fno-omit-frame-pointer
-D_FORTIFY_SOURCE=3 -D_GLIBCXX_ASSERTIONS
-fstack-protector-strong -fstack-clash-protection
-fcf-protection=full             # x86-64, CET
-mbranch-protection=standard     # aarch64, PAC and BTI
-ftrivial-auto-var-init=zero
-fPIE -pie
-Wl,-z,relro,-z,now -Wl,-z,noexecstack
```
MSVC release: `/O2 /GL /guard:cf /guard:ehcont /sdl /utf-8`, linked with `/LTCG /DYNAMICBASE /HIGHENTROPYVA /NXCOMPAT /CETCOMPAT`.

`_FORTIFY_SOURCE` needs `-O1` or higher. It does nothing in a debug build.

## Testing native code
A parser without a fuzzer is untested, however many unit tests it has.

**The sanitizer build goes inside the build file you deliver, not into a sentence next to it.** A `CMakeLists.txt` for code that parses untrusted input is incomplete without it. Prose around the code gets trimmed on the way to the user; the build file does not. Include this in the file itself:

```cmake
option(SANITIZE "Build with ASan and UBSan" OFF)
if(SANITIZE AND NOT MSVC)
  target_compile_options(<target> PRIVATE -fsanitize=address,undefined -fno-sanitize-recover=all -O1 -g)
  target_link_options(<target> PRIVATE -fsanitize=address,undefined)
endif()
```

* A separate build type with `-fsanitize=address,undefined -fno-sanitize-recover=all`. ASan and MSan cannot be combined. Run TSan separately for threaded code.
* Fuzz every entry point that takes bytes: libFuzzer (`-fsanitize=fuzzer`) or AFL++. Commit the corpus. Every crash becomes a regression test.
* Differential fuzzing when reimplementing an existing format: your code and the reference implementation get the same input, and any difference is a bug. This is the only honest way to replace a mature decoder.
* CI runs the sanitizer build on every commit and the fuzzer on a schedule.

## Performance
* Profile before optimizing: `perf record` on Linux, Windows Performance Analyzer or VTune on Windows. The profile is a prerequisite, not a formality.
* Benchmark with a harness that reports variance (Google Benchmark), on a fixed corpus, pinned to a core. A single timing number is noise.
* For data-heavy code, memory layout beats instruction count. Contiguous arrays, struct-of-arrays in hot loops, cache-line awareness.
* When the profile shows cache misses dominating, batch and prefetch. That is the usual bottleneck in search and lookup structures.
* SIMD only after the profile names the loop, always behind run-time dispatch with a scalar fallback. Intrinsics, not inline assembly, unless the compiler demonstrably fails.
* PGO (`-fprofile-generate` then `-fprofile-use`) is often a bigger win than hand tuning, at no risk to correctness.
* LTO in release, then measure it. It occasionally hurts.
