# Research log: legado.md

## Verified facts
- Delphi: Community Edition is free; individuals and companies may use it under US$5,000/year revenue; companies must move to Professional at US$5,000 revenue or more than five developers; current CE is Delphi 13 Florence (https://www.embarcadero.com/products/delphi/starter, checked 2026-11-20)
- Delphi: FireDAC parameters use `:name` markers and `ParamByName(...).AsString`; macros `&name` with `MacroByName(...).AsRaw` substitute raw text (https://docwiki.embarcadero.com/RADStudio/en/Executing_Commands_(FireDAC), https://docwiki.embarcadero.com/RADStudio/Rio/en/Preprocessing_Command_Text_(FireDAC), checked 2026-11-20)
- Delphi: THTTPClient/TNetHTTPClient use native OS APIs (WinHTTP on Windows), not Indy/OpenSSL; libcurl is default on Linux (https://docwiki.embarcadero.com/Libraries/Athens/en/System.Net.HttpClient.Curl, https://blog.marcocantu.com/blog/2018-january-http-improvements-1022.html, checked 2026-11-20)
- Delphi/Indy: TIdSSLIOHandlerSocketOpenSSL supports OpenSSL 1.0.2 and earlier only; default TLS 1.0; set `SSLOptions.SSLVersions := [sslvTLSv1_2]`; OpenSSL 3 support only via PR #529 / third-party handlers (https://www.github.com/IndySockets/Indy/pull/529, https://atozed.com/forums/thread-2697.html, https://docwiki.embarcadero.com/RADStudio/en/Securing_Indy_Network_Connections, checked 2026-11-20)
- ACBr: Delphi/Lazarus component palette, LGPL; A3 certificates only via WinCrypt; OpenSSL DLL bitness must match the app (https://sourceforge.net/projects/acbr/, https://www.projetoacbr.com.br/forum/tags/wincrypt/, checked 2026-11-20)
- Free Pascal: current stable listed is 3.2.2 (https://www.freepascal.org/, checked 2026-11-20)
- Lazarus: current stable 4.8 built with FPC 3.2.2; 5.0 RC1 announced 2026-10-16 (https://www.lazarus-ide.org/, checked 2026-11-20)
- Free Pascal: compiler GPL, RTL "FPC modified LGPL" allowing static linking (https://wiki.lazarus.freepascal.org/licensing, checked 2026-11-20)
- Free Pascal: `{$mode tp}` / `-Mtp` for Turbo Pascal 7 compatibility; TP mode compiles 32/64-bit only (https://wiki.lazarus.freepascal.org/Mode_TP, https://freepascal.org/daily/doc/user/userse33.html, checked 2026-11-20)
- Harbour: free/open source, usable for nonfree products; latest tagged stable 3.0.0 (2011-07-17), nightly builds from master; build tool hbmk2 (https://harbour.github.io/, checked 2026-11-20)
- Harbour: contribs hbpgsql, hbmysql, hbodbc; rddsql with sddpg, sddmy, sddodbc (https://groups.google.com/g/harbour-users/c/hqDDiRyOcBA, https://gitea.com/pblsnchz/harbour/src/, checked 2026-11-20)
- Harbour: hbssl links OpenSSL; hbtip TIPClientHTTP needs hbssl for https; OpenSSL 3 libs named libssl-3/libcrypto-3; Oct 2025 upstream moved away from ssleay32/libeay32 (https://fivetechsoft.github.io/forums/topic-24992.html, https://groups.google.com/g/harbour-users/c/ude3nAGxonA, https://groups.google.com/g/harbour-devel/c/Fs3W5ihna78, checked 2026-11-20)
- xHarbour/SQLRDD: xHarbour sources moved to GitHub 2023; SQLRDD source released into xHarbour repo; license not stated; sqlrddpp port for Harbour (https://github.com/xHarbour-org/xharbour/blob/main/README.md, https://groups.google.com/g/harbour-users/c/eMj701B2A_k, https://www.github.com/marcosgambeta/sqlrddpp, checked 2026-11-20)
- VFP: VFP 9.0 support ended 2015-01-13 (https://learn.microsoft.com/en-us/lifecycle/end-of-support/end-of-support-2015, checked 2026-11-20)
- VFP: SQLEXEC parameters with `?variable`; 255-char string literal limit (https://learn.microsoft.com/en-us/previous-versions/xc123bb1(v=vs.90), checked 2026-11-20)
- VB6: IDE unsupported since 2008-04-08; runtime supported for lifetime of supported Windows (Win10/11, Server 2008 R2 to 2025), 32-bit WOW only, limited to serious regressions and critical security issues (https://learn.microsoft.com/en-us/previous-versions/visualstudio/visual-basic-6/visual-basic-6-support-policy, checked 2026-11-20)
- ADO: CreateParameter(Name, Type, Direction, Size, Value) does not auto-append; use Parameters.Append; `?` placeholders (https://learn.microsoft.com/en-us/archive/blogs/neilcar/sql-injection-mitigation-using-parameterized-queries-part-2-types-and-recordsets, checked 2026-11-20)
- Windows DPAPI: CryptProtectData, per user by default, machine scope by flag (https://learn.microsoft.com/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata, checked 2026-11-20)
- GnuCOBOL: 3.2 released 2023-07-28 (https://lists.gnu.org/archive/html/info-gnu/2023-07/msg00007.html, checked 2026-11-20)
- GnuCOBOL: `cobc -x` builds executable; `-std=` dialects include ibm, mvs, mf, acu, rm and strict variants (https://www.mankier.com/1/cobc, checked 2026-11-20)
- GixSQL: ESQL preprocessor for GnuCOBOL (PostgreSQL, ODBC, MySQL, Oracle, SQLite), derived from OCESQL (https://github.com/OcamlPro/gixsql, https://codeberg.org/GnuCOBOL/gixsql/releases, checked 2026-11-20)
- IBM Enterprise COBOL: Db2 coprocessor processes EXEC SQL with host variables at compile time (SQL option) (https://www.ibm.com/docs/en/SS6SG3_6.4.0/pg/concepts/cpdb203.html, checked 2026-11-20)
- IBM i: release support page; 7.4 standard support ends 2026-09-30 (https://www.ibm.com/support/pages/ibm-i-release-support, checked 2026-11-20)
- IBM i: dynamic SQL uses parameter markers with EXECUTE/OPEN USING; SELECT INTO cannot be prepared (https://archive.midrange.com/rpg400-l/202509/msg00024.html, https://archive.midrange.com/rpg400-l/201409/msg00161.html, checked 2026-11-20)
- Code for IBM i: open-source VS Code extension, needs SSH daemon on IBM i (https://codefori.github.io/docs/, checked 2026-11-20)
- OpenEdge: lifecycle page; LTS releases (https://docs.progress.com/bundle/openedge-life-cycle/page/OpenEdge-Life-Cycle.html, checked 2026-11-20)
- OpenEdge: QUOTER intended for QUERY-PREPARE WHERE clauses; 2012 community report of bypass with encoded quote (https://docs.progress.com/bundle/abl-reference/page/QUOTER-function.html, https://community-archive.progress.com/forums/00019/02434.html, checked 2026-11-20)
- PowerBuilder: Dynamic SQL Format 2 `PREPARE SQLSA FROM "...?"` + `EXECUTE SQLSA USING :var` (https://docs.appeon.com/pb2019/powerscript_reference/ch08s02.html, checked 2026-11-20)
- ABAP: `@` host variable escape and strict mode from 7.40 SP05 (https://help.sap.com/http.svc/rc/abapdocu_750_index_htm/7.50/en-US/abenopen_sql_host_variables.htm, checked 2026-11-20)
- ABAP: dynamic WHERE protected with cl_abap_dyn_prg=>check_column_name and quote (https://eduardocopat.github.io/abap-docs/7.54/abensql_inj_dyn_tokens_scrty, checked 2026-11-20)
- ABAP: AUTHORITY-CHECK OBJECT ... ID ... FIELD; sy-subrc 0 only if all authorized; check immediately (https://eduardocopat.github.io/abap-docs/7.54/abapauthority-check, https://rules.sonarsource.com/abap/RSPEC-5117, checked 2026-11-20)
- ABAP: Code Vulnerability Analyzer needs separate license on-premise; ATC standard checks do not (https://blogs.sap.com/2020/12/08/sap-code-vulnerability-analyzer-cva-faqs/, checked 2026-11-20)
- NF-e/SEFAZ: TLS 1.2 mandatory with NF-e 4.00; states disabled obsolete protocols (https://goias.gov.br/economia/problemas-com-protocolo-tls-1-2-e-incompatibilidadesdes-na-nf-e-4-00/, https://www.sefaz.pe.gov.br/Noticias/Paginas/NFE---Desativa%C3%A7%C3%A3o-dos-protocolos-de-seguran%C3%A7a-obsoletos.aspx, checked 2026-11-20)
- SMB oplocks/leasing and file databases: vendor guidance links corruption to client caching; Microsoft guidance differs by version (https://learn.microsoft.com/windows/desktop/FileIO/opportunistic-locks, https://support.tibco.com/external/article/80871/disabling-leasing-mode-to-prevent-corrup.html, checked 2026-11-20)

- Free Pascal: command-line default is FPC mode; Lazarus units default to ObjFPC (https://wiki.lazarus.freepascal.org/Mode_FPC, https://wiki.lazarus.freepascal.org/Mode_ObjFPC, checked 2026-11-20)
- Free Pascal: HTTPS in TFPHTTPClient needs opensslsockets or gnutlssockets in uses (https://www.freepascal.org/daily/doc/fcl/fphttpclient/fphttpclienthttps.html, checked 2026-11-20)
- Free Pascal: issue reports FPHTTPClient with OpenSSL accepting wrong host certificates with validation on (https://gitlab.com/freepascal.org/fpc/source/-/issues/40479, checked 2026-11-20)
- Harbour: DBFNTX is the default RDD when none is specified; DBFCDX compound index; RLOCK/FLOCK/DBUNLOCK (https://github-wiki-see.page/m/Petewg/harbour-core/wiki/dB/, https://www.linguagemclipper.com.br/harbour/index.html, checked 2026-11-20)
- PowerBuilder: Format 1 is EXECUTE IMMEDIATE; check SQLCode after each statement (https://docs.appeon.com/pb2019/powerscript_reference/ch08s02.html, checked 2026-11-20)

## Changed from the previous text
- New file; no previous text. Legacy stacks were not covered by any reference before.

## Not verified
- Exact SMB settings to disable oplocks/leasing on current Windows (left as "talk to the network owner").
- SQLRDD license.
- DataSnap current status vs RAD Server (written version-independent).
- PowerBuilder and Clipper lifecycle dates (pointed to vendor sites).
- QUOTER bypass status in current OpenEdge releases (worded as "reported").
- Whether Harbour master builds use OpenSSL 3 by default on all compilers.
- Whether FPC 3.2.2 loads OpenSSL 3 (forum reports only; worded as "may not").
- Indy default TLS version (Stack Overflow only; text now says "never rely on the default").
- Windows XP/Server 2003 lacking TLS 1.2 (vendor page only; removed from the text).
- "SELECT INTO cannot be prepared" on IBM i (mailing list only; removed).
- OpenEdge QUOTER bypass is a 2012 community report, kept as "reported".
- Removed as unverified: TADOQuery/IBX/Zeos/UniDAC specifics, BDE status, TFormatSettings, ACBrMonitor/ACBrLib, VFP EVALUATE/SET LIBRARY/SET EXCLUSIVE, RPG MONITOR/QSECOFR/exit programs, OpenEdge EXCLUSIVE-LOCK/ERROR-STATUS, PowerBuilder SetSQLSelect/DBPass/LogPass, ABAP CALL 'SYSTEM' and RFC start-check claim, VB6 Winsock/MSINET TLS claim.
