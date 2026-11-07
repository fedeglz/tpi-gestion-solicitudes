# Sistema de Gestión de Solicitudes Académicas

TPI – Metodología de Sistemas II · UTN Tecnicatura Universitaria en Programación a Distancia.
Módulo simple para registrar y gestionar solicitudes de estudiantes (constancias, equivalencias,
reclamos), usado como caso de estudio de **calidad interna, deuda técnica y refactoring seguro**.

## Funcionalidades
- Registrar solicitudes (tipo, prioridad, estudiante, descripción).
- Cambiar estado respetando el flujo `Pendiente → En proceso → Resuelta` (o `Rechazada`).
- Asignar responsable (`Alumnado`, `Bedelia`, `Tecnica`).
- Buscar/filtrar por estado, tipo y prioridad.
- Reporte con totales por estado, tipo y prioridad.

## Instalación y uso
Requisitos: Python 3.9 o superior. No hay dependencias externas.

    python main.py registrar <dni> <nombre> <email> <tipo> <prioridad> <descripcion>
    python main.py estado <id> "En proceso"
    python main.py asignar <id> Bedelia
    python main.py buscar --estado=Pendiente --tipo=reclamo
    python main.py reporte

Variables opcionales: `SOLICITUDES_DB` (ruta del JSON, por defecto `data/solicitudes.json`) y
`SOLICITUDES_FECHA` (fija la fecha, útil para pruebas). Usar solo datos sintéticos.

## Pruebas
    python -m unittest discover -s tests          # todas las pruebas
    python scripts/golden_master.py salida.txt    # transcripción para comparar versiones
    diff docs/evidencias/golden_inicial.txt docs/evidencias/golden_refactorizado.txt   # debe estar vacío

## Estructura
    main.py                      punto de entrada
    gestion_solicitudes/
      dominio.py                 entidades, enums y reglas (sin E/S)
      repositorio.py             persistencia JSON (detrás de un Protocol)
      servicio.py                casos de uso (recibe repositorio y reloj)
      reporte.py                 formato de salida
      cli.py                     interpretación de comandos
    tests/                       caracterización, unitarias y cambio intencional
    scripts/golden_master.py     evidencia antes/después
    docs/                        diagnóstico, checklist de code review, decisiones y evidencias

## Tags del repositorio
`estado-inicial` · `etapa-diagnostico` · `etapa-refactoring` · `etapa-pruebas` · `etapa-docs` · `estado-refactorizado`

## Tecnologías
Python 3, `unittest`, `dataclasses`, `enum`, JSON. Análisis: `radon`, `flake8`, `coverage`.
