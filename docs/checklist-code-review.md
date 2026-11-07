# Checklist de code review (tag `etapa-docs`)

Se aplicó sobre el repositorio en el commit previo a `estado-refactorizado`. Marca: ✅ cumple · ⚠️ observación registrada · ❌ no cumple.

## 1. Funcionalidad y comportamiento externo
- [x] ✅ Las 4+ operaciones (registrar, cambiar estado, asignar, buscar/filtrar, reporte) funcionan igual que en `estado-inicial`.
- [x] ✅ `scripts/golden_master.py` produce salida idéntica en ambos tags (`diff` vacío).
- [x] ⚠️ Los errores devuelven código de salida 0 (heredado). Ver O-05.

## 2. Legibilidad y Clean Code
- [x] ✅ Nombres descriptivos y consistentes (español, sin abreviaturas).
- [x] ✅ Funciones cortas (≤ 30 líneas) y con un solo nivel de abstracción.
- [x] ✅ Sin código muerto ni comentarios obsoletos.
- [x] ✅ Sin strings mágicos: enums `Estado`, `Tipo`, `Prioridad`, `Area`.

## 3. Diseño (SOLID)
- [x] ✅ SRP: dominio / repositorio / servicio / reporte / cli separados.
- [x] ✅ OCP: transiciones en la tabla `TRANSICIONES`; agregar un estado no modifica funciones.
- [x] ✅ LSP: no hay jerarquías de herencia que violen el contrato; `RepositorioEnMemoria` sustituye a `RepositorioJSON`.
- [x] ✅ ISP: el servicio depende de un protocolo de dos métodos (`cargar`, `guardar`).
- [x] ✅ DIP: `ServicioSolicitudes` recibe repositorio y reloj por constructor.
- [x] ✅ Sin estado global mutable.

## 4. Manejo de errores
- [x] ✅ Sin `except:` desnudo; excepciones específicas.
- [x] ✅ Errores de negocio como `ErrorDeNegocio`, convertidos a mensaje solo en la capa CLI.
- [x] ✅ Archivo corrupto informado y sin pisar datos (paso 10).

## 5. Pruebas
- [x] ✅ Pruebas de caracterización (caja negra) + unitarias + prueba del cambio intencional.
- [x] ⚠️ `cli.py` no figura en la cobertura medida porque se prueba por subprocess. Ver O-03.

## 6. Repositorio y documentación
- [x] ✅ Historial de commits atómico, con mensajes convencionales (`refactor:`, `test:`, `docs:`).
- [x] ✅ Tags: `estado-inicial`, `etapa-diagnostico`, `etapa-refactoring`, `etapa-pruebas`, `etapa-docs`, `estado-refactorizado`.
- [x] ✅ README con descripción, instalación/uso, funcionalidades y tecnologías.
- [x] ✅ Sin datos personales reales (datos sintéticos).

## Criterios de aceptación técnica
1. Todas las pruebas en verde. 2. `diff` del golden master vacío. 3. `flake8` sin avisos. 4. CC ≤ 10 por función. 5. Cero variables globales mutables. 6. Todo cambio de comportamiento documentado en `decisiones-tecnicas.md`.

## Registro de observaciones
| ID | Hallazgo | Severidad | Acción | Estado |
|----|----------|-----------|--------|--------|
| O-01 | `servicio.py` importaba `Estado` sin usarlo (flake8 F401) | Baja | Eliminar import | Corregido |
| O-02 | `cli.ejecutar` tiene CC=8: concentra el enrutamiento de comandos | Baja | Aceptado (≤ 10). Mejora futura: tabla de comandos | Aceptado |
| O-03 | La cobertura unitaria no incluye `cli.py` | Media | Mejora futura: probar `main(args)` capturando stdout | Pendiente |
| O-04 | `interpretar()` recorre el Enum en cada llamada | Baja | Aceptado: 3-4 miembros, sin impacto | Aceptado |
| O-05 | Errores terminan con exit code 0 | Media | Se conserva para no cambiar el contrato; proponer exit 1 como cambio versionado | Pendiente |
| O-06 | JSON corrupto se ignoraba y se pisaban datos | Alta | Lanzar `ErrorDeDatos` sin escribir | Corregido (paso 10) |
| O-07 | Si el DNI ya existe, se ignoran nombre/email nuevos | Baja | Comportamiento heredado; fijado por test | Aceptado |
