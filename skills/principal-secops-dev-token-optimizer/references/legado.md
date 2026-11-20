# Legacy and business stacks: Delphi, Pascal, Clipper/Harbour, FoxPro, VB6, COBOL, RPG, OpenEdge, PowerBuilder, ABAP

Version policy: follow `versoes-e-fontes.md`. Read the version from the project itself: the IDE "About" box, the compiler's version output, the project file the IDE saves, or ask the person who maintains the server (IBM i, OpenEdge, SAP). Lifecycles: endoflife.date when listed, otherwise the vendor page named in each section. Many of these products have no supported compiler any more; say so as a finding, never as a reason to rewrite.

## Contents
- The rule for any legacy system
- Cross-cutting fixes (all stacks)
- Delphi / Object Pascal
- Free Pascal, Lazarus, Turbo Pascal code
- Clipper, Harbour, xHarbour
- Visual FoxPro
- Visual Basic 6
- COBOL
- RPG on IBM i
- Progress OpenEdge ABL
- PowerBuilder
- SAP ABAP
- Staged migration (strangler pattern)

## The rule for any legacy system
* **Never rewrite a working legacy system.** It encodes years of tax, stock and billing rules nobody wrote down. A rewrite loses them and stops the business. Make it safe where it stands, then migrate piece by piece.
* **Backup before any change, every time.** DBF/CDX/NTX/FPT/DBC folders, `.mdb`, Firebird `.fdb`, the SQL database dump, the source folder and the compiled `.exe`. Close the system on every workstation first: a copy of an open DBF can be inconsistent. Restore once to a test folder to prove the backup works.
* Say it in pt-BR before anything: "Antes de mexer, feche o sistema em todos os computadores e copie a pasta inteira dos dados para um pendrive ou outro disco. Sem essa cópia eu não altero nada."
* **Keep the old build reproducible.** Find the exact compiler, version and third-party components (packages, OCX, VCX, FLL, LIB) that build today's `.exe`. Without that, the first rebuild can change behaviour. Archive the installer media and license keys with the source.
* **Change one thing at a time, compare outputs.** Same input, old `.exe` vs new `.exe`: totals, tax values, report pages, the XML of the fiscal document. Any difference is a bug until proven otherwise.
* **No source code?** Do not decompile and "fix" the binary. Isolate it (network, permissions, backups) and plan the migration around its data.

## Cross-cutting fixes (all stacks)
* **SQL by concatenation.** Replace `"... WHERE CODE = '" + edit.Text + "'"` with the stack's parameter mechanism (each section below). Values only; table and column names come from a fixed whitelist in code, never from input.
* **Plain-text passwords in INI, registry or a DBF users table.** User passwords: store a salted slow hash (Argon2id or bcrypt through a maintained library); if the stack has none, call one through a DLL or move login to the database server. Database credentials on Windows: encrypt the INI value with DPAPI (`CryptProtectData`, per user by default, machine scope by flag) instead of plain text or home-made XOR. Never the same `sa`/`SYSDBA`/`admin` password on every client.
* **Database login with full rights.** Create an application user with only the rights it needs. `sa`, `SYSDBA`, `root` or `postgres` in a client INI means every workstation holds the master key.
* **Windows share for the DBF folder.** DBF/VFP/Paradox files have no access control of their own: whoever reads the folder reads every customer, price and password. Share and NTFS permissions: only the group of system users, Modify (not Full Control), never `Everyone`/`Todos`. Remove the share from computers that do not run the system. Backups stored off the share, so ransomware on a workstation cannot encrypt them.
* **DBF corruption on network shares.** Index corruption ("índice corrompido", wrong record counts) is often linked to SMB client caching (oplocks / leasing) on file-based databases. Guidance differs by Windows version; do not change server SMB settings without the person responsible for the network and a backup. Also check: same compiler build on every station, no antivirus scanning the data folder in real time, no Wi-Fi workstations writing to DBF.
* **TLS for NF-e, NFC-e, CT-e and other SEFAZ webservices.** SEFAZ requires TLS 1.2 (introduced with NF-e 4.00, older protocols disabled by the states). Fix by stack: Delphi/Lazarus via the OS HTTP client or a current OpenSSL; Harbour via `hbssl` against current OpenSSL; VB6/VFP via the OS stack (WinHTTP) on a supported Windows. Never "fix" a handshake error by allowing SSLv3 or TLS 1.0: that is a downgrade, and SEFAZ refuses it anyway.
* **Digital certificate (A1 `.pfx` / A3 token).** The `.pfx` and its password are secrets: never in the source, the repo or a shared folder readable by all; restrict the folder to the user that emits the notes. A3 tokens are used through the Windows certificate store (in ACBr, the WinCrypt setting).
* **Errors fail closed.** Legacy code often uses `ON ERROR RESUME NEXT`, empty `except`, `BEGIN SEQUENCE ... END` that swallows, `ON ERROR *`. Around money, stock and fiscal steps, an error must stop the operation, log it, and roll back.
* **Supply chain.** Third-party components (VCL packages, OCX, FLL, Harbour contrib, ACBr) are dependencies: record the exact version and source, download only from the maintainer, keep the installer archived.

