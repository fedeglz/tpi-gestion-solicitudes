# Sistema de Gestion de Solicitudes Academicas
# R4: Replace Error Code with Exception + Replace Conditional with Table (OCP)
import sys
import json
import os
import datetime
from dataclasses import dataclass
from typing import Optional

ESTADO_PENDIENTE = "Pendiente"
ESTADO_EN_PROCESO = "En proceso"
ESTADO_RESUELTA = "Resuelta"
ESTADO_RECHAZADA = "Rechazada"
ESTADOS = [ESTADO_PENDIENTE, ESTADO_EN_PROCESO, ESTADO_RESUELTA, ESTADO_RECHAZADA]
TIPOS = ["constancia", "equivalencia", "reclamo", "otro"]
PRIORIDADES = ["alta", "media", "baja"]
RESPONSABLES = ["Alumnado", "Bedelia", "Tecnica"]

# Tabla de transiciones: agregar un estado = agregar una fila (Abierto/Cerrado).
TRANSICIONES = {
    ESTADO_PENDIENTE: (ESTADO_EN_PROCESO, ESTADO_RECHAZADA),
    ESTADO_EN_PROCESO: (ESTADO_RESUELTA, ESTADO_RECHAZADA),
}

datos = {"solicitudes": [], "estudiantes": {}, "ultimo_id": 0}
RUTA_DATOS = os.environ.get("SOLICITUDES_DB", "data/solicitudes.json")


class ErrorDeNegocio(Exception):
    """Regla de negocio incumplida. El mensaje es el que ve el usuario."""


@dataclass(frozen=True)
class NuevaSolicitud:
    dni: str
    nombre: str
    email: str
    tipo: str
    prioridad: str
    descripcion: str


@dataclass(frozen=True)
class FiltroBusqueda:
    estado: Optional[str] = None
    tipo: Optional[str] = None
    prioridad: Optional[str] = None

    def acepta(self, solicitud):
        return ((self.estado is None or solicitud["estado"] == self.estado)
                and (self.tipo is None or solicitud["tipo"] == self.tipo)
                and (self.prioridad is None or solicitud["prioridad"] == self.prioridad))


def cargar_datos():
    global datos
    try:
        with open(RUTA_DATOS) as archivo:
            datos = json.load(archivo)
    except (OSError, ValueError):
        pass


def guardar_datos():
    carpeta = os.path.dirname(RUTA_DATOS)
    if carpeta != "" and not os.path.exists(carpeta):
        os.makedirs(carpeta)
    with open(RUTA_DATOS, "w") as archivo:
        json.dump(datos, archivo)


def fecha_de_hoy():
    return os.environ.get("SOLICITUDES_FECHA") or str(datetime.date.today())


def esta_cerrada(solicitud):
    return solicitud["estado"] not in TRANSICIONES


def obtener_solicitud(id_solicitud):
    for solicitud in datos["solicitudes"]:
        if solicitud["id"] == id_solicitud:
            return solicitud
    raise ErrorDeNegocio("no existe la solicitud " + str(id_solicitud))


def validar_nueva_solicitud(nueva):
    if nueva.dni == "" or nueva.nombre == "" or nueva.descripcion == "":
        raise ErrorDeNegocio("datos incompletos")
    if nueva.tipo not in TIPOS:
        raise ErrorDeNegocio("tipo invalido")
    if nueva.prioridad not in PRIORIDADES:
        raise ErrorDeNegocio("prioridad invalida")
    if "@" not in nueva.email:
        raise ErrorDeNegocio("email invalido")


def registrar_solicitud(nueva, fecha=None):
    validar_nueva_solicitud(nueva)
    if nueva.dni not in datos["estudiantes"]:
        datos["estudiantes"][nueva.dni] = {"nombre": nueva.nombre, "email": nueva.email}
    datos["ultimo_id"] = datos["ultimo_id"] + 1
    solicitud = {"id": datos["ultimo_id"], "dni": nueva.dni, "tipo": nueva.tipo,
                 "prioridad": nueva.prioridad, "desc": nueva.descripcion,
                 "estado": ESTADO_PENDIENTE, "resp": None, "fecha": fecha or fecha_de_hoy()}
    datos["solicitudes"].append(solicitud)
    guardar_datos()
    return solicitud["id"]


