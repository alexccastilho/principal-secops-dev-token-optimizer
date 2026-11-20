# Benchmark: con y sin la skill

[English](BENCHMARK.md) · [Português](BENCHMARK.pt-BR.md)

Medido el 20/11/2026 con la versión 2.2.0 de la skill, Claude Code 2.1.329, el modelo `sonnet`, en Windows 11. Son 6 lenguajes × 2 condiciones × 3 repeticiones = 36 ejecuciones.

## Resumen

- **Seguridad:** en una revisión a ciegas, la app hecha con la skill fue la más segura en los 6 lenguajes. Ninguna condición produjo una vulnerabilidad de gravedad alta, y todas las apps usaron SQL parametrizado. La diferencia está en la segunda capa: hash de contraseña con costo actual, bloqueo de login que sobrevive a reiniciar el programa, mensajes de error genéricos e instrucciones de copia de seguridad y recuperación.
- **Costo:** con la skill, cada pedido salió cerca de 3 veces más caro y 2,5 veces más lento. Los promedios fueron USD 0,58 contra 0,20 por app, y 176 s contra 69 s. La skill también escribió cerca del doble de código.
- **Funcionar tal como se entrega:** sin la skill compilaron 18 de 18 apps. Con la skill compilaron 16 de 18, y una app en PHP no podía crear su primer usuario.

Para una app pequeña hecha desde cero, la skill cambia tokens y tiempo por un resultado más seguro y mejor documentado. El ahorro de tokens del nombre de la skill viene de sus reglas de lectura, respuesta y refactorización: no repetir, no pegar archivos enteros, leer una sección en lugar del archivo completo. Este benchmark no mide ese ahorro; mide una app completa por ejecución.

## El pedido

El mismo texto, en portugués, en todas las ejecuciones. `{lang}` fue PHP, Python, JavaScript con Node.js, Java, C# con .NET o Go:

> Preciso de um sistema simples em {lang} para cadastrar meus contatos (nome, e-mail e telefone), com login de usuário e senha, salvando num banco SQLite. Vai rodar só no meu computador com Windows, é tudo do zero, só eu vou usar, e guarda dado pessoal (nome, e-mail e telefone). Crie os arquivos nesta pasta e me diga como rodar. Não sou programador.

(Traducción: "Necesito un sistema simple en {lang} para registrar mis contactos (nombre, correo y teléfono), con login de usuario y contraseña, guardando en una base SQLite. Va a correr solo en mi computadora con Windows, es todo desde cero, solo yo lo voy a usar y guarda datos personales. Crea los archivos en esta carpeta y dime cómo ejecutarlo. No soy programador.")

Las preguntas que la skill suele hacer antes de un proyecto nuevo ya están respondidas en el texto. Así las dos condiciones pueden entregar en un solo turno, sin interacción.

## Resultados por lenguaje

Promedios de 3 ejecuciones. "Líneas de código" cuenta las líneas de código fuente sin líneas en blanco ni comentarios.

| Lenguaje | Tiempo (s) sin / con | Tokens de salida sin / con | Costo (USD) sin / con | Líneas de código sin / con | Compiló sin / con |
|---|---|---|---|---|---|
| PHP | 62 / 155 | 10.195 / 22.218 | 0,18 / 0,48 | 303 / 483 | 3/3 / 3/3 |
| Python | 44 / 171 | 6.575 / 23.962 | 0,13 / 0,56 | 198 / 544 | 3/3 / 3/3 |
| Node.js | 63 / 172 | 9.778 / 25.715 | 0,18 / 0,56 | 209 / 597 | 3/3 / 3/3 |
| Java | 93 / 165 | 14.920 / 24.824 | 0,25 / 0,56 | 404 / 624 | 3/3 / 2/3 |
| C# | 60 / 201 | 10.620 / 29.748 | 0,19 / 0,65 | 249 / 678 | 3/3 / 3/3 |
| Go | 93 / 193 | 15.052 / 30.584 | 0,25 / 0,64 | 490 / 767 | 3/3 / 2/3 |
| **Promedio** | **69 / 176** | **11.190 / 26.175** | **0,20 / 0,58** | **309 / 616** | **18/18 / 16/18** |

El total de tokens de entrada (contando lecturas de caché) promedió 141 mil sin la skill y 734 mil con ella; los turnos de conversación, 10 y 34. La skill lee su archivo de enrutamiento y de tres a cinco referencias antes de escribir, y escribe más archivos (15 en promedio, contra 5).

Las dos fallas de compilación con la skill: una ejecución en Go no creó el `go.mod`, y una en Java usó una clase del driver de SQLite sin importarla.

## Seguridad

**Chequeos estáticos.** El escáner de la propia skill (`revisar_codigo.py`) solo encontró hallazgos HIGH en Node.js: en promedio 0,7 por app sin la skill y 0,3 con ella. Semgrep (`p/default`, versión 1.186) encontró cantidades parecidas en las dos condiciones, casi todas advertencias en handlers web de Go.

