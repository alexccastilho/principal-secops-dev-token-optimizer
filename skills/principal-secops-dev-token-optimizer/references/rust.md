# Rust: stable toolchain, editions, unsafe and FFI discipline

Version policy: follow `versoes-e-fontes.md`. Read `edition` and `rust-version` in `Cargo.toml` and the pin in `rust-toolchain.toml`; check releases at releases.rs and editions at doc.rust-lang.org/edition-guide. A new stable ships every six weeks, so update the pin deliberately and often. Edition 2024 needs Rust 1.85+; move to it only when the MSRV allows (`cargo fix --edition`, then review every change it made).

## Language and style
* `rustfmt` on commit. `cargo clippy -- -D warnings` in CI, `clippy::pedantic` where the crate can afford it.
* `#![forbid(unsafe_code)]` on every crate that does not genuinely need `unsafe`. Confine `unsafe` to one crate with a safe API on top.
* Errors: `thiserror` for library error types, `anyhow` only in binaries, `?` for propagation.
* `unwrap()` and `expect()` only where a panic is correct, with a message naming the invariant. Never on a path reachable from untrusted input. Clippy `unwrap_used` and `indexing_slicing` find them.
* `#![warn(missing_docs)]` on public crates. `# Errors` section on anything returning `Result`, `# Safety` on every `unsafe fn`. Doc examples run under `cargo test`.

## Edition 2024 changes that matter for safety
* `extern` blocks must be `unsafe extern "C" { ... }` (allowed in all editions from 1.82). Items can be marked `safe fn` only when every input is valid; default is unsafe.
* `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`, `#[unsafe(link_section = "...")]`: symbol names are global, the compiler cannot check uniqueness.
* `unsafe_op_in_unsafe_fn` warns by default: the body of an `unsafe fn` needs explicit `unsafe {}` blocks.
* `std::env::set_var` and `remove_var` are `unsafe`: unsound while any other thread runs. Set environment before spawning threads, or pass config explicitly.
* References to `static mut` are denied (`static_mut_refs`). Use atomics, `Mutex`, `OnceLock`, or `&raw mut` where truly needed.

## Security
* SQL: placeholders and `.bind()` (`sqlx::query("... WHERE id = $1").bind(id)`), or an ORM such as Diesel. Never `format!` into SQL; the sqlx docs show it as an injection.
* Commands: `std::process::Command::new(prog).arg(x)`, never `Command::new("sh").arg("-c").arg(format!(...))`. On Windows, running `.bat`/`.cmd` with untrusted arguments was exploitable before 1.77.2 (CVE-2024-24576) and got more fixes in 1.81 (CVE-2024-43402); avoid batch files, keep the toolchain current, never `raw_arg` with input.
* Paths: `Path::join` with an absolute argument replaces the base (`Path::new("/srv").join("/etc/passwd")` is `/etc/passwd`). Reject absolute paths and `..` components, then canonicalize and check `starts_with(base)`. Details in `native-app-security.md`.
* Secrets: from the environment or a secret store, never in source. Wrap in `secrecy` or zeroize on drop (`zeroize` crate) so they do not linger or print in `Debug`.
* Passwords: RustCrypto `argon2` (Argon2id by default). Random tokens from the OS RNG (`getrandom` or `rand::rngs::OsRng`), never a seeded PRNG. Compare tokens in constant time (`subtle`).
* TLS: `rustls` or the platform verifier. Never `danger_accept_invalid_certs(true)` or `danger_accept_invalid_hostnames(true)` in reqwest (renamed `tls_danger_*`), and never a custom verifier that returns success.
* Deserialization: `serde` into concrete types with `#[serde(deny_unknown_fields)]` at trust boundaries. Cap input size before parsing, and cap lengths in binary formats; an attacker-chosen length must not drive `Vec::with_capacity`.
* Integer overflow: release builds wrap silently (`overflow-checks = false` by default). On untrusted numbers use `checked_*`, `saturating_*` or `try_from`, or set `overflow-checks = true` in `[profile.release]`.
* Web frameworks (axum, actix-web): extractors with typed, validated input; auth as middleware that denies by default.

## Exceptional conditions
* Every `Result` is handled or propagated. `let _ = fallible();` needs a comment saying why the error is ignorable.
* Errors to the user are generic; detail goes to `tracing` or `log`. Never log secrets.
* An authorization check returns `Result<(), Denied>` and any error path is a deny.
* Panics are not an error strategy in a long-running process or across FFI. Since 1.81 a panic escaping an `extern "C"` function aborts the process; use `extern "C-unwind"` only when the C side is built to unwind, else `catch_unwind` at the boundary and return a status code.