## Delphi / Object Pascal
* **Run and build today.** RAD Studio / Delphi from Embarcadero; Community Edition is free while the individual or company earns under US$5,000 a year and has at most five developers (check the current license text before recommending it to a company). A project from an old Delphi usually opens in a new one, but VCL third-party packages (reports, grids, BDE components) must exist for the new version: list them before upgrading. Upgrading the compiler is a project of its own, never a side effect of a bug fix.
* **Style.** Follow the project's existing conventions and the IDE formatter. One unit per form or responsibility; business rules out of `OnClick` handlers into separate units over time.
* **SQL with FireDAC.** Parameters with `:name` in the SQL text and `ParamByName('name').AsString := ...` (or `.AsInteger`, `.AsDate`). Other data-access libraries in the project have their own parameter mechanism; use it the same way. FireDAC macros (`&name`, `MacroByName(...).AsRaw`) are raw text substitution: never fill them from input.

```pascal
// insecure
Qry.SQL.Text := 'SELECT * FROM CLIENTES WHERE CPF = ''' + EdtCpf.Text + '''';
// safe
Qry.SQL.Text := 'SELECT * FROM CLIENTES WHERE CPF = :cpf';
Qry.ParamByName('cpf').AsString := EdtCpf.Text;
Qry.Open;
```
* **FMX (FireMonkey) apps** follow the same rules; on mobile, the HTTP client uses each OS's own stack, and secrets in the app package are extractable.
* **Code still on BDE (Borland Database Engine):** migrating to FireDAC is a staged task: one data module at a time, same SQL, compare results.
* **HTTPS and TLS.** `TNetHTTPClient` / `THTTPClient` (System.Net) use the operating system's HTTP stack (WinHTTP on Windows), so TLS 1.2+ follows a supported Windows with no DLLs to ship. Indy (`TIdHTTP` + `TIdSSLIOHandlerSocketOpenSSL`) needs OpenSSL DLLs and the classic handler only loads OpenSSL 1.0.2-era libraries, which no longer receive fixes; set `SSLOptions.SSLVersions := [sslvTLSv1_2]` explicitly, never rely on the default and plan a move to the OS client or to a maintained OpenSSL 3 handler for Indy. Never set a certificate-verification callback that always returns `True`.
* **NF-e in Delphi/Lazarus.** ACBr (Projeto ACBr, LGPL) is the common component set. In ACBr, A3 tokens need the WinCrypt setting; OpenSSL builds must match the app bitness (32-bit DLLs only load in a 32-bit `.exe`). Update ACBr from its official repository with a backup and a homologation-environment test before production.
* **DataSnap / REST servers.** If a server is exposed beyond the LAN: HTTPS only, authentication on every method, no method that runs SQL text sent by the client, generic errors (no exception text to the caller).
* **Secrets.** Connection strings in `.ini` beside the `.exe` are the classic leak. Protect with DPAPI or move to Windows authentication on the database server. Never compile a password into the `.exe`: strings are readable with any hex viewer.
* **Traps.** `Application.ProcessMessages` inside loops causes re-entrance bugs; `with` blocks hide which object a name belongs to; `FormatFloat`/`StrToFloat` depend on the Windows decimal separator (Brazilian `,` vs `.`): pass an explicit format setting for fiscal XML; string/`AnsiString` changes in Unicode Delphi break byte-oriented code (hashes, serial protocols, fiscal printers) when an old project is upgraded.

