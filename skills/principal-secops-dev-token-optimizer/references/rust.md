# Rust — current stable and edition

Version policy: follow `versoes-e-fontes.md`. Use the current stable toolchain and the newest edition the project's dependencies support (check doc.rust-lang.org/edition-guide); set `edition` and `rust-version` in `Cargo.toml`. Pin the toolchain in `rust-toolchain.toml` so every machine and CI build use the same compiler, and update the pin deliberately when a new stable is checked.

## Language and standards
* `rustfmt` on commit. `clippy -- -D warnings` in CI, with `clippy::pedantic` where the crate can afford it.
* `#![forbid(unsafe_code)]` on every crate that does not genuinely need `unsafe`. Confine `unsafe` to one crate and put a safe API on top of it.
* Errors: `thiserror` for library error types, `anyhow` only in binaries, `?` for propagation.
* `unwrap()` and `expect()` only where a panic is the correct behavior, with a message naming the invariant. Never on a path reachable from untrusted input.
* Panics are not an error strategy across an FFI boundary or in a long-running process. Use `catch_unwind` at the boundary, or design so it cannot panic.

## Documentation
* `#![warn(missing_docs)]` on public crates.
* Doc comments carry an `# Errors` section on anything returning `Result`, and a `# Safety` section on every `unsafe fn`.
* Examples in doc comments are compiled and run by `cargo test`, so they cannot rot. Prefer one runnable example over prose.

## unsafe discipline
* Every `unsafe` block gets a `// SAFETY:` comment naming the invariant that makes it sound. Enforce with `clippy::undocumented_unsafe_blocks`.
* Every `unsafe fn` gets a `/// # Safety` section stating what the caller must guarantee.
* `unsafe` is not a performance tool. Measure before assuming the safe version is slower; bounds checks are usually hoisted out of loops.
* `cargo miri test` on anything containing `unsafe`. It finds undefined behavior that no test will.

## FFI to C: the contract goes before the call
The wrapper exists to make the C function's preconditions impossible to violate. **A check placed after the call is worthless.** If the C side wrote past the buffer, memory is already corrupt, the process is already unsound, and returning an error does not undo it. Validating an out-length after the call detects a buggy C function reporting a wrong size; it does not detect or prevent an overflow.

* Establish every bound before the call. Pass the real capacity and never a value the C side could grow.
* An in-out length parameter that carries capacity in and size out is read back into a local. Never let a later bound depend on the same variable the C side just wrote.
* Treat every value the C side writes as untrusted on return. Clamp it before it reaches a slice or an index.
* Generate declarations with `bindgen`, so a signature change on the C side fails the build instead of silently corrupting memory.
* Declare `unsafe extern "C"`. Map the C status code to a typed Rust error at the boundary; a nonzero return never flows on as success.
* `#[repr(C)]` on every struct that crosses. Never send a Rust enum, `String` or `Vec` across.
* When the C function writes an arbitrary amount, give it a buffer you sized and have it report what it used, then `truncate`. Never let it allocate for you unless you also call its matching free function.
* Run the FFI test suite under ASan. Miri cannot see into the C side.

## Supply chain
* `cargo audit` and `cargo deny` in CI. `cargo deny` also enforces a license allowlist, which is what keeps a copyleft project compliant.
* `Cargo.lock` committed for binaries. `cargo vet` for dependencies inside a security boundary.
* Every dependency is code you ship. In a parser, a crate with one maintainer and no release in two years is a liability.

## Testing
* `cargo fuzz` on every function that takes bytes from a file or a socket. Commit the corpus; each crash becomes a `#[test]`.
* `proptest` for round-trip invariants: encode then decode returns the input.
* Sanitizers on the FFI boundary, Miri on the `unsafe` core.

## Performance
* `criterion` for benchmarks, because it reports variance and detects regressions. Profile with `cargo flamegraph` or `perf`. Numbers from a debug build mean nothing.
* `[profile.release]` with `lto = "fat"`, `codegen-units = 1`, and `panic = "abort"` for binaries. Measure each one; LTO costs build time.
* Allocation is usually the cost. Reuse buffers, `Vec::with_capacity`, `&str` over `String`, iterator chains instead of intermediate collections.
* `rayon` for data parallelism. Do not hand-roll threads for a parallel map.
