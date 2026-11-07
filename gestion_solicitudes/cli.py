"""Interfaz de linea de comandos: interpreta argumentos, invoca al servicio, imprime."""
import datetime
import os

from . import reporte
from .dominio import ErrorDeNegocio, FiltroBusqueda, NuevaSolicitud
from .repositorio import RepositorioJSON
from .servicio import ServicioSolicitudes

USO = "Uso: main.py <registrar|estado|asignar|buscar|reporte> ..."


def _ruta_datos():
    return os.environ.get("SOLICITUDES_DB", "data/solicitudes.json")


def _fecha_de_hoy():
    return os.environ.get("SOLICITUDES_FECHA") or str(datetime.date.today())


def _leer_id_y_texto(args):
    try:
        return int(args[0]), args[1]
    except (IndexError, ValueError):
        raise ErrorDeNegocio("argumentos invalidos")


def _leer_filtro(args):
    valores = {}
    for argumento in args:
        for campo in ("estado", "tipo", "prioridad"):
            prefijo = "--%s=" % campo
            if argumento.startswith(prefijo):
                valores[campo] = argumento[len(prefijo):]
    return FiltroBusqueda(**valores)


def ejecutar(args, servicio):
    """Ejecuta un comando y devuelve las lineas de salida. Lanza ErrorDeNegocio."""
    if not args:
        return [USO]
    comando, resto = args[0], args[1:]
    if comando == "registrar":
        if len(resto) < 6:
            raise ErrorDeNegocio("faltan argumentos")
        return ["OK: solicitud %d registrada" % servicio.registrar(NuevaSolicitud(*resto[:6]))]
    if comando == "estado":
        id_solicitud, destino = _leer_id_y_texto(resto)
        servicio.cambiar_estado(id_solicitud, destino)
        return ["OK: solicitud %d ahora %s" % (id_solicitud, destino)]
    if comando == "asignar":
        id_solicitud, area = _leer_id_y_texto(resto)
        servicio.asignar_responsable(id_solicitud, area)
        return ["OK: solicitud %d asignada a %s" % (id_solicitud, area)]
    if comando == "buscar":
        encontradas = servicio.buscar(_leer_filtro(resto))
        return reporte.listado(encontradas, servicio.nombre_de)
    if comando == "reporte":
        return reporte.generar_reporte(servicio.todas())
    raise ErrorDeNegocio("comando desconocido %s" % comando)


def main(args):
    servicio = ServicioSolicitudes(RepositorioJSON(_ruta_datos()), _fecha_de_hoy)
    try:
        lineas = ejecutar(args, servicio)
    except ErrorDeNegocio as error:
        lineas = ["ERROR: %s" % error]
    for linea in lineas:
        print(linea)
