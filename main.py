# Sistema de Gestion de Solicitudes Academicas
# R2: Extract Method (busqueda por id, validacion, filtrado, formato, conteo)
import sys
import json
import os
import datetime

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


def validar_nueva_solicitud(dni, nombre, email, tipo, prioridad, descripcion):
    """Devuelve el mensaje de error o None si los datos son validos."""
    if dni == "" or nombre == "" or descripcion == "":
        return "datos incompletos"
    if tipo not in TIPOS:
        return "tipo invalido"
    if prioridad not in PRIORIDADES:
        return "prioridad invalida"
    if "@" not in email:
        return "email invalido"
    return None


def registrar_solicitud(dni, nombre, email, tipo, prioridad, descripcion, fecha=None):
    error = validar_nueva_solicitud(dni, nombre, email, tipo, prioridad, descripcion)
    if error is not None:
        print("ERROR: " + error)
        return -1
    if dni not in datos["estudiantes"]:
        datos["estudiantes"][dni] = {"nombre": nombre, "email": email}
    datos["ultimo_id"] = datos["ultimo_id"] + 1
    solicitud = {"id": datos["ultimo_id"], "dni": dni, "tipo": tipo, "prioridad": prioridad,
                 "desc": descripcion, "estado": ESTADO_PENDIENTE, "resp": None,
                 "fecha": fecha or fecha_de_hoy()}
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


def cumple_filtros(solicitud, estado, tipo, prioridad):
    return ((estado is None or solicitud["estado"] == estado)
            and (tipo is None or solicitud["tipo"] == tipo)
            and (prioridad is None or solicitud["prioridad"] == prioridad))


def formatear_solicitud(solicitud):
    nombre = datos["estudiantes"][solicitud["dni"]]["nombre"]
    responsable = solicitud["resp"] if solicitud["resp"] is not None else "-"
    return " | ".join(["#" + str(solicitud["id"]), solicitud["fecha"], nombre, solicitud["tipo"],
                       solicitud["prioridad"], solicitud["estado"], responsable])


def buscar_solicitudes(estado=None, tipo=None, prioridad=None):
    encontradas = [s for s in datos["solicitudes"] if cumple_filtros(s, estado, tipo, prioridad)]
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


def leer_filtros(argumentos):
    filtros = {"--estado=": None, "--tipo=": None, "--prioridad=": None}
    for argumento in argumentos:
        for prefijo in filtros:
            if argumento.startswith(prefijo):
                filtros[prefijo] = argumento[len(prefijo):]
    return filtros["--estado="], filtros["--tipo="], filtros["--prioridad="]


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
        registrar_solicitud(*argumentos[2:8])
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
        buscar_solicitudes(*leer_filtros(argumentos[2:]))
    elif comando == "reporte":
        imprimir_reporte()
    else:
        print("ERROR: comando desconocido " + comando)


main()