**Revisión a ciegas.** En la repetición 1 de cada lenguaje, dos agentes revisores recibieron el par como `A` y `B`, en orden aleatorio, y puntuaron 10 criterios de 0 a 2 leyendo el código. Las notas completas, con los defectos encontrados en cada lado, están en [benchmark/results/blind_review.md](../benchmark/results/blind_review.md).

| Lenguaje | Sin skill | Con skill |
|---|---|---|
| PHP | 18/20 (seguridad 14/16) | 16/20 (seguridad 16/16) |
| Python | 10/14 | 14/14 |
| Node.js | 17/20 | 18/20 |
| Java | 12/14 | 14/14 |
| C# | 10/14 | 13/14 |
| Go | 19/20 | 20/20 |

Las apps de escritorio y de consola valen 14 puntos, porque sesión, CSRF y XSS no se aplican a ellas. PHP con la skill tuvo una nota general menor porque no funciona tal como se entrega: su lanzador llama a un script que nunca se escribió.

**Chequeos de entrega** en las 18 apps de cada condición (chequeo de archivos y palabras clave, no una revisión):

| Chequeo | Sin skill | Con skill |
|---|---|---|
| README o instrucciones de uso | 6/18 | 18/18 |
| `.gitignore` | 0/18 | 17/18 |
| Pruebas automatizadas | 0/18 | 3/18 |
| Hash de contraseña fuerte (Argon2id, bcrypt, scrypt o PBKDF2) | 18/18 | 18/18 |
| Límite de intentos de login | 18/18 | 18/18 |

## Método

- **Aislamiento.** Cada ejecución usa su propio `CLAUDE_CONFIG_DIR`, con solo una copia del login, `--strict-mcp-config` y ningún plugin. La excepción es la condición con skill, que recibe `--plugin-dir` apuntando a este repositorio. `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` impide que las skills subidas a claude.ai se sincronicen en la ejecución. Sin eso, una copia antigua de esta skill, venida de la cuenta, se cargaba en la condición "sin skill". La primera ronda completa quedó contaminada así y se descartó. `run.json` registra las skills vistas y llamadas, y `analyze.py` marca cualquier ejecución sin skill que haya llamado a la skill. Ninguna lo hizo en la ronda publicada.
- **Rutas cortas de Windows.** Claude Code pide aprobación antes de escribir en una ruta con `~` (por ejemplo `C:\Users\NOMBRE~1`), y una ejecución sin interacción nunca puede darla. El script expande los nombres cortos; una ronda anterior a esa corrección dejó vacías las carpetas de Node.js con la skill.
- **Permisos.** Las dos condiciones tuvieron la misma lista de herramientas: archivos, búsqueda web, lectura de páginas, el intérprete de Python y los chequeos de versión y sintaxis de cada lenguaje. Instalar paquetes no estaba permitido, para que el chequeo de compilación siga siendo comparable. Los números de arriba se midieron en el commit `b723084`, cuya lista también permitía `curl` y leer cualquier página. El script actual limita la red a las fuentes de versión y pasa un entorno filtrado.
- **Chequeo de compilación.** Corre después de la sesión, sobre los archivos que dejó: `php -l`, `python -m compileall`, `node --check`, `mvn package` (o `javac` cuando no hay `pom.xml`), `dotnet build` y `go mod tidy && go build`. La etapa de análisis descarga las dependencias declaradas; la sesión no podía. Herramientas: PHP 8.5.12, Go 1.27.4, .NET SDK 10.0.404, Temurin JDK 25.0.5 y Maven 3.9.16.
- **Límites.** Tres repeticiones por celda es una muestra pequeña: el tiempo y los tokens varían hasta 2 veces entre repeticiones de la misma celda. Es un pedido, un modelo y una máquina. La revisión a ciegas cubre una repetición por lenguaje y la hicieron modelos, no personas. Las líneas de código miden tamaño, no calidad.

## Cómo reproducir

Ejecutar el benchmark gasta tokens reales en la cuenta cuyo login copies: cerca de USD 14 en las 36 ejecuciones, a los precios de la fecha de arriba. Ejecútalo en una máquina virtual o sandbox: los intérpretes siguen permitidos para probar las apps generadas, y pueden abrir conexiones de red.

```
# 1. configuración limpia, solo con el login
mkdir cfg && cp ~/.claude/.credentials.json cfg/

# 2. ejecuciones (fuera del repositorio; en Windows, en una ruta sin "~")
python benchmark/run_benchmark.py --config-dir cfg --out ../bench --reps 3 --jobs 3

# 3. análisis (necesita en el PATH las herramientas de los lenguajes medidos y semgrep)
python benchmark/analyze.py --runs ../bench --results benchmark/results

# 4. borra la copia del login
rm cfg/.credentials.json
```

`benchmark/results/` guarda la ronda publicada: `runs.json` (una entrada por ejecución), `summary.json` (promedios por lenguaje y condición), `quality.json` (chequeos de entrega) y `blind_review.md`.
