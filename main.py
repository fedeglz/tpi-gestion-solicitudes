# Sistema de Gestion de Solicitudes Academicas
# R3: Introduce Parameter Object (NuevaSolicitud, FiltroBusqueda)
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
ESTADOS_CERRADOS = (ESTADO_RESUELTA, ESTADO_RECHAZADA)
TIPOS = ["constancia", "equivalencia", "reclamo", "otro"]
PRIORIDADES = ["alta", "media", "baja"]
RESPONSABLES = ["Alumnado", "Bedelia", "Tecnica"]

datos = {"solicitudes": [], "estudiantes": {}, "ultimo_id": 0}
RUTA_DATOS = os.environ.get("SOLICITUDES_DB", "data/solicitudes.json")


@dataclass(frozen=True)
class NuevaSolicitud:
    """Agrupa los datos de alta que antes viajaban como 6 parametros sueltos."""
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
    return solicitud["estado"] in ESTADOS_CERRADOS


def obtener_solicitud(id_solicitud):
    for solicitud in datos["solicitudes"]:
        if solicitud["id"] == id_solicitud:
            return solicitud
    return None


def validar_nueva_solicitud(nueva):
    """Devuelve el mensaje de error o None si los datos son validos."""
    if nueva.dni == "" or nueva.nombre == "" or nueva.descripcion == "":
        return "datos incompletos"
    if nueva.tipo not in TIPOS:
        return "tipo invalido"
    if nueva.prioridad not in PRIORIDADES:
        return "prioridad invalida"
    if "@" not in nueva.email:
        return "email invalido"
    return None


def registrar_solicitud(nueva, fecha=None):
    error = validar_nueva_solicitud(nueva)
    if error is not None:
        print("ERROR: " + error)
        return -1
    if nueva.dni not in datos["estudiantes"]:
        datos["estudiantes"][nueva.dni] = {"nombre": nueva.nombre, "email": nueva.email}
    datos["ultimo_id"] = datos["ultimo_id"] + 1
    solicitud = {"id": datos["ultimo_id"], "dni": nueva.dni, "tipo": nueva.tipo,
                 "prioridad": nueva.prioridad, "desc": nueva.descripcion,
                 "estado": ESTADO_PENDIENTE, "resp": None, "fecha": fecha or fecha_de_hoy()}
    datos["solicitudes"].append(solicitud)
    guardar_datos()
    print("OK: solicitud " + str(solicitud["id"]) + " registrada")
    return solicitud["id"]


def transicion_permitida(estado_actual, nuevo_estado):
    if estado_actual == ESTADO_PENDIENTE:
        return nuevo_estado in (ESTADO_EN_PROCESO, ESTADO_RECHAZADA)
    if estado_actual == ESTADO_EN_PROCESO:
        return nuevo_estado in (ESTADO_RESUELTA, ESTADO_RECHAZADA)
    return False


def cambiar_estado(id_solicitud, nuevo_estado):
    solicitud = obtener_solicitud(id_solicitud)
    if solicitud is None:
        print("ERROR: no existe la solicitud " + str(id_solicitud))
        return False
    if esta_cerrada(solicitud):
        print("ERROR: la solicitud ya esta cerrada")
        return False
    if not transicion_permitida(solicitud["estado"], nuevo_estado):
        print("ERROR: transicion invalida " + solicitud["estado"] + " -> " + nuevo_estado)
        return False
    solicitud["estado"] = nuevo_estado
    guardar_datos()
    print("OK: solicitud " + str(id_solicitud) + " ahora " + nuevo_estado)
    return True


def asignar_responsable(id_solicitud, responsable):
    if responsable not in RESPONSABLES:
        print("ERROR: responsable invalido")
        return False
    solicitud = obtener_solicitud(id_solicitud)
    if solicitud is None:
        print("ERROR: no existe la solicitud " + str(id_solicitud))
        return False
    if esta_cerrada(solicitud):
        print("ERROR: la solicitud ya esta cerrada")
        return False
    solicitud["resp"] = responsable
    guardar_datos()
    print("OK: solicitud " + str(id_solicitud) + " asignada a " + responsable)
    return True


def formatear_solicitud(solicitud):
    nombre = datos["estudiantes"][solicitud["dni"]]["nombre"]
    responsable = solicitud["resp"] if solicitud["resp"] is not None else "-"
    return " | ".join(["#" + str(solicitud["id"]), solicitud["fecha"], nombre, solicitud["tipo"],
                       solicitud["prioridad"], solicitud["estado"], responsable])


def buscar_solicitudes(filtro):
    encontradas = [s for s in datos["solicitudes"] if filtro.acepta(s)]
    for solicitud in encontradas:
        print(formatear_solicitud(solicitud))
    print(str(len(encontradas)) + " resultado(s)")
    return encontradas


def imprimir_conteo(titulo, campo, valores):
    print("-- " + titulo + " --")
    for valor in valores:
        cantidad = len([s for s in datos["solicitudes"] if s[campo] == valor])
        print(valor + ": " + str(cantidad))


def contar_abiertas_sin_responsable():
    return len([s for s in datos["solicitudes"] if s["resp"] is None and not esta_cerrada(s)])


def imprimir_reporte():
    print("=== REPORTE ===")
    print("Total: " + str(len(datos["solicitudes"])))
    imprimir_conteo("Por estado", "estado", ESTADOS)
    imprimir_conteo("Por tipo", "tipo", TIPOS)
    imprimir_conteo("Por prioridad", "prioridad", PRIORIDADES)
    print("Sin responsable (abiertas): " + str(contar_abiertas_sin_responsable()))


def leer_filtro(argumentos):
    valores = {}
    for argumento in argumentos:
        for campo in ("estado", "tipo", "prioridad"):
            prefijo = "--" + campo + "="
            if argumento.startswith(prefijo):
                valores[campo] = argumento[len(prefijo):]
    return FiltroBusqueda(**valores)


def main():
    cargar_datos()
    argumentos = sys.argv
    if len(argumentos) < 2:
        print("Uso: main.py <registrar|estado|asignar|buscar|reporte> ...")
        return
    comando = argumentos[1]
    if comando == "registrar":
        if len(argumentos) < 8:
            print("ERROR: faltan argumentos")
            return
        registrar_solicitud(NuevaSolicitud(*argumentos[2:8]))
    elif comando == "estado":
        try:
            cambiar_estado(int(argumentos[2]), argumentos[3])
        except (IndexError, ValueError):
            print("ERROR: argumentos invalidos")
    elif comando == "asignar":
        try:
            asignar_responsable(int(argumentos[2]), argumentos[3])
        except (IndexError, ValueError):
            print("ERROR: argumentos invalidos")
    elif comando == "buscar":
        buscar_solicitudes(leer_filtro(argumentos[2:]))
    elif comando == "reporte":
        imprimir_reporte()
    else:
        print("ERROR: comando desconocido " + comando)


main()
