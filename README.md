# Sistema de Gestión de Solicitudes Académicas (versión inicial)

Módulo simple para registrar y gestionar solicitudes de estudiantes (constancias,
equivalencias, reclamos). TPI de Metodología de Sistemas II – UTN TUP a Distancia.

## Uso
    python main.py registrar <dni> <nombre> <email> <tipo> <prioridad> <descripcion>
    python main.py estado <id> <nuevo_estado>
    python main.py asignar <id> <responsable>
    python main.py buscar [--estado=..] [--tipo=..] [--prioridad=..]
    python main.py reporte

Tecnologías: Python 3 (solo librería estándar). Datos en `data/solicitudes.json`.
