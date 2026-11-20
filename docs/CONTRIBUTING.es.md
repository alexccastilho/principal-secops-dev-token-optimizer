*Léelo en otros idiomas: [English](../CONTRIBUTING.md) · [Português (Brasil)](CONTRIBUTING.pt-BR.md)*

# Cómo contribuir

Gracias por considerar una contribución. Este documento explica qué está dentro del alcance, cómo probar un cambio y las convenciones en las que se apoya la skill. La documentación para quien la usa es el [README](README.es.md).

## Qué es este proyecto

Una skill, no una aplicación: `skills/principal-secops-dev-token-optimizer/SKILL.md` y los archivos que enlaza son instrucciones que Claude lee. La mayoría de las contribuciones cambian texto, y cambiar el texto cambia el comportamiento. Trata una frase del `SKILL.md` como tratarías una línea de código.

El público es fijo: una persona que **no programa**, atendida en portugués de Brasil sencillo. Las contribuciones que hacen las respuestas más largas, más técnicas o menos seguras para esa persona quedan fuera del alcance, aunque sean correctas.

## Prioridades

Cada cambio se evalúa en el mismo orden que la skill usa en caso de conflicto:

1. **Seguridad.** Nunca debilitar la línea base, el modelo de amenazas ni la verificación previa a la entrega.
2. **Integridad del sistema.** La skill nunca debe romper código que funciona: alcance mínimo, contratos preservados, permiso explícito para acciones destructivas.
3. **Claridad para quien la usa.** pt-BR sencillo, una instrucción de aplicar y probar, ninguna jerga sin traducir.
4. **Estructura.** Código que sigue siendo fácil de cambiar (sección 9 del `SKILL.md`).
5. **Ahorro de tokens.** El `SKILL.md` se carga cada vez que la skill se activa. El detalle va en una referencia, cargada bajo demanda.
6. **Estilo.**

## Preparar el entorno

Necesitas Git y Python 3.8 o más reciente. Nada más: el escáner, las pruebas y las herramientas solo usan la biblioteca estándar, a propósito. La skill se ejecuta en los entornos aislados de claude.ai y en equipos de personas que no programan, donde instalar un paquete es un paso que falla.

```bash
git clone https://github.com/alexccastilho/principal-secops-dev-token-optimizer.git
cd principal-secops-dev-token-optimizer
python -B -m unittest discover -s tests -v
```

La única excepción es `tools/make_icon.py`: necesita Pillow, y solo para volver a dibujar el icono.

## Probar un cambio

- **La suite de pruebas** debe pasar antes y después de tu cambio. GitHub Actions la ejecuta en Linux y Windows, con Python 3.8 y la versión actual.
- **Los cambios en el escáner** necesitan una prueba en `tests/test_scanner.py`, con un fragmento que debe marcarse y otro que no. Un falso positivo es tan grave como un falso negativo: con la regla "entrega solo con cero HIGH", un falso positivo hace que Claude reescriba código que funciona.
- **Los cambios en el `SKILL.md` o en una referencia** necesitan una comprobación manual: prueba al menos un escenario afectado de `evals/evals.json` en Claude Code (`claude --plugin-dir .`) o subiendo el ZIP a claude.ai, y compara la respuesta con sus aserciones. Si el comportamiento es nuevo, añade un escenario.
- **Nunca pegues un secreto real** en una prueba, un eval o un issue. Usa valores claramente falsos.

## Convenciones

### Enlaces de la skill

- Cada archivo de `references/` debe estar enlazado desde la tabla de la sección 6 del `SKILL.md`. Una referencia que nadie enlaza es texto muerto, y un enlace a un archivo inexistente es una promesa rota. La suite de pruebas comprueba ambas cosas.
- La descripción del `SKILL.md` no supera los 1024 caracteres, el límite del formato de skill.
- Los números de sección del `SKILL.md` se citan desde otros archivos ("sección 4, regla 9"). Añade las secciones nuevas al final en lugar de renumerar.
- Las referencias se escriben en inglés, como el `SKILL.md`. El texto que la skill muestra a quien la usa (ejemplos de respuesta, preguntas, nombres de archivo como `LEIA-ME.md`) va en pt-BR.

### Versiones y lanzamientos

- La versión vive en dos lugares, `.claude-plugin/plugin.json` y `metadata.version` en el `SKILL.md`, y debe coincidir con la primera entrada de los tres changelogs. La suite de pruebas lo comprueba.
- Para lanzar una versión: actualiza ambos, añade la entrada en `CHANGELOG.md`, `docs/CHANGELOG.pt-BR.md` y `docs/CHANGELOG.es.md`, ejecuta `python tools/build_zip.py` y adjunta el ZIP de `dist/` a la release en GitHub.

### Documentación en tres idiomas

README, CHANGELOG y CONTRIBUTING existen en inglés (en la raíz), portugués y español (en `docs/`). Un cambio en uno se hace en los tres en el mismo pull request, y los README mantienen las mismas secciones.

La documentación parece escrita por una persona: nada de raya ni semirraya como inciso, comillas rectas, tres puntos en lugar del carácter de puntos suspensivos, nada de vocabulario inflado. La suite de pruebas falla con el primer carácter prohibido.

### Trabajo de terceros

Partes de la skill adaptan [caldoai/skills](https://github.com/caldoai/skills) (MIT). Si adaptas otro trabajo de terceros, su licencia debe permitirlo, y el crédito y el texto de la licencia van en `skills/principal-secops-dev-token-optimizer/THIRD_PARTY_NOTICES.md`, que va incluido en el ZIP.

### Commits

Un cambio completo por commit, con un mensaje que diga qué cambió y por qué. No mezcles un renombrado masivo o un cambio de formato con un cambio de comportamiento.

## Informar de problemas

Errores e ideas: abre un issue con las plantillas. Vulnerabilidades de seguridad: nunca en un issue público; consulta [SECURITY.md](../SECURITY.md).

## Licencia

Al contribuir, aceptas que tu contribución queda bajo la Licencia MIT, la misma que el resto del proyecto (consulta [LICENSE](../LICENSE)).
