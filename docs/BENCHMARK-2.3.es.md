# Benchmark de la 2.3.0 (parcial): sin la skill, 2.2.1 y 2.3.0

[English](BENCHMARK-2.3.md) · [Português](BENCHMARK-2.3.pt-BR.md) · [Primer benchmark](BENCHMARK.es.md) · [Benchmark de refactorización](BENCHMARK-REFACTOR.es.md)

Ejecutado el 2026-11-25 con Claude Code 2.1.332, el modelo `sonnet` (`claude-sonnet-5-5`), en Windows 11, en la configuración aislada de `benchmark/run_benchmark.py`. Tres condiciones: sin la skill, versión 2.2.1 y versión 2.3.0. La 2.3.0 se midió a partir de los archivos de la rama `v2.3` antes del primer commit, así que sus ejecuciones registran el commit base con `-dirty`. **Esta ronda es parcial:** tres lenguajes en lugar de seis, dos o tres repeticiones por celda y un solo modelo. Los resúmenes, las notas a ciegas y los mapas de etiquetas están en [benchmark/results/2.3.0/](../benchmark/results/2.3.0/). La segunda ronda de app nueva está en `custos2.json` y `create2-summary.json`. En la 2.3.1 los resúmenes se recalcularon a partir de las mismas ejecuciones, sin llamar de nuevo al modelo: costo con tres decimales, compilación de C# como no verificada (0/0) en lugar de fallida, y las pruebas originales de Node.js en la suite de refactorización como 3/3; un comando de prueba equivocado las había registrado como 0/3.

## Versión corta

- **Activación:** la 2.3.0 se cargó en todo tipo de pedido de código probado y en ningún pedido que no era de código. La 2.2.1 nunca se cargó para corregir un error en un proyecto existente, crear un campo, crear una tabla, actualizar dependencias o escribir pruebas.
- **Costo:** con la skill funcionando en ambas, la 2.3.0 no fue más cara que la 2.2.1 (USD 1,61 contra 1,73 en las tres apps, 0,75 contra 0,81 en las dos revisiones), una diferencia dentro del ruido. Una corrección pequeña ahora cuesta USD 0,10 en lugar de 0,06, porque ahora la skill se carga; en la 2.2.1 no se cargaba, así que esa ejecución era el modelo solo.
- **Calidad:** en las revisiones a ciegas, las apps de la 2.3.0 fueron tan seguras como las de la 2.2.1 o más, y más fáciles de ejecutar para quien no programa. Las revisiones de la 2.3.0 encontraron tantos problemas plantados como las demás, sin ninguna afirmación falsa.
- **No verificado:** el C# no se pudo compilar (no hay SDK de .NET en la máquina de prueba) en ninguna condición. Una app Node.js de la 2.3.0 se entregó sin sus dos paquetes declarados en `package.json`.

## Activación

Diez pedidos que deben cargar la skill y cuatro que no, en proyectos Python y Node.js, dos repeticiones cada uno (4 ejecuciones por pedido). El criterio de la puerta 5 se registró antes de las ejecuciones de la 2.3.0 (`gate5-preregistro.md` en la carpeta de resultados).

| Pedido | Sin skill | 2.2.1 | 2.3.0 |
|---|---|---|---|
| a01 revisa el código, problema más grave | 0/4 | 4/4 | 4/4 |
| a02 ¿hay problemas de seguridad? | 0/4 | 4/4 | 4/4 |
| a03 total del pedido incorrecto con descuento | 0/4 | 4/4 | 4/4 |
| a04 error al registrar cliente sin teléfono | 0/4 | 2/4 | 4/4 |
| a05 agrega un campo de CPF | 0/4 | 0/4 | 4/4 |
| a06 ¿es seguro publicarlo? | 0/4 | 4/4 | 4/4 |
| a07 actualiza las dependencias | 0/4 | 0/4 | 4/4 |
| a08 crea una tabla de proveedores | 0/4 | 0/4 | 4/4 |
| a09 informe de ventas lento | 0/4 | 4/4 | 4/4 |
| a10 escribe pruebas para el descuento | 0/4 | 0/4 | 3/4 |
| n01 a n04 (LGPD, correo, capital, traducción) | 0/16 | 0/16 | 0/16 |
| Suite de refactorización: revisión | 0/6 | 6/6 | 6/6 |
| Suite de refactorización: corrección | 0/6 | 0/6 | 6/6 |

