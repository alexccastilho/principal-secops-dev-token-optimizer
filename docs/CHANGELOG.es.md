*Léelo en otros idiomas: [English](../CHANGELOG.md) · [Português (Brasil)](CHANGELOG.pt-BR.md)*

# Registro de cambios

Todos los cambios relevantes de este proyecto. El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y las versiones siguen [SemVer](https://semver.org/lang/es/).

## [2.3.1] - 2026-11-27

Correcciones de una auditoría externa de la 2.3.0. Cada una tiene una prueba que fallaba antes de la corrección.

### Corregido
- Escáner: la regla de Android para tráfico sin cifrado (`usesCleartextTraffic="true"`, `cleartextTrafficPermitted="true"`) nunca se activaba, porque el archivo tenía un carácter de control invisible (backspace, 0x08) en lugar de `\b`. Una prueba ahora rechaza caracteres de control en todo archivo Python del repositorio.
- Escáner: los archivos `.gvy` y `.jenkinsfile` quedaban fuera al analizar una carpeta.
- Escáner: una regla que existe una vez por lenguaje (`shell-montado`, `codigo-dinamico`) imprimía en el informe de texto la corrección de un lenguaje para todos; un hallazgo de Clipper venía con la corrección de Lua. Cada corrección tiene ahora su propio grupo.
- Escáner: una contraseña corta solo con letras minúsculas (`password = "minhasenha"`, `"adminadmin"`) se tomaba por una etiqueta de pantalla y no se señalaba. Una etiqueta empieza con mayúscula o termina en puntuación; las contraseñas desechables de las pruebas automatizadas siguen sin aviso. En las apps del benchmark el cambio no agregó ningún hallazgo fuera de archivos de prueba.
- `--entrega`: una frase como `"copy from 'somewhere'"` dentro de un texto, o un import en un comentario, se tomaba por un paquete faltante y reprobaba la puerta. Los archivos `.jsx`, `.tsx`, `.mts` y `.cts` no se verificaban. Un import de Python dentro de un docstring contaba. En Python 3.8 y 3.9 la verificación de Python se saltaba sin aviso. `--entrega` sobre un archivo suelto pasaba con salida 0; ahora pide la carpeta del proyecto y sale con 2.
- Texto de `--entrega` en `SKILL.md`: verifica que `package.json` liste todo paquete que importa el código Node.js; para Python, Go, C# y PHP solo verifica que el manifiesto exista. El texto de la 2.3.0 decía que todo manifiesto se comparaba con los imports.
- `fontes.py`: una versión preliminar (`1.2.3-rc1`) contaba como más nueva que la versión final, lo que podía ocultar la versión corregida; la fecha del caché vencido más antiguo se comparaba como texto (`01/12` antes de `25/11`); un CVE que es el propio id del registro, y no un alias, quedaba sin la marca del KEV de la CISA; los módulos dentro de los bloques `exclude (...)` y `replace (...)` de `go.mod` se enviaban a OSV como dependencias.
- Benchmark: las pruebas originales de Node.js en la suite de refactorización se ejecutaban con `node --test tests/`, que falla en Node 22 y posteriores, así que las seis filas de Node.js mostraban 0/3. El costo en los resúmenes de app nueva tenía un decimal, y C# quedaba como compilación fallida cuando la máquina tenía el runtime de .NET pero no el SDK. Los resúmenes de la 2.3.0 se recalcularon a partir de las mismas ejecuciones, sin llamar de nuevo al modelo: Node.js 3/3, costo con tres decimales, C# 0/0 (no verificado). La segunda ronda de app nueva, que muestra la tabla del benchmark, está ahora en `custos2.json`. `ativacao.txt` estaba en CP1252 y ahora está en UTF-8.

### Cambiado
- Las descripciones del plugin y del marketplace ya no prometen ahorro de tokens.
- `references/projeto-do-zero.md` apunta a `padrao-de-entrega.md`, al lanzador de doble clic y a `--entrega`; `references/security-baseline.md` apunta a `fontes.py`.
- README: el código de salida 1 también cubre `--entrega` reprobado, y el escáner lee 153 tipos de archivo. El benchmark registra que las puertas 2 y 4 fueron aceptadas, y la versión en español recibió los tres pasajes que le faltaban.

## [2.3.0] - 2026-11-25

Datos consultados en el momento en vez de escritos, y código que funciona tal como se entrega.

### Añadido
- `scripts/fontes.py`: lee en el momento de uso el estado de soporte de una versión (endoflife.date) y las fallas conocidas de las dependencias fijadas del proyecto (OSV), y marca las que están en la lista de explotadas activamente de la CISA (KEV). El registro `fontes/registro.json` guarda solo direcciones, nunca datos con fecha, así que una nueva versión de PHP o un CVE nuevo no exige una nueva versión de la skill. Lista fija de hosts, solo HTTPS, caché fuera de la skill y del proyecto, `SECOPS_OFFLINE=1` para apagar la red, y "no verificado" en vez de una suposición cuando la fuente no responde. Solo se envían a OSV los paquetes que provienen comprobadamente del registro público; en Go, un módulo privado fuera de la ruta del propio proyecto necesita estar en `GOPRIVATE`.
- `revisar_codigo.py --entrega`: verifica, sin ejecutar nada, que todo archivo citado en un lanzador, en el README o en `package.json` exista, y que el manifiesto del lenguaje esté presente y liste los paquetes que el código importa. Cada verificación reproduce una falla medida en el benchmark de la 2.2.0.
- `references/padrao-de-entrega.md`: qué significa "listo" para código, esquemas y migraciones de base de datos, API, pruebas y operación, aplicado en proporción al pedido.
- Un canario semanal en CI (`.github/workflows/fontes-canario.yml`) que abre un issue cuando una fuente deja de responder con los campos que el script lee.

### Cambiado
- `SKILL.md`: la puerta previa a la entrega ahora empieza por "funciona tal como se entrega" (compilar una vez, camino feliz, `--entrega`); secciones nuevas sobre trabajar junto con skills de planificación, TDD, depuración y revisión de diff (sección 11) y sobre entrega proporcional con menos turnos (sección 12). La descripción ahora empieza con "cargar antes de la primera edición de cualquier archivo de código, incluso en una corrección de una línea": en la medición de la 2.2.1 la skill nunca se llamó para corregir un error en un proyecto existente (0 de 6), crear un campo, crear una tabla, actualizar dependencias o escribir pruebas (0 de 4 cada uno). El texto se eligió en un piloto pequeño en la tarea de corrección de errores (4 de 4 contra 0 de 4 del primer borrador), antes de la ronda completa.
- La documentación ya no promete ahorro de tokens: el gasto se mide en el benchmark.
- Una app nueva para quien no programa siempre trae un lanzador de doble clic y los requisitos con su enlace; pruebas, scripts de respaldo y herramientas de administración solo cuando se piden o cuando el riesgo lo exige.

### Medido
- Benchmark parcial contra la 2.2.1 y sin la skill, en Python, Node.js y C#: [BENCHMARK-2.3.es.md](BENCHMARK-2.3.es.md). Con la skill funcionando en ambas, la 2.3.0 no fue más cara por app nueva ni por revisión, y una corrección pequeña cuesta USD 0,04 más porque ahora la skill se carga; en las revisiones a ciegas sus apps fueron igual de seguras o más y más fáciles de ejecutar, y sus revisiones no hicieron afirmaciones falsas. El C# no se pudo compilar en la máquina de prueba.

## [2.2.1] - 2026-11-20

### Cambiado
- La descripción de la skill ahora menciona primero la revisión y la corrección de código existente, con los pedidos que los dueños de proyectos escriben de verdad ("revise o código", "tem algum problema?", "corrija isso", "não está calculando certo"). En el [benchmark de refactorización](BENCHMARK-REFACTOR.es.md), la skill estaba instalada pero no se llamó en ninguna revisión ni corrección (0 de 12 ejecuciones), mientras que el pedido de refactorizar el proyecto entero la llamó todas las veces. Para caber en el límite de 1.024 caracteres, la lista de cobertura perdió "archives", "drag and drop" y "visual design", que las referencias siguen cubriendo. Todavía no se midió si la nueva descripción resuelve la activación.

### Agregado
- Benchmark de refactorización (`benchmark/refactor/`, `benchmark/analyze_refactor.py`, `--suite refactor`): un proyecto de práctica de 2.700 líneas en Python y Node.js, con fallas plantadas, pruebas ocultas, respuestas esperadas y un validador que corre sin costo. La primera ronda es parcial y está publicada tal como salió en [BENCHMARK-REFACTOR.es.md](BENCHMARK-REFACTOR.es.md).

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