## Free Pascal, Lazarus, Turbo Pascal code
* **Run and build today.** Free Pascal (FPC) and the Lazarus IDE are free and open source (compiler GPL; runtime library under the "FPC modified LGPL", which allows static linking, so your `.exe` is not GPL). Lazarus ships with its own FPC build; use the pair from the same Lazarus release.
* **Delphi code** compiles in `{$mode delphi}`; **Turbo Pascal / Borland Pascal 7 code** in `{$mode tp}` (command line `-Mtp`). TP mode targets 32 or 64-bit, so DOS-specific code (direct `Mem[]`, `Port[]`, interrupt calls, `Crt` timing loops, BGI graphics) must be isolated and replaced, not compiled blindly.
* **SQL.** SQLdb (`TSQLQuery`) with `:name` parameters and `ParamByName`, exactly as in Delphi. ZeosLib the same.
* **HTTPS.** `fphttpclient` needs the `opensslsockets` unit (or `gnutlssockets`) in `uses`. Ship the OpenSSL version that the project's FPC release can load (FPC 3.2.2 may not load OpenSSL 3), from a trusted build. Test that a wrong host certificate is rejected: an FPC issue reported wrong host certificates accepted with validation on.
* **Traps.** Lazarus units default to `{$mode objfpc}` and the command-line compiler to `fpc` mode, both different from Delphi in strings and generics; set the mode at the top of each unit. Old TP code assumes 16-bit `Integer`: check record layouts written to binary files before changing the target.