def cambiar_estado(id_solicitud, nuevo_estado):
    solicitud = obtener_solicitud(id_solicitud)
    if esta_cerrada(solicitud):
        raise ErrorDeNegocio("la solicitud ya esta cerrada")
    if nuevo_estado not in TRANSICIONES[solicitud["estado"]]:
        raise ErrorDeNegocio("transicion invalida " + solicitud["estado"] + " -> " + nuevo_estado)
    solicitud["estado"] = nuevo_estado
    guardar_datos()


def asignar_responsable(id_solicitud, responsable):
    if responsable not in RESPONSABLES:
        raise ErrorDeNegocio("responsable invalido")
    solicitud = obtener_solicitud(id_solicitud)
    if esta_cerrada(solicitud):
        raise ErrorDeNegocio("la solicitud ya esta cerrada")
    solicitud["resp"] = responsable
    guardar_datos()


def buscar_solicitudes(filtro):
    return [s for s in datos["solicitudes"] if filtro.acepta(s)]


def formatear_solicitud(solicitud):
    nombre = datos["estudiantes"][solicitud["dni"]]["nombre"]
    responsable = solicitud["resp"] if solicitud["resp"] is not None else "-"
    return " | ".join(["#" + str(solicitud["id"]), solicitud["fecha"], nombre, solicitud["tipo"],
                       solicitud["prioridad"], solicitud["estado"], responsable])


def contar_por(campo, valores):
    return [(valor, len([s for s in datos["solicitudes"] if s[campo] == valor]))
            for valor in valores]


def contar_abiertas_sin_responsable():
    return len([s for s in datos["solicitudes"] if s["resp"] is None and not esta_cerrada(s)])


def generar_reporte():
    lineas = ["=== REPORTE ===", "Total: " + str(len(datos["solicitudes"]))]
    for titulo, campo, valores in (("Por estado", "estado", ESTADOS), ("Por tipo", "tipo", TIPOS),
                                   ("Por prioridad", "prioridad", PRIORIDADES)):
        lineas.append("-- " + titulo + " --")
        for valor, cantidad in contar_por(campo, valores):
            lineas.append(valor + ": " + str(cantidad))
    lineas.append("Sin responsable (abiertas): " + str(contar_abiertas_sin_responsable()))
    return lineas


def leer_filtro(argumentos):
    valores = {}
    for argumento in argumentos:
        for campo in ("estado", "tipo", "prioridad"):
            prefijo = "--" + campo + "="
            if argumento.startswith(prefijo):
                valores[campo] = argumento[len(prefijo):]
    return FiltroBusqueda(**valores)


def ejecutar_comando(argumentos):
    """Interpreta los argumentos y devuelve las lineas a mostrar. Lanza ErrorDeNegocio."""
    if len(argumentos) < 2:
        return ["Uso: main.py <registrar|estado|asignar|buscar|reporte> ..."]
    comando = argumentos[1]
    if comando == "registrar":
        if len(argumentos) < 8:
            raise ErrorDeNegocio("faltan argumentos")
        id_nueva = registrar_solicitud(NuevaSolicitud(*argumentos[2:8]))
        return ["OK: solicitud " + str(id_nueva) + " registrada"]
    if comando == "estado":
        try:
            id_solicitud, nuevo_estado = int(argumentos[2]), argumentos[3]
        except (IndexError, ValueError):
            raise ErrorDeNegocio("argumentos invalidos")
        cambiar_estado(id_solicitud, nuevo_estado)
        return ["OK: solicitud " + str(id_solicitud) + " ahora " + nuevo_estado]
    if comando == "asignar":
        try:
            id_solicitud, responsable = int(argumentos[2]), argumentos[3]
        except (IndexError, ValueError):
            raise ErrorDeNegocio("argumentos invalidos")
        asignar_responsable(id_solicitud, responsable)
        return ["OK: solicitud " + str(id_solicitud) + " asignada a " + responsable]
    if comando == "buscar":
        encontradas = buscar_solicitudes(leer_filtro(argumentos[2:]))
        resumen = str(len(encontradas)) + " resultado(s)"
        return [formatear_solicitud(s) for s in encontradas] + [resumen]
    if comando == "reporte":
        return generar_reporte()
    raise ErrorDeNegocio("comando desconocido " + comando)


def main():
    cargar_datos()
    try:
        lineas = ejecutar_comando(sys.argv)
    except ErrorDeNegocio as error:
        lineas = ["ERROR: " + str(error)]
    for linea in lineas:
        print(linea)


main()
