# Evidence log: normas (standards, sources, compliance, GUI refresh)

Files: `references/security-baseline.md`, `references/versoes-e-fontes.md`, `references/compliance-licencas.md`, `references/qt.md`, `references/gui-desktop.md`, `references/gui-outros.md`.

## Verified facts

### Standards
- OWASP Top 10: 2025 edition published; A01 Broken Access Control, A02 Security Misconfiguration, A03 Software Supply Chain Failures, A04 Cryptographic Failures, A05 Injection, A06 Insecure Design, A07 Authentication Failures, A08 Software or Data Integrity Failures, A09 Security Logging and Alerting Failures, A10 Mishandling of Exceptional Conditions; no newer edition mentioned (https://top10.owasp.org/2025, checked 2026-11-20)
- OWASP Top 10: owasp.org/Top10 now redirects (308) to top10.owasp.org (https://owasp.org/Top10/2025/, checked 2026-11-20)
- OWASP ASVS: latest stable release is v5.0.0 (tag v5.0.0_release, 30 May); only a "latest" bleeding-edge build after it (https://github.com/OWASP/ASVS/releases, checked 2026-11-20)
- OWASP API Security Top 10: current edition is 2023; no newer edition listed; owasp.org/API-Security redirects to api-security.owasp.org (https://api-security.owasp.org/, checked 2026-11-20)
- OWASP Top 10 for LLM Applications: current edition 2025, LLM01 Prompt Injection to LLM10 Unbounded Consumption (https://genai.owasp.org/llm-top-10/, checked 2026-11-20)
- OWASP Top 10 for Agentic Applications for 2026: published 9 December 2025 (https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/, checked 2026-11-20)
- CWE Top 25: most recent list is the 2025 edition (https://cwe.mitre.org/top25/, checked 2026-11-20)
- OWASP Password Storage Cheat Sheet: Argon2id minimum m=19 MiB, t=2, p=1; scrypt N=2^17, r=8, p=1; bcrypt work factor at least 10, 72-byte input limit; PBKDF2-HMAC-SHA256 600,000 iterations when FIPS-140 is required (https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html, checked 2026-11-20)
- NIST SP 800-63B-4: Final, published July 2025, supersedes SP 800-63B (https://csrc.nist.gov/pubs/sp/800/63/b/4/final, checked 2026-11-20)
- NIST SP 800-63B-4: password minimum 15 characters when it is the only factor, 8 when used only inside MFA; SHOULD permit at least 64; SHALL NOT impose composition rules; no periodic change without evidence of compromise; check against a blocklist of common, expected or compromised values (https://pages.nist.gov/800-63-4/sp800-63b.html, checked 2026-11-20)
- NIST SP 800-218 SSDF: Version 1.1 final (February 2022) remains the final (https://csrc.nist.gov/pubs/sp/800/218/final, checked 2026-11-20)
- NIST SP 800-218 Rev. 1 (SSDF 1.2): initial public draft 17 December 2025, comments closed 30 January 2026, not final (https://csrc.nist.gov/pubs/sp/800/218/r1/ipd, checked 2026-11-20)
- PCI DSS: v4.0.1 is the "currently published" version; PCI SSC opened an RFC on it from 3 June to 20 July 2026 to begin the next iteration; no next version named (https://blog.pcisecuritystandards.org/request-for-comments-pci-data-security-standard-pci-dss-v4.0.1, checked 2026-11-20)
- EU CRA: entry into force 10 December 2024; reporting obligations apply from 11 September 2026; main obligations from 11 December 2027 (https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act, checked 2026-11-20)
- EU CRA: Art. 71: Chapter IV (notification of conformity assessment bodies) applies from 11 June 2026, Art. 14 from 11 September 2026, rest from 11 December 2027; Art. 14: early warning 24 h, notification 72 h, final report 14 days after a corrective measure for actively exploited vulnerabilities, one month for severe incidents (https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng, checked 2026-11-20)

### Brazil (LGPD, ANPD)
- ANPD: the body is now the Agencia Nacional de Protecao de Dados (ANPD), a special-nature autarchy; Lei 15.352 of 25 February 2026 (conversion of MP 1.317/2025) amended the LGPD and made the agency the successor of the Autoridade (https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/L15352.htm, checked 2026-11-20)
- ANPD: site header reads "Agencia Nacional de Protecao de Dados" (https://www.gov.br/anpd/pt-br, checked 2026-11-20)
- Resolucao CD/ANPD 15/2024: art. 6 caput, notice to ANPD in 3 business days; art. 6 par. 1, counted from when the controller learns personal data was affected; art. 6 par. 3, complement within 20 business days; art. 6 par. 8 and art. 9 par. 6, deadlines doubled for small processors; art. 9, notice to data subjects in 3 business days; art. 10, incident record kept at least 5 years (https://www.normasbrasil.com.br/norma/resolucao-15-2024_458235.html, checked 2026-11-20; mirror, official gov.br page returned 404)
- Resolucao CD/ANPD 2/2022: art. 3 excludes from the small-processor regime agents doing high-risk processing (save art. 8), with gross revenue above the LC 123/2006 art. 3 II limit, or in a group above it (https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022, checked 2026-11-20)
- Resolucao CD/ANPD 2/2022: art. 14 II (as amended by Res. 15/2024) doubles deadlines for small processors on incident communication; art. 13 allows a simplified information security policy; art. 11 exempts small processors from naming an encarregado but requires a communication channel with the data subject (https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022, checked 2026-11-20)

### endoflife.date
- endoflife.date: legacy `https://endoflife.date/api/<product>.json` and `https://endoflife.date/api/all.json` both return 200 (https://endoflife.date/api/php.json, checked 2026-11-20)
- endoflife.date: v1 API `https://endoflife.date/api/v1/products/<product>/` returns 200, schema_version 1.2.1; product list at `https://endoflife.date/api/v1/products/` (489 products) (https://endoflife.date/api/v1/products/, checked 2026-11-20)
- endoflife.date covers: lua, perl, julia, kotlin, scala, elixir, erlang, ghc (Haskell), apache-groovy, powershell, windows-powershell, deno, bun, ibm-db2, duckdb, cockroachdb, apache-cassandra, elasticsearch, opensearch, neo4j, clickhouse, influxdb, valkey (https://endoflife.date/api/v1/products/, checked 2026-11-20)
- endoflife.date does not cover: R, Fortran compilers, Zig, Ada/GNAT, Delphi/RAD Studio, Free Pascal, Lazarus, Harbour, GnuCOBOL (only visual-cobol), Swift, Dart, Flutter, OCaml, Clojure, TypeScript, Firebird, DynamoDB, GCC (https://endoflife.date/api/v1/products/, checked 2026-11-20)

### Maintainer sources (reachable, and content checked where noted)
- Lua: lua.org/versions.html (https://www.lua.org/versions.html, checked 2026-11-20)
- Perl: support policy in perlpolicy (https://perldoc.perl.org/perlpolicy, checked 2026-11-20)
- R: r-project.org front page lists releases with dates (https://www.r-project.org/, checked 2026-11-20)
- Julia: downloads page names the current stable and the LTS release (https://julialang.org/downloads/, checked 2026-11-20)
- Fortran: fortran-lang.org/compilers lists gfortran, LFortran and others; gfortran ships with GCC (https://fortran-lang.org/compilers/, checked 2026-11-20)
- GCC: release list (https://gcc.gnu.org/releases.html, checked 2026-11-20)
- Zig: download page shows "Latest Stable Version" 0.x, pre-1.0 (https://ziglang.org/download/, checked 2026-11-20)
- Ada: Alire provides GNAT FSF toolchains (https://alire.ada.dev/, checked 2026-11-20)
- Delphi/RAD Studio: embarcadero.com/products/rad-studio reachable; its FAQ block still mentions 11.3 while the What's New page announces 13.2 Florence, so read the What's New page (https://www.embarcadero.com/products/rad-studio, checked 2026-11-20)
- Free Pascal: download page names the latest release (https://www.freepascal.org/download.html, checked 2026-11-20)
- Lazarus: front page announces releases (https://www.lazarus-ide.org/, checked 2026-11-20)
- Harbour: harbour.github.io still lists 3.0.0 (2011-07-17) as "latest stable"; development is in the GitHub repo (https://harbour.github.io/, checked 2026-11-20)
- GnuCOBOL: project page names the current release; source kits at ftp.gnu.org/gnucobol (https://gnucobol.sourceforge.io/, checked 2026-11-20)
- Swift: swift.org/blog announces releases; install page at swift.org/install (https://www.swift.org/blog/, checked 2026-11-20)
- Kotlin: releases page (https://kotlinlang.org/docs/releases.html, checked 2026-11-20)
- Dart: "The Dart team supports only the latest stable release of the SDK" (https://dart.dev/get-dart, checked 2026-11-20)
- Flutter: release archive; docs.flutter.dev/release/archive redirects to /install/archive (https://docs.flutter.dev/install/archive, checked 2026-11-20)
- Scala: all releases (https://www.scala-lang.org/download/all.html, checked 2026-11-20)
- Elixir: compatibility and deprecations page (https://hexdocs.pm/elixir/compatibility-and-deprecations.html, checked 2026-11-20)
- Erlang/OTP: downloads (https://www.erlang.org/downloads, checked 2026-11-20)
- Haskell/GHC: haskell.org/ghc (https://www.haskell.org/ghc/, checked 2026-11-20)
- OCaml: releases (https://ocaml.org/releases, checked 2026-11-20)
- Clojure: downloads and releases (https://clojure.org/releases/downloads, checked 2026-11-20)
- Groovy: download page (https://groovy.apache.org/download.html, checked 2026-11-20)
- PowerShell: support lifecycle (https://learn.microsoft.com/powershell/scripting/install/powershell-support-lifecycle, checked 2026-11-20)
- TypeScript: GitHub releases and devblog (https://github.com/microsoft/TypeScript/releases, checked 2026-11-20)
- Deno: stability and releases (https://docs.deno.com/runtime/fundamentals/stability_and_releases/, checked 2026-11-20)
- Bun: blog with release posts (https://bun.com/blog, checked 2026-11-20)
- Firebird: release policy, series first released more than five years ago are discontinued; no version table, points to roadmap (https://firebirdsql.org/en/release-policy/, checked 2026-11-20)
- Db2: Db2 Distributed end of support dates table (https://www.ibm.com/support/pages/db2-distributed-end-support-eos-dates, checked 2026-11-20)
- DuckDB: release calendar (https://duckdb.org/release_calendar, checked 2026-11-20)
- CockroachDB: release support policy (https://www.cockroachlabs.com/docs/releases/release-support-policy, checked 2026-11-20)
- Cassandra: download page with supported releases (https://cassandra.apache.org/_/download.html, checked 2026-11-20)
- Elasticsearch: Elastic product end-of-life dates (https://www.elastic.co/support/eol, checked 2026-11-20)
- OpenSearch: releases (https://opensearch.org/releases/, checked 2026-11-20)
- Neo4j: supported versions article; neo4j.com URL redirects to support.neo4j.com (https://neo4j.com/developer/kb/neo4j-supported-versions/, checked 2026-11-20)
- ClickHouse: SECURITY.md carries the table of versions supported with security updates (https://github.com/ClickHouse/ClickHouse/blob/master/SECURITY.md, checked 2026-11-20)
- InfluxDB: docs list InfluxDB 3 Core/Enterprise, InfluxDB 2 and InfluxDB 1 products (https://docs.influxdata.com/, checked 2026-11-20)
- Valkey: releases page carries a supported versions table (maintenance and security support end); SECURITY.md has only a reporting contact (https://valkey.io/topics/releases/, checked 2026-11-20)
- DynamoDB: managed service; AWS SDKs and Tools maintenance policy and DynamoDB Local docs (https://docs.aws.amazon.com/sdkref/latest/guide/maint-policy.html, checked 2026-11-20)

### Qt and GUI
- Qt: LTS 6.8 open source support ended 2025-04-02, commercial to 2029-10-08; LTS 6.12 (2026-09-30) open source to 2027-04-01, commercial to 2031-10-01; open source users are expected to move to each new minor release about every 6 months (https://endoflife.date/qt, checked 2026-11-20)
- Qt 5: 5.15 open source support ended 2020-12-08; commercial support ended 2025-05-25; KDE maintains a 5.15 patch collection for open source users (https://endoflife.date/qt, checked 2026-11-20)
- Qt: QStyleHints::colorScheme is (since 6.5) and follows the system scheme, with a change signal (https://doc.qt.io/qt-6/qstylehints.html, checked 2026-11-20)
- Qt: qt_standard_project_setup and qt_generate_deploy_app_script introduced in Qt 6.3 (https://doc.qt.io/qt-6/qt-generate-deploy-app-script.html, checked 2026-11-20)
- Qt: QT_DISABLE_DEPRECATED_UP_TO documented; should be set to the minimum Qt version supported (https://doc.qt.io/qt-6/qtglobal.html, checked 2026-11-20)
- Qt: QProcess in Qt 6 has startCommand (6.0+) and splitCommand; QProcess never uses a shell automatically; startCommand tokenization can allow argument injection; untrusted arguments to .bat/.cmd or cmd.exe on Windows are command injection even when passed separately (https://doc.qt.io/qt-6/qprocess.html, checked 2026-11-20)
- Slint: licences are GPLv3, Royalty-Free (excluding embedded systems), and commercial (Enterprise, Small Enterprise, Startup & Individual) (https://slint.dev/pricing, checked 2026-11-20)
- Slint: 1.17 (24 June 2026) added drag and drop within the application with DragArea and DropArea; dragging to and from other applications not yet supported, in development upstream in winit (https://slint.dev/blog/slint-1.17-released, checked 2026-11-20)
- Slint: 1.18 (16 Sep 2026) and 1.19 (16 Nov 2026) release posts do not mention external drag and drop (https://slint.dev/blog/slint-1.19-released, checked 2026-11-20)
- Electron: nodeIntegration off by default since 5.0.0, contextIsolation since 12.0.0, sandbox since 20.0.0; checklist includes validating IPC sender, custom protocol over file://, fuses (https://www.electronjs.org/docs/latest/tutorial/security, checked 2026-11-20)
- Electron: majors 40 to 45 released in 2026, each supported about six months (https://endoflife.date/api/v1/products/electron/, checked 2026-11-20)
- GTK4: GtkTreeView and GtkListStore deprecated since GTK 4.10 (https://docs.gtk.org/gtk4/class.TreeView.html, checked 2026-11-20)
- Tauri 2: capabilities grant permissions per window or webview; remote URL access is opt-in through `remote.urls` and needs care (https://v2.tauri.app/security/capabilities/, checked 2026-11-20)
- Avalonia 12: IDataObject removed, DragDrop.DoDragDrop replaced by DoDragDropAsync with DataTransfer, DataFormats.* by DataFormat.*; Avalonia no longer uses BinaryFormatter for clipboard; compiled bindings on by default (https://docs.avaloniaui.net/docs/avalonia12-breaking-changes, checked 2026-11-20)
- Avalonia: files via `DataFormat.File` and `TryGetFiles()` (https://docs.avaloniaui.net/docs/how-to/drag-and-drop-how-to, checked 2026-11-20)
- egui: eframe enables AccessKit by default on native platforms where an adapter exists; plain egui integrations opt in with Context::enable_accesskit() (https://raw.githubusercontent.com/emilk/egui/main/docs/accessibility.md, checked 2026-11-20)
- Python: PEP 779 Final, free-threaded build officially supported but optional from 3.14 (https://peps.python.org/pep-0779/, checked 2026-11-20)

## Changed from the previous text
- security-baseline: title and severity scale em dashes removed.
- security-baseline: A04 bcrypt "cost >= 12" replaced by the OWASP minimum (work factor >= 10, raise as the server allows); added PBKDF2-HMAC-SHA256 600,000 iterations for FIPS cases.
- security-baseline: A07 now carries the NIST SP 800-63B-4 rules (15 chars single-factor, 8 inside MFA, accept at least 64, no composition rules, blocklist).
- security-baseline: LGPD section renamed the authority (Agencia Nacional de Protecao de Dados, Lei 15.352/2026), added notice to data subjects (art. 9), doubled deadlines for small processors, 5-year incident record, simplified security policy and encarregado exemption for small processors (Res. 2/2022).
- security-baseline: incident section deadline now notes the doubled deadline for qualifying small processors (art. 3 conditions).
- security-baseline: LLM section points to the Agentic Top 10 for tool-using agents.
- security-baseline: standards map dated 2026-11-20; added Agentic Top 10 2026, CWE Top 25 2025, SSDF 1.1 final with 1.2 draft, PCI DSS 4.0.1 with the 2026 RFC, Res. 2/2022, CRA dates.
- versoes-e-fontes: title em dash removed; endoflife.date paragraph keeps both API forms (verified) and says products may be missing; added 36 stack rows with endoflife.date slugs or "not on endoflife.date"; OWASP sources updated to top10.owasp.org and api-security.owasp.org.
- compliance-licencas: title em dash removed; CRA adds Chapter IV date (11 June 2026) and the severe incident reporting chain.
- qt.md: title em dash removed; version policy now says open source users get fixes only on the newest minor release, LTS maintenance (6.8, 6.12) is commercial; Qt 5.15 open source support ended 2020, standard commercial May 2025, KDE patch collection noted; colorScheme gated (6.5+); QProcess line rewritten for Qt 6 (no single-string start, startCommand argument injection, batch files on Windows); deployment adds qt_generate_deploy_app_script (6.3+).
- gui-desktop.md: title em dash removed; Slint licence cell updated; virtualisation note says GtkTreeView/GtkListStore are deprecated since 4.10; embedded webview line adds sandbox.
- gui-outros.md: Slint drag and drop updated (in-app since 1.17, cross-app not announced through 1.19); Slint licence names; Avalonia drag and drop gated (12+) with the 11.x idiom kept; GTK 4.10 deprecation; Tauri v1 allowlist replaced by v2 capabilities and permissions; Electron sandbox default (20+) and IPC sender validation; egui accessibility corrected (AccessKit); Python GIL line notes the optional free-threaded build (3.14+).

## Not verified
- ISO/IEC 27001:2022 still current and Amendment 1:2024: only search summaries and resellers; iso.org returned 403. Kept "ISO/IEC 27001:2022" unchanged.
- CWE Top 25 2025 release date (11 December 2025) and ranking: search summaries only; not written into the files.
- OWASP Agentic Top 10 entry names (ASI01 to ASI10): secondary sources only; not written.
- Resolucao CD/ANPD 15/2024: read on a legal mirror (normasbrasil); the gov.br page for it returned 404. Res. 2/2022 was read on gov.br and confirms the doubling.
- New 2025-2026 ANPD acts on incident reporting: none found, but the DOU was not searched directly.
- Embarcadero docwiki (403 on both tools): not cited.
- Tool commands inside security-baseline.md (gitleaks, trufflehog, osv-scanner, trivy, the per-language auditors, header values): outside this assignment, not re-checked.
- Avalonia `DataFormats.Files` in 11.x, and when the old DataObject API became obsolete in 11.x: not verified; only the removal in 12 is verified.
- gui-desktop.md toolkit table: licence cells other than Slint, and the cold-start numbers: not re-checked.
- Dear ImGui having no platform accessibility tree: kept from the old text, not re-verified.
- Zig "any release may break source compatibility": inferred from the 0.x version on ziglang.org, not quoted from a policy page.
- Lei 15.352/2026 keeping earlier ANPD resolutions in force: not checked, so not written.
- REUSE specification version and `reuse lint` command: not re-checked, left as written.

## Lead decisions
- bcrypt: kept cost 12 as the default and stated the OWASP floor of 10 (https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html gives 10 as the minimum). The default of 12 is a project choice, not a quoted figure.
