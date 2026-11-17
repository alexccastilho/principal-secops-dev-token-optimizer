# Compliance for distributed software — licensing, SBOM, CRA

For anything shipped as a downloadable binary or reusing third-party source. Personal data and LGPD stay in `security-baseline.md`; this file is about the product itself.

## License compatibility
* Decide the project license before writing code. Changing it later needs the agreement of every contributor.
* Combining code means the result must satisfy every input license at once. Permissive terms (MIT, BSD, Apache-2.0) flow into copyleft. Copyleft does not flow back out.
* GPLv3 accepts MIT, BSD-2 and BSD-3, Apache-2.0, LGPLv2.1 or later, LGPLv3, and MPL-2.0 as part of a GPL whole. LGPL code may be used under the GPL; the reverse is not true.
* Apache-2.0 is compatible with GPLv3 but not with GPLv2, because of the patent clause. A GPLv2-only dependency and an Apache-2.0 one cannot be combined.
* **A license carrying an added restriction is incompatible with the GPL, however reasonable the restriction sounds.** Non-commercial clauses, field-of-use limits and most "source available" terms all fall here. A component under such terms belongs in an optional, separately distributed plugin with its own build, never linked into the main binary. Document why.
* Never copy code without checking its license and preserving its copyright notices, including a few lines from an answer found online.

## Attribution and file headers
* SPDX identifier as the first comment line of every source file, with a copyright line beside it:
  ```
  // SPDX-FileCopyrightText: 2026 <holder>
  // SPDX-License-Identifier: GPL-3.0-or-later
  ```
  It is machine-readable and it survives the file being copied elsewhere.
* Follow the REUSE specification: full license texts in `LICENSES/`, every file covered, checked by `reuse lint` in CI.
* Ship a `THIRD-PARTY-NOTICES` file listing every bundled component with its license and version. Apache-2.0 and BSD both require this.
* Keep third-party sources in their own directory, unmodified where possible, with local changes as separate patches. That is what makes a license audit finishable.

## SBOM and supply chain
* Generate an SBOM in CycloneDX or SPDX format as a build artifact on every release, produced from the actual build rather than written by hand.
* It lists transitive dependencies with versions and hashes. That is what lets you answer "are we affected?" in minutes on the day a vulnerability is published.
* Pin toolchain versions. The compiler is part of the supply chain.
* Publish the SBOM next to the release, with the checksums and signatures.

## EU Cyber Resilience Act (Regulation 2024/2847)
Applies to products with digital elements placed on the EU market, including software given away when there is a commercial dimension. Purely non-commercial open source development is out of scope, but donations, paid support or a commercial edition can pull a project in. Check the current scope rather than assuming a free project is exempt.

* In force since 10 December 2024. The vulnerability and incident **reporting obligations have applied since 11 September 2026**; the **full obligations and CE marking apply from 11 December 2027**.
* Reporting an actively exploited vulnerability: early warning within 24 hours, notification within 72 hours, final report within 14 days of a fix being available.
* What to build in from the start rather than retrofit: secure-by-default configuration, no known exploitable vulnerabilities at release, an SBOM, a documented vulnerability handling process, a security contact with a coordinated disclosure policy, security updates over a stated support period, and integrity verification of updates.
* A `SECURITY.md` carrying a contact address and a response commitment is the minimum entry point.

## Versioning and change history
* Semantic versioning. Track the file format version separately from the application version; they change at different rates.
* `CHANGELOG.md` in Keep a Changelog format, with security fixes called out and their CVE identifier where one exists.
* Architecture Decision Records for choices that are expensive to reverse: file format, threading model, GUI toolkit. One short file per decision, giving the context, the decision and what was rejected.
