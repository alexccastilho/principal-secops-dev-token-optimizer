# Native desktop apps and file parsers: threat model

The web baseline does not apply here. There is no CSRF, no cookie, no webroot. The attack surface is a file the user received from someone else, plus the process boundary on the user's own machine.

Read this for anything that ships as an installable binary, parses files it did not create, or extracts content to disk. Memory-safety rules live in `c-cpp.md` and `rust.md`.

## The file is the attacker
Treat every byte of a document, archive, image or package as chosen by someone trying to break you. Structure the parser accordingly: validate the header before allocating from it, keep a running bound on what has been consumed, and fail closed on anything unexpected. A parser that "recovers" from a malformed field is a parser that keeps going with attacker-controlled state.

## Extraction: writing attacker-named files to disk
Each of these has shipped as a CVE in a widely used archiver. The first is well known. The rest are the ones that get missed.

1. **Path traversal (Zip Slip).** Reject absolute and drive-qualified paths, then resolve the joined path and verify it is still under the destination. A string prefix test is wrong: `/home/user/docs` also prefixes `/home/user/docs-evil`. Compare after normalization, component by component, requiring a separator at the boundary.
2. **Symlink escape.** Containment passes, then a later entry writes *through* a symlink an earlier entry created. Either refuse to create links on extraction, or open every file with `O_NOFOLLOW` (`CREATE_NEW` plus reparse-point rejection on Windows) and re-verify the parent at open time, not at plan time.
3. **Hard links and reparse points.** Same class. An entry that hard-links to a file outside the destination lets the archive overwrite it.
4. **Windows name hazards**, none of which an `is_absolute` check catches:
   * Reserved device names: `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`, with or without an extension.
   * Alternate Data Streams: `nota.pdf:payload.exe` writes a hidden stream.
   * Trailing dots and spaces are stripped silently by the filesystem, so `evil.exe .` lands as `evil.exe` and slips a check on the literal name.
   * `\?\` and UNC prefixes, and drive-relative paths such as `C:file`.
   * Case-insensitive collisions: two entries differing only in case overwrite each other.
5. **TOCTOU.** Validate and open in as few steps as possible and act on the handle, not on the path. A check against a path is a statement about the past.
6. **Never restore setuid, setgid or world-writable bits** from archive metadata, and never restore an owner. Clamp modes to what the extracting user should get.
7. Reject rather than normalize: empty names, `.` or `..` as a whole component, embedded NUL bytes, and names that are not valid UTF-8.

## Resource exhaustion
* **Decompression bombs.** Enforce a maximum output size and a maximum compression ratio per entry, plus a total for the archive. Check mid-stream and abort; never buffer the whole output to find out how big it was.
* **Nesting and blowup.** Cap recursion depth for nested archives and directory depth, and cap the number of entries.
* Bound memory per operation. Window and dictionary sizes are validated fields with a ceiling, not whatever the header claims.
* Every limit is a named constant with a comment explaining the number, and overridable by a user who genuinely needs more.

## Process and platform hardening
* **Library hijacking.** Windows: `SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_SYSTEM32)` early, load with absolute paths, never depend on the current directory. Linux: no writable directory on the search path, prefer `RUNPATH` with `$ORIGIN`.
* Never require administrator or root to extract a file. Run with the least privilege the operation needs.
* Shell integration and context-menu handlers run inside another process. Keep them small, with no parsing logic of their own.
* Self-extracting archives are executables assembled from attacker data. Sign them, and never let the stub interpret payload content before verifying it.
* Temporary files via `mkstemp` or `GetTempFileName`, in a directory the user owns, cleaned up on failure paths as well as success.
* Verify a signature before applying any update. An auto-updater without signature verification is a malware distribution channel.

## Release integrity
* Sign the binaries: Authenticode on Windows, a detached GPG signature plus a checksum file on Linux, notarization on macOS.
* Publish checksums through a channel separate from the download.
* Reproducible builds where the toolchain allows, so a third party can confirm the binary matches the source.
* Ship an SBOM with each release. See `compliance-licencas.md`.

## Pre-delivery checklist (native code)
Run this on top of the gate in `SKILL.md`, for C, C++ and Rust FFI.

```
- [ ] Every length or count from the input validated against the bytes actually available
- [ ] Every size arithmetic on input overflow-checked (ckd_mul, __builtin_mul_overflow)
- [ ] Byte order explicit at every read and write of a multi-byte field
- [ ] Every allocation checked, freed once, on every error path
- [ ] Any path built from input confined to the destination, component-wise, after normalizing
- [ ] No -march=native in a build that ships; hardening flags present
- [ ] Bounds established before an FFI call, never checked after it
- [ ] A build file for code that parses untrusted input carries a sanitizer configuration in it
```
