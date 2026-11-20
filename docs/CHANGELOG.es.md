*Léelo en otros idiomas: [English](../CHANGELOG.md) · [Português (Brasil)](CHANGELOG.pt-BR.md)*

# Registro de cambios

Todos los cambios relevantes de este proyecto. El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y las versiones siguen [SemVer](https://semver.org/lang/es/).

## [2.2.0] - 2026-11-20

Todas las referencias de lenguajes y bases de datos reescritas a partir de fuentes primarias actuales, cinco referencias nuevas, el mantenimiento de sistemas heredados como caso principal y un escáner que lee 151 tipos de archivo. Los datos que dependen de la versión se comprobaron en fuentes primarias el 2026-11-20; lo que no se pudo verificar se eliminó o se escribió sin versión. Los registros de evidencia en [docs/research/](research/) (en inglés) listan cada dato comprobado con su URL, y también lo que vino del texto anterior o del conocimiento general.

### Añadido
- `references/legado.md`: Delphi, Free Pascal/Lazarus, Pascal, Clipper/Harbour/xBase, Visual FoxPro, VB6, COBOL, RPG, OpenEdge, PowerBuilder y ABAP. La regla es "nunca reescribas un sistema heredado que funciona": copia de seguridad, seguridad donde está, migración por etapas.
- `references/scripts-e-automacao.md`: Lua (sandbox en 5.5 y Luau), Perl, VBA y macros de Office/Access, Google Apps Script, PowerShell 7 y 5.1, Bash/shell, `.bat`/`.cmd`, AutoHotkey y Tcl, con una sección común sobre ejecutar scripts con seguridad en Windows.
- `references/dados-e-ciencia.md`: R, Julia, MATLAB/Octave, Fortran, SAS, Jupyter, pandas/Polars, inyección de fórmulas en CSV/Excel y LGPD en conjuntos de datos.
- `references/sistemas-outros.md`: Zig, Ada/SPARK, Assembly, Objective-C, D y Nim.
- `references/bancos-nosql.md`: MongoDB, Redis/Valkey, Firebase, DynamoDB, Cassandra/ScyllaDB, Elasticsearch/OpenSearch, Neo4j, ClickHouse, InfluxDB/TimescaleDB y bases vectoriales con RAG (OWASP LLM01 y LLM08).
- `references/outras-linguagens.md` ahora cubre Swift, Dart/Flutter, Scala, Elixir/Erlang, Clojure, Haskell, OCaml, Groovy/Jenkins, Crystal, F# y VB.NET, además de Go, .NET, Ruby, Kotlin y móvil (OWASP MASVS).
- `references/bancos-outros.md` ahora cubre Firebird, Db2, DuckDB, CockroachDB, Access y DBF/Paradox, además de PostgreSQL, SQLite, SQL Server y Oracle.
- Escáner: 25 reglas nuevas (de 52 a 77) y 80 tipos de archivo nuevos (de 71 a 151), cada regla probada con una línea insegura y con la línea segura correspondiente. Novedades: SQL armado con `&`, `..`, `||`, interpolación o `Sprintf`/`format!`/`paste`; `FromSqlRaw` de EF Core; interpolación en Rails; SQL dinámico en COBOL/ABAP; filtro de MongoDB tomado de `req.body`; comandos del sistema armados con datos en 20 lenguajes; `Invoke-Expression`, `curl | bash`, `eval "$x"`; `load` de Lua, `&()` de Clipper, `read-string` de Clojure, `Eval.me` de Groovy; átomos y `binary_to_term` en BEAM; `BinaryFormatter` de .NET; `open` de dos argumentos en Perl; `expr` sin llaves en Tcl; `<?!=` en Apps Script; `trust` de PostgreSQL por la red; reglas abiertas de Firebase; verificación TLS desactivada en una docena de stacks; claves `sb_secret_` de Supabase; comprobaciones de seguridad de Zig/Ada desactivadas. Se respeta la sintaxis de comentarios de cada lenguaje (`--`, `'`, `!`, `;`, `rem`, `&&`).
- `tests/test_scanner_languages.py`: 83 pares inseguro/seguro y 8 casos comentados.
- Evals: de 28 a 35 escenarios (Delphi con Firebird, Clipper en una carpeta compartida, mods en Lua, VBA con la coma decimal de pt-BR, CSV para Excel, Redis y MongoDB en un VPS, `irm | iex` en PowerShell).
- `benchmark/`: scripts que ejecutan el mismo pedido de app en Claude Code con y sin la skill, en una configuración limpia, y miden tokens, tiempo, costo, líneas de código, compilación y hallazgos de seguridad (ver [BENCHMARK.es.md](BENCHMARK.es.md)).

### Cambiado
- Todas las referencias web actualizadas: PER Coding Style, funciones de PHP 8.5/8.6, bloqueo de paquetes con avisos en Composer, Laravel y Symfony; modelo de permisos de Node, type stripping, aprobación de install scripts en npm 12, Express 5, Next.js 16; funciones de Python 3.14/3.15, `pip lock`, CSP de Django 6; Java 25, Spring Boot 4 y Spring Security 7; Trusted Types, CSP estricta, WCAG 2.2 y la Ley Europea de Accesibilidad.
- `mysql.md`: ramas LTS e Innovation, fin del MySQL 8.0 (2026-04-30), `mysql_native_password` eliminado en 9.0, eliminaciones de 8.4 que rompen scripts, `unix_socket` y PARSEC en MariaDB.
- `security-baseline.md`: las contraseñas siguen NIST SP 800-63B-4 (15 caracteres cuando la contraseña es el único factor, sin reglas de composición, lista de bloqueo); OWASP Top 10 for Agentic Applications y CWE Top 25 2025 en el mapa de normas; bcrypt con costo 12 por defecto.
- `versoes-e-fontes.md`: 36 filas nuevas en la tabla de fuentes, cada una con el identificador de endoflife.date o la página del fabricante cuando no existe.
- `compliance-licencas.md`: fechas del CRA (11 de junio de 2026, 11 de septiembre de 2026, 11 de diciembre de 2027) y la cadena de notificación de 24 h / 72 h / un mes.
- `qt.md`: el Qt de código abierto recibe correcciones solo hasta la siguiente versión menor; el LTS largo es comercial. Reglas de QProcess reescritas para Qt 6.
- `gui-desktop.md`, `gui-outros.md`: obsolescencias de GTK 4.10, capabilities de Tauri 2, valores por defecto de Electron por versión, arrastrar y soltar en Avalonia 12, accesibilidad en egui.
- `c-cpp.md` y `rust.md` reescritos con flags de hardening, sanitizers y herramientas de cadena de suministro actuales.
- SKILL.md: enrutamiento de las referencias nuevas, reglas de emparejamiento para heredados y NoSQL, y una descripción que nombra los stacks nuevos (todavía por debajo de 1024 caracteres). La prueba de estilo ahora cubre el SKILL.md y todas las referencias.

## [2.1.0] - 2026-11-20

Estructura preventiva y modo refactorización, con ideas adaptadas de [`untangle-codebase` y `prune-tests`](https://github.com/caldoai/skills) (MIT, © 2026 Maze). El repositorio ahora tiene pruebas automatizadas, CI y documentación en inglés, portugués y español.

### Añadido
- **Estructura en el modo normal.** Sección 9 del SKILL.md: antes de escribir, la pregunta "¿qué tiene que cambiar junto con esto?"; nada de lógica o valores copiados, de acceder a los detalles internos de otro módulo, de wrappers que solo reenvían, ni de configuración para lo que nunca varía; "corrige la causa, no el caso" en lugar de un `if` para un solo valor, un `sleep`, un reintento o un `catch` vacío. En código existente la regla es "no lo empeores": rige lo que la skill escribe, nunca el código de alrededor. El código de seguridad nunca se trata como sobrante.
- `references/estrutura.md`: las reglas completas con ejemplos y las reglas para escribir pruebas que protegen el comportamiento (valor esperado literal, comprobar lo que ve quien usa el código, nunca simular lo que se está probando).
- **Modo refactorización, solo con pedido explícito.** Sección 10 del SKILL.md, `references/refatoracao-completa.md` y el comando `/secops-refatorar` del plugin. Exige Git con todo guardado y una rama propia, congela los contratos públicos, no actualiza dependencias, mantiene un registro de decisiones, vuelve a revisar hasta que no quede nada que valga la pena corregir y termina con un informe en pt-BR. Extras opcionales: comentarios y pruebas, con las pruebas de seguridad y de regresión siempre conservadas.
- Dos elementos nuevos en la lista de comprobación de entrega: ninguna lógica copiada ni import de algo más volátil, y ningún caso especial nuevo donde cabe una corrección en la causa.
- Evals: de 23 a 28 escenarios (costo de envío sin duplicar, descuento doble sin `if`, pedido vago que no inicia una refactorización, `/secops-refatorar`, prueba con valores literales).
- Suite de pruebas (`tests/`, solo biblioteca estándar): comportamiento del escáner, versiones coherentes, referencias enlazadas desde el SKILL.md, evals, traducciones, estilo de la documentación y contenido del ZIP.
- GitHub Actions: pruebas en Linux y Windows con Python 3.8 y el actual, el ZIP de claude.ai adjunto a cada ejecución, CodeQL y Dependabot para las actions.
- Documentación en tres idiomas (README, CHANGELOG y CONTRIBUTING en inglés, portugués y español), `SECURITY.md`, `CODE_OF_CONDUCT.md`, plantillas de issue y de pull request.
- `THIRD_PARTY_NOTICES.md` dentro de la carpeta de la skill, con el crédito y la licencia MIT de caldoai/skills. Va incluido en el ZIP.

### Cambiado
- Prioridad en caso de conflicto: Seguridad > Integridad > Claridad > **Estructura** > Ahorro de tokens > Estilo.
- `projeto-do-zero.md`: el esqueleto estándar organiza `src/` por funcionalidad, con `comum/` solo para lo que usan dos o más funcionalidades.
- `diagnostico.md`: "corrección mínima" significa menos líneas en la causa, no un parche sobre el síntoma.
- Descripción de la skill: ahora menciona estructura de código, pruebas y "reorganize o projeto", dentro del límite de 1024 caracteres.
- El SKILL.md creció de 15.665 a 19.634 bytes por las secciones 9 y 10. Los detalles están en las referencias, que se cargan solo cuando la tarea las necesita.
- `tools/build_zip.py` acepta la carpeta de salida como argumento.
- El README principal pasó a estar en inglés, con versiones en portugués y español en `docs/`.

## [2.0.2] - 2026-11-16

### Añadido
- Icono del plugin (`.claude-plugin/icon.png`, 1024x1024): un escudo con el símbolo de código. El generador es `tools/make_icon.py`.

## [2.0.1] - 2026-11-16

### Cambiado
- Sección 7 del SKILL.md: la instrucción de la ruta del escáner sigue teniendo sentido después de que Claude Code sustituye `${CLAUDE_SKILL_DIR}`. Probado en los dos escenarios (ruta sustituida y marcador literal en claude.ai).
- Informe de revisión actualizado con los ajustes de empaquetado.

## [2.0.0] - 2026-11-16

Revisión profunda de la skill. El informe completo, con hallazgos por gravedad y la validación realizada, está en [docs/ANALISE-v2.0.0.md](ANALISE-v2.0.0.md) (en portugués).

### Corregido
- Escáner: un secreto podía filtrarse en la salida cuando la misma línea también activaba otra regla. Ahora el fragmento se oculta en toda la línea.
- Escáner: las claves privadas PEM nunca se detectaban, y los archivos `.pem` y `.key` no se leían.
- Escáner: falsos HIGH en código correcto (`sprintf` en PHP, `prepare()->execute([...])`, `{$wpdb->prefix}`, concatenación de texto común).
- Escáner: ya no se cae con `UnicodeEncodeError` en la consola de Windows y lee archivos UTF-16. Una carpeta superior llamada `build` o `dist` ya no vacía el análisis, y una ruta inexistente devuelve el código de salida 2.
- `php.md`: el `.htaccess` ahora bloquea `/.git/` de verdad.
- SKILL.md: el límite de referencias ya no descarta el modelo de amenazas (`security-baseline.md`). La seguridad va antes que el ahorro de tokens.
- SKILL.md: se eliminó la contradicción entre "corrige todo HIGH" y "no toques nada fuera del pedido".

### Añadido
- El escáner detecta más secretos: `'password' => '...'`, `define('DB_PASSWORD', ...)`, `new PDO(..., "root", "senha")`, `mongodb+srv://`, tokens de GitHub, Stripe, Google y Mercado Pago.
- Cobertura de WordPress, pagos y Pix, Supabase y Firebase, CPF y CNPJ (incluido el CNPJ alfanumérico), cPanel/`public_html`, Kotlin, PowerShell y shell script.
- Evals: de 17 a 23 escenarios (inyección de instrucciones en un archivo, hallazgo crítico fuera del alcance, falso positivo, WordPress, Pix, Supabase).
- Empaquetado: plugin y marketplace de Claude Code, ZIP para claude.ai, `license` y `metadata` (autoría y versión) en el frontmatter.

### Cambiado
- La ruta del escáner se construye a partir de la carpeta de la skill (`${CLAUDE_SKILL_DIR}` en Claude Code), sin ruta fija.
- Las listas de comprobación de código nativo y de GUI pasaron del SKILL.md a `native-app-security.md` y `gui-desktop.md`. El SKILL.md quedó alrededor de un 6% más pequeño.
- El escáner funciona con Python 3.8+ y usa solo la biblioteca estándar.

## [1.0.0]

Versión original de la skill, creada por Alex Camacho Castilho.
