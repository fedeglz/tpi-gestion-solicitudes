"""Presentacion de resultados como texto (sin I/O: devuelve listas de lineas)."""
from .dominio import Estado, Prioridad, Tipo


def formatear_solicitud(solicitud, nombre_estudiante):
    responsable = solicitud.responsable.value if solicitud.responsable else "-"
    return " | ".join(["#%d" % solicitud.id, solicitud.fecha, nombre_estudiante,
                       solicitud.tipo.value, solicitud.prioridad.value,
                       solicitud.estado.value, responsable])


def listado(solicitudes, nombre_de):
    lineas = [formatear_solicitud(s, nombre_de(s.dni)) for s in solicitudes]
    lineas.append("%d resultado(s)" % len(solicitudes))
    return lineas


def _conteo(titulo, solicitudes, extraer, enum_clase):
    lineas = ["-- %s --" % titulo]
    for miembro in enum_clase:
        cantidad = sum(1 for s in solicitudes if extraer(s) == miembro)
        lineas.append("%s: %d" % (miembro.value, cantidad))
    return lineas


def generar_reporte(solicitudes):
    sin_responsable = sum(1 for s in solicitudes if s.responsable is None and not s.esta_cerrada)
    lineas = ["=== REPORTE ===", "Total: %d" % len(solicitudes)]
    lineas += _conteo("Por estado", solicitudes, lambda s: s.estado, Estado)
    lineas += _conteo("Por tipo", solicitudes, lambda s: s.tipo, Tipo)
    lineas += _conteo("Por prioridad", solicitudes, lambda s: s.prioridad, Prioridad)
    lineas.append("Sin responsable (abiertas): %d" % sin_responsable)
    return lineas