La descripción de la 2.3.0 se eligió en un piloto pequeño en la tarea de corrección antes de esta ronda: el primer borrador se cargó en 0 de 4 y el texto final ("cargar antes de la primera edición de cualquier archivo de código, incluso en una corrección de una línea") en 4 de 4.

## App nueva (contactos con login y SQLite)

Dos repeticiones por lenguaje. La primera ronda de la 2.3.0 perdió en entrega en la revisión a ciegas: sus apps pedían escribir comandos en una terminal. Se cambió la regla de entrega proporcional para que quien no programa siempre reciba un lanzador de doble clic y los requisitos con su enlace, y las apps de la 2.3.0 se hicieron de nuevo. La tabla muestra esa segunda ronda.

| Lenguaje | Condición | Costo (USD) | Tokens de salida | Escritura en caché | Lectura de caché | Turnos | Tiempo (s) |
|---|---|---|---|---|---|---|---|
| Python | sin skill | 0,123 | 6.599 | 12.540 | 69.268 | 5 | 47 |
| Python | 2.2.1 | 0,488 | 21.069 | 51.769 | 699.964 | 30,5 | 163 |
| Python | 2.3.0 | 0,440 | 18.458 | 47.462 | 659.290 | 35 | 135 |
| Node.js | sin skill | 0,262 | 14.842 | 21.289 | 286.184 | 14,5 | 93 |
| Node.js | 2.2.1 | 0,582 | 26.687 | 59.248 | 781.052 | 37 | 174 |
| Node.js | 2.3.0 | 0,553 | 26.655 | 54.129 | 695.806 | 43 | 172 |
| C# | sin skill | 0,257 | 15.280 | 22.648 | 137.148 | 17,5 | 89 |
| C# | 2.2.1 | 0,655 | 31.094 | 71.730 | 557.400 | 35,5 | 199 |
| C# | 2.3.0 | 0,621 | 31.828 | 60.784 | 598.422 | 45,5 | 199 |

Total de las tres apps: USD 1,614 con la 2.3.0, contra 1,725 con la 2.2.1 y 0,642 sin la skill. Con dos repeticiones es del tamaño del ruido: en la primera ronda de la 2.3.0, Python costó 6% más que la 2.2.1 y C# 24% menos.

**Compilación.** Python y Node.js compilaron en todas las ejecuciones de todas las condiciones. El C# no se compiló en ninguna condición: la máquina de prueba no tiene el SDK de .NET.

**Funciona tal como se entrega.** 11 de las 12 ejecuciones de la 2.3.0 ejecutaron el escáner con `--entrega`. La que no lo hizo fue una app Node.js cuyo `npm install` bloqueó el banco de pruebas; dejó `package.json` sin `express` ni `helmet`. Su lanzador los instala, pero un `npm start` en una copia nueva falla. Después de esta ronda se agregó una frase a la puerta (si la instalación está bloqueada, escribir la dependencia en el manifiesto a mano); esa frase no se midió.

**Revisión a ciegas.** Otro modelo calificó una app por lenguaje y condición, con etiquetas al azar, en seguridad y en entrega para quien no programa (1 a 10), en dos rondas con dos evaluadores. La segunda rúbrica agregó dos criterios de entrega (nada de escribir en una terminal, todos los requisitos nombrados) que son las mismas reglas añadidas a la skill entre las rondas; los criterios de seguridad fueron los mismos.