## unsafe discipline
* Every `unsafe` block gets a `// SAFETY:` comment naming the invariant. Enforce with `clippy::undocumented_unsafe_blocks` and `clippy::multiple_unsafe_ops_per_block` (restriction group, opt in).
* Every `unsafe fn` gets `/// # Safety` stating what the caller must guarantee.
* `unsafe` is not a performance tool. Measure first; bounds checks are usually hoisted out of loops.
* `cargo miri test` on anything with `unsafe`. It finds undefined behavior no test will.

## FFI to C: the contract goes before the call
The wrapper exists to make the C function's preconditions impossible to violate. **A check placed after the call is worthless.** If the C side wrote past the buffer, memory is already corrupt and returning an error does not undo it.

* Establish every bound before the call. Pass the real capacity, never a value the C side could grow.
* An in-out length parameter (capacity in, size out) is read back into a local. Never let a later bound depend on the variable the C side just wrote.
* Every value the C side writes is untrusted on return. Clamp it before it reaches a slice or an index.
* Generate declarations with `bindgen` so a C signature change fails the build.
* `unsafe extern "C"`. Map the C status to a typed Rust error at the boundary; a nonzero return never flows on as success.
* `#[repr(C)]` on every struct that crosses. Never send a Rust enum, `String` or `Vec` across. Strings via `CString`/`CStr`, checking for interior NUL.
* When the C function writes an arbitrary amount, give it a buffer you sized, have it report what it used, then `truncate`. If it allocates, free with its matching function, never with Rust's allocator.
* Run the FFI tests under ASan. Miri cannot see into C. Rust sanitizers are nightly-only (`-Zsanitizer=address`, Linux and macOS targets), so run them in a separate CI job.

## Supply chain
* `Cargo.lock` committed for binaries; build with `cargo build --locked`.
* `cargo audit` (RustSec database) and `cargo deny check` (advisories, bans, licenses, sources) in CI. The license check keeps a copyleft project compliant.
* `cargo vet` for dependencies inside a security boundary.
* `cargo auditable build` embeds the dependency list in the binary, so `cargo audit bin`, Trivy, Grype or Syft can scan the shipped file later.
* Malicious crates are real (typosquats, hijacked releases, build-time payloads). Check the crate name letter by letter, prefer crates with several maintainers and recent releases, read `build.rs` and proc-macro crates before adding them.
* Publishing: crates.io trusted publishing from GitHub Actions (or GitLab.com) instead of a long-lived API token, with "trusted publishing only" enabled on the crate.

## Testing
* `cargo fuzz` on every function that takes bytes from a file or a socket. Commit the corpus; each crash becomes a `#[test]`.
* `proptest` for round-trip invariants: encode then decode returns the input.
* Sanitizers on the FFI boundary, Miri on the `unsafe` core.

## Tuning
* `criterion` for benchmarks (variance, regression detection). Profile with `cargo flamegraph` or `perf`. Debug-build numbers mean nothing.
* `[profile.release]`: `lto = "fat"`, `codegen-units = 1`, and `panic = "abort"` for binaries that do not rely on unwinding. Measure each; LTO costs build time.
* Allocation is usually the cost: reuse buffers, `Vec::with_capacity` from trusted sizes, `&str` over `String`, iterators instead of intermediate collections.
* `rayon` for data parallelism. Do not hand-roll threads for a parallel map.

## Traps and fixes
* `.unwrap()` on parsed input: one bad file kills the service. Fix: `?` with a typed error.
* `as` casts truncate silently (`len as u32`). Fix: `u32::try_from(len)?`; Clippy `cast_possible_truncation` flags them.
* `Path::join` with user input: absolute path escapes the base. Fix: reject absolute and `..`, then check containment.
* `std::env::set_var` in a threaded program: unsound. Fix: set before threads start or pass values explicitly.
* Blocking I/O inside an async task: stalls the runtime. Fix: `spawn_blocking` or the async API.
* `RefCell` borrowed twice at run time: panic. Fix: shorter borrows or restructure ownership.
* Missing `--locked` in CI or Docker: builds a different dependency set than the one tested.

## Adding Rust to a C or C++ codebase
* Matches the CISA and NSA memory-safety guidance (see `c-cpp.md`): no rewrite of a working system. Pick one module with hostile input (a parser, a decoder), reimplement it behind the same C ABI, run differential fuzzing against the old one, then switch.
* Expose `#[unsafe(no_mangle)] pub extern "C" fn` with only C types, generate the header with `cbindgen`, and build a static library the existing CMake target links.
* Keep the old implementation available behind a build option until the new one has run in production.
