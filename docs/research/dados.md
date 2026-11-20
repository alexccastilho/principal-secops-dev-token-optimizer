# Evidence log: dados-e-ciencia.md

## Verified facts
- R: CVE-2024-27322, readRDS/load of crafted RDS or package ran code in R 1.4.0 to before 4.4.0; fixed in 4.4.0 (https://svn.r-project.org/R-dev-web/trunk/Blog2/content/post/2024-05-10-CVE-2024-27322.Rmd, source of the R blog statement, fetched; says use R code and data only from trusted sources, checked 2026-11-20)
- R: renv lockfile is always `renv.lock`; commit `renv.lock`, `.Rprofile`, `renv/settings.json`, `renv/activate.R`; `renv::snapshot()` and `renv::restore()` (https://rstudio.github.io/renv/articles/renv.html, checked 2026-11-20)
- R: renv function list includes init, status, snapshot, restore; no audit function (https://rstudio.github.io/renv/reference/index.html, checked 2026-11-20)
- R: tidyverse style guide supported by styler (restyles) and lintr (checks) (https://style.tidyverse.org/, checked 2026-11-20)
- R: `lintr::use_lintr(type = "tidyverse")`; lintr complementary to styler (https://lintr.r-lib.org/, checked 2026-11-20)
- R: DBI placeholders `?` (RMariaDB, RSQLite), `$1` (RPostgres, RSQLite); dbSendQuery + dbBind (https://dbi.r-dbi.org/reference/dbBind.html, checked 2026-11-20)
- R: dbGetQuery accepts `params` per DBI spec (https://dbi.r-dbi.org/reference/dbGetQuery.html, checked 2026-11-20)
- R: glue_sql quotes strings, backticks quote identifiers, `*` collapses; parameterized queries are safest (https://glue.tidyverse.org/reference/glue_sql.html, checked 2026-11-20)
- R: system2 args must be quoted, e.g. with shQuote, for special characters (https://stat.ethz.ch/R-manual/R-devel/library/base/html/system2.html, checked 2026-11-20)
- R: endoflife.date has no R product (404) (https://endoflife.date/api/v1/products/r/, checked 2026-11-20)
- Shiny: `HTML()` marks text so tag functions skip escaping (https://shiny.posit.co/r/reference/shiny/latest/html.html, checked 2026-11-20)
- Shiny: fileInput gives `name` (user's file name) and `datapath`; default upload limit 5 MB, `shiny.maxRequestSize` (https://mastering-shiny.org/action-transfer.html, checked 2026-11-20)
- Julia: backtick commands never run with a shell; interpolated value is one argument (https://docs.julialang.org/en/v1/manual/running-external-programs/, checked 2026-11-20)
- Julia: Serialization.deserialize does not validate data; format can change in 1.x releases (https://docs.julialang.org/en/v1/stdlib/Serialization/, checked 2026-11-20)
- Julia: stable and LTS lines published; juliaup is the recommended installer (https://julialang.org/downloads/, checked 2026-11-20)
- Julia: Project.toml with [deps] and [compat] (incl. julia); Manifest.toml exact state, not edited by hand (https://pkgdocs.julialang.org/v1/toml-files/, checked 2026-11-20)
- Julia: JuliaFormatter presets incl. BlueStyle, `.JuliaFormatter.toml`, `style = "blue"`; SciML guide suggests Runic.jl (https://domluna.github.io/JuliaFormatter.jl/dev/sciml_style, search-result excerpt, page not fetched, checked 2026-11-20)
- MATLAB: codeIssues introduced R2022b, recommended over checkcode; R2026b exists (https://www.mathworks.com/help/matlab/ref/codeissues.html, checked 2026-11-20)
- MATLAB: avoid eval; alternatives dynamic field names, str2func, feval (https://www.mathworks.com/help/matlab/matlab_prog/string-evaluation.html, checked 2026-11-20)
- MATLAB: `S = load(...)` returns a structure; load overwrites existing workspace variable (https://www.mathworks.com/help/matlab/ref/load.html, checked 2026-11-20)
- Octave: system runs a shell command, typically /bin/sh or cmd.exe (https://octave.sourceforge.io/octave/function/system.html and https://docs.octave.org/v8.1.0/Controlling-Subprocesses.html, search-result excerpt, page not fetched, checked 2026-11-20)
- Octave: release notes published as NEWS on octave.org (https://octave.org/download, checked 2026-11-20)
- Fortran: Fortran 2023, ISO/IEC 1539-1:2023, published November 2023, replaces Fortran 2018 (https://wg5-fortran.org/f2020.html, search-result excerpt, page not fetched, checked 2026-11-20)
- Fortran: gfortran -std= accepts f95, f2003, f2008, f2018, f2023, gnu, legacy; default gnu (https://gcc.gnu.org/onlinedocs/gfortran/Fortran-Dialect-Options.html, checked 2026-11-20)
- Fortran: -fcheck= keywords all, bounds, do, mem, pointer, recursion etc.; -finit-real=snan (https://gcc.gnu.org/onlinedocs/gfortran/Code-Gen-Options.html, checked 2026-11-20)
- Fortran: -ffpe-trap= invalid, zero, overflow, underflow, inexact, denormal; backtrace on unless -fno-backtrace (https://gcc.gnu.org/onlinedocs/gfortran/Debugging-Options.html, checked 2026-11-20)
- Fortran: ifort discontinued Oct 2024 (2025.0); ifx replacement, .o and .mod compatible, no 32-bit (https://www.intel.com/content/www/us/en/docs/fortran-compiler/get-started-guide/2025-0/overview.html, search-result excerpt, page not fetched, checked 2026-11-20)
- Fortran: flang-new renamed flang from LLVM 20.1.0 (https://blog.llvm.org/posts/2025-03-11-flang-new/, search-result excerpt, page not fetched, checked 2026-11-20)
- Fortran: fpm manifest `fpm.toml`; git deps with branch, tag, rev (https://fpm.fortran-lang.org/spec/manifest.html, checked 2026-11-20)
- Fortran: fortitude linter (Ruff-inspired); fprettify whitespace formatter (https://fortitude.readthedocs.io/ and https://pypi.org/project/fprettify/, search-result excerpt, page not fetched, checked 2026-11-20)
- SAS: NOXCMD disables PIPE/NAMEPIPE, CALL SYSTEM, X, DDE, %SYSEXEC, SYSTASK, FILENAME function; valid in config file or invocation (https://support.sas.com/documentation/cdl/en/hostwin/63285/HTML/default/win-sysop-xcmd.htm, checked 2026-11-20)
- SAS: %SUPERQ returns value without resolving macro references (https://support.sas.com/documentation/cdl/en/mcrolref/62978/HTML/default/p0ldeqll9sabzcn1jxnvid754b3t.htm, search-result excerpt, page not fetched, checked 2026-11-20)
- SAS: PROC PWENCODE prevents only casual viewing of passwords (https://support.sas.com/documentation/cdl/en/proc/65145/HTML/default/n0dc6in0v7nfain1f2whl6f5x66p.htm, search-result excerpt, page not fetched, checked 2026-11-20)
- Jupyter: token auth on by default; disabling token and password NOT RECOMMENDED; untrusted JS never executed, untrusted HTML sanitized; `jupyter trust` (https://jupyter-server.readthedocs.io/en/latest/operators/security.html, checked 2026-11-20)
- Jupyter: nbstripout `--install` Git filter, pre-commit hook id `nbstripout`, `--keep-output`, `--extra-keys` (https://github.com/kynan/nbstripout, checked 2026-11-20)
- pandas: read_pickle warns untrusted data unsafe (https://pandas.pydata.org/docs/reference/api/pandas.read_pickle.html, checked 2026-11-20)
- pandas: DataFrame.query can run arbitrary code with user input; `@var` syntax (https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html, checked 2026-11-20)
- pandas: 3.0.0 (Jan 21 2026): CoW only mode, chained assignment stops working, SettingWithCopyWarning removed, default str dtype, Python 3.11+, NumPy 1.26.0+, upgrade via 2.3 (https://pandas.pydata.org/docs/whatsnew/v3.0.0.html, checked 2026-11-20)
- Polars: read_csv schema_overrides, infer_schema_length, infer_schema (https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html, checked 2026-11-20)
- Polars: scan_csv returns LazyFrame, `.collect()` (https://docs.pola.rs/api/python/stable/reference/api/polars.scan_csv.html, checked 2026-11-20)
- DuckDB: enable_external_access, allowed_directories/allowed_paths (set before disabling access), lock_configuration, autoinstall/autoload_known_extensions, prepared statements; not a sandbox (https://duckdb.org/docs/2.0/operations_manual/securing_duckdb/overview.html, checked 2026-11-20)
- CSV injection: leading = + - @ tab CR LF, full-width variants; quote, prefix single quote, double inner quotes; Excel may strip on save (https://community.owasp.org/attacks/CSV_Injection, checked 2026-11-20)
- LGPD: Art. 5 II, III, XI; Art. 11; Art. 12 caput, §1, §2; Art. 13 §4 pseudonymization (https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm, checked 2026-11-20)
- MATLAB: system executes in a system shell (cmd on Windows, MATLAB_SHELL/SHELL or /bin/sh on UNIX) (https://www.mathworks.com/help/matlab/ref/system.html, checked 2026-11-20)
- Fortran: EXECUTE_COMMAND_LINE passes the command to the shell, sh or cmd.exe (https://gcc.gnu.org/onlinedocs/gfortran/EXECUTE_005fCOMMAND_005fLINE.html, checked 2026-11-20)
- pandas: to_sql if_exists='replace' drops the table before inserting (https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html, checked 2026-11-20)
- pandas: to_datetime dayfirst=True is not strict, only prefers day first (https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html, checked 2026-11-20)
- LGPD: Art. 5 II list written as examples (full list also includes union or religious/philosophical/political organisation membership) (https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm, checked 2026-11-20)

## Changed from the previous text
- New file. No previous reference covered R, Julia, MATLAB, Octave, Fortran, SAS, notebooks, pandas/Polars, analytics SQL, CSV injection or dataset anonymization. LGPD general rules stay in `security-baseline.md`; Python basics stay in `python.md`.

## Not verified
- ANPD Guia de Anonimização e Pseudonimização: consultation opened Jan 2024; final publication status not confirmed. Left out of the reference.
- SAS `&SYSVLONG` macro variable: not confirmed, replaced by "release printed at the top of the log".
- SAS missing-value ordering and log NOTE meaning: general knowledge, written without quoting log text.
- Shiny login: "not part of the core package" is general knowledge; no hosting product named.
- pandas 3.0 chained assignment: whatsnew says it "will stop working"; whether a warning is raised was not confirmed, so the reference says only that it no longer changes the frame.
- Julia current stable/LTS numbers, Octave current version, nbstripout version, Polars default `infer_schema_length` value: seen but deliberately not written as current facts.
- Octave package install behavior and MATLAB database parameter API: written without API names.
- Excel separator and encoding expectations by locale: not fetched; reference says only to check them.
- Exceptional-condition constructs for SAS and MATLAB: not verified, no bullet added.

## Lead additions (general knowledge, not fetched)
- CSV for pt-BR Excel: `;` separator because the comma is the decimal mark, UTF-8 with BOM (`utf-8-sig`) so accents open correctly, or deliver .xlsx. Added by the lead on 2026-11-20 from general knowledge; no URL fetched.