## Clipper, Harbour, xHarbour
* **Run and build today.** CA-Clipper is 16-bit DOS and does not run on 64-bit Windows. The path is **Harbour** (free, GPL with a linking exception so your `.exe` is not GPL): last tagged stable is old, and the project ships current builds from the master branch (3.2 nightly). Build with `hbmk2` (one command: `hbmk2 app.hbp`). xHarbour is a separate fork; its sources were moved to GitHub by its maintainers. Pick one, and do not mix libraries between them.
* **Migrating Clipper to Harbour.** Usually recompiles with few changes. Watch: third-party Clipper LIBs (no Harbour version means a replacement), `.OBJ` in C or ASM, screen code written for 80x25 DOS, `SET DATE`/`SET EPOCH`, codepage of strings and indexes (select the same codepage the indexes were created with, or reindex), and printing to `LPT1` (map it or use a print library). Rebuild all indexes after the switch, on a copy first.
* **Data (RDD).** `DBFNTX` (`.ntx`, Clipper style, Harbour's default when none is set) and `DBFCDX` (`.cdx`, FoxPro-compatible) can read the same DBF; switching RDD changes index files, so keep the RDD the old system used until the migration step that changes it. Locking: every write between `RLOCK()`/`FLOCK()` and `DBUNLOCK()`, check the return value, never write without the lock.
* **SQL.** Harbour contribs `hbpgsql` (PostgreSQL), `hbmysql`, `hbodbc`, or `rddsql` with an SDD (`sddpg`, `sddmy`, `sddodbc`) to see SQL tables as work areas. SQLRDD was a commercial xHarbour product; its source was later published in the xHarbour repository and community ports exist for Harbour: confirm the license before shipping. Whatever the layer, build values with the library's quoting or parameter function, never by concatenating `GET` input into SQL text.
* **HTTPS / SEFAZ.** `hbssl` contrib links OpenSSL; `hbtip` (`TIPClientHTTP`) needs hbssl for `https`. Current OpenSSL 3 libraries have new file names (`libssl-3`, `libcrypto-3`); old tutorials pointing at `ssleay32`/`libeay32` describe OpenSSL 1.0 and are outdated. Many Harbour shops emit NF-e through an external component or vendor DLL instead.
* **Security traps.** `&` macro operator and `Eval()`/`&(cExpr)` on text typed by a user or read from a file is code injection: never macro-expand external input. Passwords in a `SENHAS.DBF` in clear or with a home-made XOR "cripto": hash them (see cross-cutting) and restrict the folder.

## Visual FoxPro
* **Status.** Microsoft ended extended support for VFP 9.0 on 2015-01-13; there is no supported compiler. The VFP 9 runtime still runs on current Windows in practice; keep the exact IDE version and service pack that built the `.exe`.
* **SQL pass-through.** `SQLEXEC(nHandle, "SELECT * FROM clientes WHERE cpf = ?lcCpf")` sends `?lcCpf` as a parameter. Concatenating `"... = '" + lcCpf + "'"` is injection. Same for remote views: parameterized views with `?variable`.

```foxpro
* insecure
SQLEXEC(lnH, "SELECT * FROM clientes WHERE cpf = '" + lcCpf + "'", "crs")
* safe
SQLEXEC(lnH, "SELECT * FROM clientes WHERE cpf = ?lcCpf", "crs")
```
* **Native DBC/DBF data.** Same share and backup rules as Clipper. `&` macro substitution or evaluating user text as an expression is code injection. Program and library files loaded from a folder all users can write let anyone replace code.
* **Traps.** String literals are limited to 255 characters in a command; build long SQL in pieces. Opening tables exclusively on a share locks everyone else out. Memo (`.fpt`) and index (`.cdx`) files must travel with the `.dbf` in every backup.
* **Migration.** Move data first: upsize tables to SQL Server or PostgreSQL and keep VFP as the front end through SQL pass-through, then replace screens one module at a time.

## Visual Basic 6
* **Status.** IDE unsupported since 2008-04-08 and not supported on 64-bit Windows; the runtime is supported for the lifetime of supported Windows versions listed in Microsoft's VB6 support statement, 32-bit only (WOW64), for serious regressions and critical security issues only. Third-party OCX are supported only by their vendors; some Microsoft OCX are on Microsoft's unsupported list.
* **SQL with ADO.** `ADODB.Command` with `?` placeholders, `CreateParameter` (name, type, direction, size, value) and `Parameters.Append`. Concatenating into `Recordset.Open "SELECT ... '" & txt.Text & "'"` is injection.

```vb
' insecure
rs.Open "SELECT * FROM Clientes WHERE Cpf = '" & txtCpf.Text & "'", cn
' safe
Set cmd = New ADODB.Command
Set cmd.ActiveConnection = cn
cmd.CommandText = "SELECT * FROM Clientes WHERE Cpf = ?"
cmd.Parameters.Append cmd.CreateParameter("cpf", adVarChar, adParamInput, 14, txtCpf.Text)
Set rs = cmd.Execute
```
* **Traps.** `On Error Resume Next` across a whole routine hides failed writes: scope it to one line and check `Err.Number`. Connection strings with `sa` in the `.exe` or `.ini`. For HTTPS, call SEFAZ through a component that uses WinHTTP on a supported Windows, or move that piece out to a small modern service first (good first strangler step).
* **Migration.** No automatic converter gives working code. Wrap business logic behind COM or a local service, replace screen by screen.

## COBOL
* **Run and build today.** GnuCOBOL (GNU project) is free: `cobc -x programa.cob` builds an executable. Pick the dialect matching the original compiler (`-std=ibm`, `-std=mvs`, `-std=mf`, `-std=acu`, `-std=rm` and others) so behaviour does not drift. IBM Enterprise COBOL for z/OS stays on the mainframe with its own lifecycle at IBM.
* **Embedded SQL.** Host variables with a colon: `EXEC SQL SELECT NOME INTO :WS-NOME FROM CLIENTE WHERE CPF = :WS-CPF END-EXEC`. Static SQL with host variables is safe by construction. Dynamic SQL: `PREPARE` a statement text with `?` markers, then `EXECUTE ... USING :var` or `OPEN cursor USING :var`; never `STRING` input into the statement text. On z/OS the Db2 coprocessor (compiler `SQL` option) or the precompiler handles `EXEC SQL`. GnuCOBOL has no built-in SQL: use the GixSQL preprocessor (PostgreSQL, ODBC, MySQL, Oracle, SQLite) or OCESQL, the project GixSQL grew from.
* **Checks.** Test `SQLCODE`/`SQLSTATE` after every statement; a negative code must stop the unit of work and `ROLLBACK`, not continue to the next record.
* **Traps.** `PIC` sizes and `COMP-3` packed decimals: a field that is too short truncates money silently; `ON SIZE ERROR` on arithmetic that touches money. File status codes after every `READ`/`WRITE`. EBCDIC vs ASCII when moving files off the mainframe changes sort order and packed fields: convert with a defined layout, never byte-for-byte.

## RPG on IBM i
* **Run and build today.** IBM i only; lifecycle at ibm.com/support/pages/ibm-i-release-support. New code in fully free-form RPG (`**FREE`), compiled as `SQLRPGLE` when it has SQL. Edit with IBM's tools or the open-source VS Code extension "Code for IBM i" (needs SSH on the IBM i); source in Git rather than only in source physical files.
* **SQL.** Static embedded SQL with host variables (`:cpf`) is safe. Dynamic SQL: build text with `?` parameter markers, `PREPARE`, then `EXECUTE ... USING :var` or `OPEN c1 USING :var` (a cursor for queries). Never concatenate input into the statement string.
* **Security.** Object authority on files and programs (public authority excluded on sensitive files), programs adopting authority only where needed, the security officer profile never used by applications. ODBC/JDBC access reaches every file the user profile can read, bypassing the green-screen menus: restrict it before opening ODBC to the network.
* **Traps.** Error handlers that do nothing; commitment control off, so a half-written order stays. Packed decimal overflow, as in COBOL.

## Progress OpenEdge ABL
* **Status.** Lifecycle at docs.progress.com (OpenEdge Life Cycle page); releases marked LTS get the long support windows. An application on a retired release is a finding.
* **Queries.** Static `FOR EACH ... WHERE field = variable` is safe. Dynamic queries (`QUERY-PREPARE` on a string) built from input are injectable; `QUOTER()` helps but was reported to be bypassable with encoded quotes, so validate input against an expected format (digits only for a code, a fixed list for a field name) before it enters the string, or keep the query static.
* **Traps.** An exclusive record lock held across a user prompt blocks other users; `NO-ERROR` without checking the error status afterwards hides failures. An AppServer exposed to the network: authentication and HTTPS.

## PowerBuilder
* **Status.** Appeon develops and sells current PowerBuilder; lifecycle on Appeon's site. Old Sybase/SAP versions are unsupported.
* **SQL.** Embedded SQL with host variables (`WHERE emp_id = :ll_id`) and DataWindows with retrieval arguments are parameterized. Dynamic SQL Format 2: `PREPARE SQLSA FROM "DELETE FROM employee WHERE emp_id = ?" ; EXECUTE SQLSA USING :ll_id ;`. Format 1 (`EXECUTE IMMEDIATE :ls_sql`) or changing a DataWindow's SQL at runtime with concatenated input is injection.
* **Traps.** Transaction-object passwords set in code or in a plain `.ini`; check `SQLCA.SQLCode` after every embedded statement.

## SAP ABAP
* **SQL.** Static Open SQL with host variables escaped by `@` (strict mode, 7.40 SP05+): `SELECT ... WHERE kunnr = @lv_kunnr`. Dynamic tokens (`WHERE (lv_cond)`, dynamic table or field lists) built from input are injectable: validate names with `cl_abap_dyn_prg=>check_column_name` (and its sibling checks), quote values with `cl_abap_dyn_prg=>quote`, or better, keep the SQL static. Native SQL (`EXEC SQL`) the same rule.
* **Authorization.** Every report, transaction and RFC function that reads or changes business data runs `AUTHORITY-CHECK OBJECT ... ID ... FIELD ...` and tests `sy-subrc` immediately (0 = allowed, anything else denies). A statement between the check and the test can overwrite `sy-subrc`. RFC-enabled function modules can be called without the transaction: give them their own `AUTHORITY-CHECK`.
* **Tooling.** SAP Code Vulnerability Analyzer runs security checks in ATC (separate license on-premise; ATC's standard checks are not). SonarSource also has ABAP rules for authority checks.
* **Traps.** Hard-coded user names (`IF sy-uname = 'JOAO'`) as authorization; OS commands built from input; changes transported to production without review.

## Staged migration (strangler pattern)
1. **Freeze and protect.** Backup routine tested by a restore, permissions fixed, passwords out of plain text, TLS for SEFAZ working. The system keeps running unchanged otherwise.
2. **Document behaviour from outputs.** Collect real inputs and outputs (orders, invoices, reports, fiscal XML) as golden files. These become the regression tests for every later step.
3. **Move data before screens.** DBF/VFP data into a real SQL server (PostgreSQL, SQL Server, Firebird), with the old system reading it through its SQL layer (FireDAC, rddsql, SQL pass-through, ADO). One table group at a time, with a way back.
4. **Carve one function out at a time.** Pick an edge with clear inputs (NF-e emission, price lookup, a report), build it as a new service or module, route that one function to it, compare outputs with the golden files, then switch. The old code for that function is removed only after the new one ran in production for an agreed period.
5. **Stop when it is enough.** A legacy core that is safe, backed up and isolated can keep running for years. Migration happens because of a real cost (no hardware, no compiler for the OS, a tax rule it cannot follow), not because the language is old.
