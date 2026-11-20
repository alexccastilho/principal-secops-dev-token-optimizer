*Léelo en otros idiomas: [English](../CHANGELOG.md) · [Português (Brasil)](CHANGELOG.pt-BR.md)*

# Registro de cambios

Todos los cambios relevantes de este proyecto. El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y las versiones siguen [SemVer](https://semver.org/lang/es/).

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
- El SKILL.md creció de 15.665 a 19.240 bytes por las secciones 9 y 10. Los detalles están en las referencias, que se cargan solo cuando la tarea las necesita.
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
