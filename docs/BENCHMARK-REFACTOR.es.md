# Benchmark de refactorización (parcial): código existente, con y sin la skill

[English](BENCHMARK-REFACTOR.md) · [Português](BENCHMARK-REFACTOR.pt-BR.md) · [Primer benchmark: app nueva](BENCHMARK.es.md)

Ejecutado el 20/11/2026 con la versión 2.2.0 de la skill, Claude Code 2.1.329, el modelo `sonnet`, en Windows 11. **Esta ronda es parcial:** 26 de 36 ejecuciones son válidas, y en ninguna de las válidas la skill llegó a trabajar. Abajo está lo que muestran las ejecuciones válidas y por qué falta el resto.

## Resumen

- **La skill nunca se activó en los pedidos de revisión y de corrección.** Estaba instalada en la condición "con skill", y su descripción menciona "bug fix" y "security review", pero en las 12 ejecuciones el modelo respondió sin llamarla. Así que esas dos tareas comparan el modelo consigo mismo, y las diferencias entre condiciones son ruido.
- **Las refactorizaciones con la skill no son válidas.** El modo refactorización de la skill se detiene y pide "pode" antes de empezar. El script debía responder a eso, pero solo reconocía preguntas terminadas en "?", y el mensaje de la skill pide sin signo de interrogación. Las 6 refactorizaciones con la skill se detuvieron en el mensaje inicial. El script se corrigió; las ejecuciones no se repitieron, por decisión del dueño del proyecto, para limitar el gasto.
- **Ninguna de las tres hipótesis de [METRICS.md](../benchmark/refactor/METRICS.md) pudo probarse.**

El hallazgo que importa para quien usa la skill: **en una revisión o una corrección pequeña, instalarla no basta; hay que pedirla** (por ejemplo: "usa la skill principal-secops-dev-token-optimizer"). Un pedido de refactorización del proyecto entero sí la activa (6 de 6).

## Cómo se armó

Un sistema administrativo de una tienda pequeña ("Loja do Bairro"), escrito con prisa, con cerca de 2.700 líneas de código, en Python y en Node.js. Cada versión tiene las mismas 8 fallas de seguridad, 4 problemas de calidad y 1 bug, plantados sin comentarios que los señalen. Tres pedidos, escritos como los escribiría el dueño de la tienda (en portugués):

1. **Revisión:** "Revisa el código de este proyecto y dime qué problemas tiene, del más grave al menos grave. No modifiques ningún archivo."
2. **Corrección:** "Un cliente hizo un pedido de exactamente R$ 500,00 y no recibió el descuento del 10% que promete la regla de la tienda. Corrígelo."
3. **Refactorización:** "Refactoriza todo este proyecto para que sea más fácil de mantener, sin cambiar el comportamiento. El proyecto ya está en Git, con el árbol limpio."

Pruebas ocultas, que el agente nunca ve, verifican la corrección y que la API pública siga igual. La skill se carga desde una copia que solo contiene el plugin, para que ninguna condición alcance las respuestas esperadas. Proyectos, pruebas ocultas, respuestas esperadas y validador: [benchmark/refactor/](../benchmark/refactor/).

## Resultados válidos

Promedios por celda. "Comportamiento preservado" significa que las pruebas ocultas de contrato y las pruebas originales del proyecto pasan en el código que dejó el agente.

| Tarea | Lenguaje | Condición (¿skill llamada?) | Ejecuciones | Tiempo (s) | Tokens de salida | Costo (USD) | Archivos / líneas cambiados | Corrección correcta | Comportamiento preservado |
|---|---|---|---|---|---|---|---|---|---|
| Corrección | Python | sin | 3 | 17 | 1.542 | 0,08 | 1,3 / 5 | 3/3 | 3/3 |
| Corrección | Python | con (no llamada) | 2 | 19 | 2.000 | 0,08 | 2 / 11 | 2/2 | 2/2 |
| Corrección | Node.js | sin | 3 | 11 | 867 | 0,07 | 1 / 2 | 3/3 | 3/3 |
| Corrección | Node.js | con (no llamada) | 3 | 16 | 1.652 | 0,08 | 1,7 / 11 | 3/3 | 3/3 |
| Revisión | Python | sin | 2 | 91 | 11.879 | 0,41 | 0 | n/a | 2/2 |
| Revisión | Python | con (no llamada) | 2 | 83 | 10.348 | 0,38 | 0 | n/a | 2/2 |
| Revisión | Node.js | sin | 3 | 54 | 6.162 | 0,36 | 0 | n/a | 3/3 |
| Revisión | Node.js | con (no llamada) | 2 | 82 | 10.493 | 0,45 | 0 | n/a | 2/2 |
| Refactorización | Python | sin | 3 | 238 | 36.034 | 1,26 | 7,7 / 318 | n/a | 3/3 |
| Refactorización | Node.js | sin | 3 | 575 | 87.645 | 2,91 | 17,3 / 1.865 | n/a | 3/3 |

Lo que muestran las ejecuciones válidas, independientemente de la skill:

- **El bug es fácil de corregir solo con el modelo.** Las 11 ejecuciones de corrección acertaron, en 10 a 20 segundos y por menos de USD 0,10, tocando uno o dos archivos.
- **La refactorización sin la skill preservó el comportamiento en 6 de 6 ejecuciones**, a USD 1,26 (Python) y 2,91 (Node.js) por ejecución. En una ejecución en Node.js también corrigió el límite de R$ 500,00 sin que se le pidiera, lo que cambia un comportamiento que el README dice que está mal.
- **Las respuestas de revisión no se evaluaron.** Como la skill no se llamó en ninguna, una evaluación a ciegas compararía el modelo consigo mismo.

## Ejecuciones excluidas

Diez ejecuciones quedaron aparte, sin borrarse:

- Las 6 refactorizaciones con la skill, detenidas en el mensaje inicial de la skill (defecto del script, descrito arriba).
- 4 ejecuciones de revisión y corrección en las que el script respondió "pode seguir" a una oferta como "¿quieres que lo corrija?". En una revisión que pedía no modificar archivos, esa respuesta autorizó cambios. Ahora el script solo responde en la tarea de refactorización.

## Costo

USD 22,16 en total, contando las ejecuciones excluidas.

## Próximo paso

Para medir la skill misma en código existente, o el pedido la nombra, en las dos condiciones, o se cambia su descripción para que una revisión o una corrección la active por sí sola. En ambos casos, el script ya maneja el "pode" del modo refactorización. Para reproducir:

```
python benchmark/refactor/validate.py
python benchmark/run_benchmark.py --suite refactor --config-dir cfg --out ../bench-refactor --reps 3 --jobs 3 --timeout 2400
python benchmark/analyze_refactor.py --runs ../bench-refactor
```

Valen las mismas advertencias del [primer benchmark](BENCHMARK.es.md#cómo-reproducir): gasta tokens en el login copiado y debe ejecutarse en un sandbox.
