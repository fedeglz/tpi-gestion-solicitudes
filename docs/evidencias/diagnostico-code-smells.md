# Diagnóstico de deuda técnica y code smells (tag `etapa-diagnostico`)

Versión analizada: `estado-inicial` (`main.py`, 202 líneas). Líneas = número de línea en ese tag.

| # | Code smell | Evidencia | Ubicación | Impacto | Riesgo de mantenimiento | Prioridad | Se resuelve en |
|---|-----------|-----------|-----------|---------|-------------------------|-----------|----------------|
| 1 | God Module / viola SRP | Un único archivo mezcla persistencia, validación, reglas de negocio, formato de salida y CLI | 1-202 | Cualquier cambio toca todo; imposible probar una parte aislada | Alto | Alta | R5 |
| 2 | Estado global mutable | `DB` global y `global DB` en `cargar()` | 7, 14 | Acoplamiento oculto, orden de llamadas importa, no se puede testear en paralelo | Alto | Alta | R5 |
| 3 | Strings mágicos duplicados | `"Pendiente"`, `"En proceso"`, `"Resuelta"`, `"Rechazada"`, tipos y áreas repetidos como literales | 34-158 | Un error tipográfico no se detecta; cambiar un nombre exige buscar en todo el archivo | Alto | Alta | R1 |
| 4 | Nombres crípticos | `reg`, `cambiar`, `asig`, `rep`, variables `n`, `t`, `p`, `d`, `ne`, `x`, `s`, `e` | 13-162 | El código no se lee sin contexto; curva de entrada alta | Medio | Media | R1 |
| 5 | Long Parameter List / Data Clump / Primitive Obsession | `reg(dni, n, mail, t, p, d, fecha)` con 7 parámetros; `buscar(e, t, p)` | 32, 107 | Fácil intercambiar argumentos del mismo tipo; agregar un campo rompe todas las llamadas | Medio | Media | R3 |
| 6 | Código duplicado | Búsqueda por id repetida en `cambiar` y `asig`; bucle de conteo copiado 3 veces en `rep` | 61-64, 92-95, 132-152 | Corregir un bug exige hacerlo en varios lugares | Alto | Alta | R2 |
| 7 | Long Method / complejidad ciclomática alta | `reg` CC=15, `rep` CC=14, `main` CC=14 (radon) | 32, 130, 162 | Difícil de entender y de probar; muchas ramas | Alto | Alta | R2 |
| 8 | `except:` desnudo / errores tragados | `cargar()` ignora cualquier error; si el JSON está corrupto arranca vacío y el próximo guardado **pisa los datos** | 19-20, 177, 182 | Pérdida silenciosa de datos; errores reales ocultos | Alto | Alta | R1 y paso 10 |
| 9 | Códigos de error + `print` dentro de la lógica | `return -1` / `return False` con `print("ERROR...")` en la regla de negocio | 35-100 | Lógica mezclada con E/S; el llamador debe interpretar valores mágicos | Medio | Media | R4 |
| 10 | Cadenas `if/elif` para transiciones (viola OCP) | Reglas de transición codificadas en ifs anidados | 66-81 | Agregar un estado obliga a modificar la función | Medio | Media | R4 |
| 11 | Dependencia directa del sistema de archivos (viola DIP) | `open()` y `json` llamados desde las reglas de negocio | 13-29, 54 | No se puede probar sin disco ni cambiar el almacenamiento | Medio | Media | R5 |
| 12 | Código muerto y comentarios obsoletos | Ruta hardcodeada de un usuario y TODO sin dueño | 9, 10 | Ruido y datos personales en el repositorio | Bajo | Baja | R1 |
| 13 | Comparaciones `== None` / `!= None` | 8 avisos E711 de flake8 | 49, 64, 95, 111-115, 122, 156 | No idiomático; falla con objetos que redefinen `==` | Bajo | Baja | R1 |
| 14 | Ausencia de pruebas automatizadas | No hay tests; refactorizar es riesgoso | — | Imposible garantizar que no hay regresiones | Alto | Alta | Paso 03 (previo a refactorizar) |

Métricas del tag `estado-inicial`: 202 LOC · complejidad ciclomática promedio **B (9.75)** · 3 funciones con CC ≥ 14 · flake8: 11 avisos (8× E711, 3× E722).