| Condición | Seguridad, ronda 1 | Entrega, ronda 1 | Seguridad, ronda 2 | Entrega, ronda 2 |
|---|---|---|---|---|
| Sin skill | 7,3 | 6,0 | 6,0 | 4,3 |
| 2.2.1 | 8,7 | 7,0 | 8,0 | 6,0 |
| 2.3.0 | 8,7 | 5,7 | 9,0 | 7,7 |

Las mismas apps sin skill y de la 2.2.1 recibieron notas distintas de los dos evaluadores: compare las condiciones dentro de cada ronda. El único defecto crítico estaba en una app Node.js sin la skill, calificada en las dos rondas.

**Escáner.** Ningún HIGH real. Dos apps Node.js de la 2.3.0 dispararon un HIGH falso en `db.exec` de SQLite con un número validado: la regla `child-process-exec`, anterior a la 2.3.0, lo confunde con el `exec` de `child_process`. La app Node.js que omitió la puerta también tiene dos hallazgos `sql-template-js` falsos en un fragmento `WHERE` constante.

## Proyecto existente (suite de refactorización)

El proyecto de práctica de 2.700 líneas del [benchmark de refactorización](BENCHMARK-REFACTOR.es.md), tres repeticiones.

| Tarea | Lenguaje | Sin skill | 2.2.1 | 2.3.0 |
|---|---|---|---|---|
| Revisión, costo (USD) | Python | 0,365 | 0,416 | 0,386 |
| Revisión, costo (USD) | Node.js | 0,357 | 0,389 | 0,359 |
| Corrección, costo (USD) | Python | 0,060 | 0,058 (skill no cargada) | 0,100 |
| Corrección, costo (USD) | Node.js | 0,058 | 0,058 (skill no cargada) | 0,098 |
| Corrección resuelta | ambos | 6/6 | 6/6 | 6/6 |

Las 18 respuestas de revisión se calificaron a ciegas contra la clave de respuestas (`benchmark/refactor/manifest/`):

| Condición | Problemas plantados encontrados (promedio de 13) | Afirmaciones falsas (total) | Problema más grave correcto |
|---|---|---|---|
| Sin skill | 10,8 | 4 | 6/6 |
| 2.2.1 | 11,2 | 2 | 4/6 |
| 2.3.0 | 11,3 | 0 | 6/6 |

El evaluador contó la inyección de SQL como la clase más grave; las dos respuestas de la 2.2.1 que pusieron primero el hash MD5 son las marcadas como erróneas.

## Puertas para publicar

| Puerta | Resultado |
|---|---|
| 1. Pruebas y ZIP | Pasó: 57 pruebas |
| 2. Toda app nueva compila | **Aceptada por el dueño el 2026-11-25.** Python y Node.js 8 de 8; C# no verificado; una app Node.js falla con un `npm start` simple |
| 3. Seguridad al menos igual a la 2.2.1 | Pasó en las dos rondas a ciegas |
| 4. Costo por entrega que funciona no mayor que la 2.2.1 | **Aceptada por el dueño el 2026-11-25.** No fue más cara donde la skill funciona en ambas; la corrección cuesta USD 0,04 más, el precio de cargarse en cada edición |
| 5. Activación (criterio registrado antes) | Pasó: 6/6, 19/20, 26/26, 0/16 |

## Límites

Tres lenguajes, dos o tres repeticiones por celda y un modelo: unos centavos de diferencia por app están dentro del ruido. Cada ejecución tenía solo este plugin, así que el trabajo junto con otras skills (sección 11) no se midió. Las rondas de activación y de revisión usaron el `SKILL.md` anterior a sus dos últimas frases (lanzador e instalación bloqueada). El piloto que eligió la descripción usó la tarea de corrección, que también se mide aquí. La regla de entrega proporcional se corrigió después de la primera revisión a ciegas y solo la suite de creación se ejecutó de nuevo. El banco de pruebas bloquea la instalación de paquetes y los servidores en ejecución, lo que es más estricto que una sesión real.
