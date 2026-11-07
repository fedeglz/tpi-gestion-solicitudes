# Sistema de Gestion de Solicitudes Academicas
# R1: constantes con nombre en lugar de strings magicos + nombres descriptivos
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


def registrar_solicitud(dni, nombre, email, tipo, prioridad, descripcion, fecha=None):
    if dni == "" or nombre == "" or descripcion == "":
        print("ERROR: datos incompletos")
        return -1
    if tipo not in TIPOS:
        print("ERROR: tipo invalido")
        return -1
    if prioridad not in PRIORIDADES:
        print("ERROR: prioridad invalida")
        return -1
    if "@" not in email:
        print("ERROR: email invalido")
        return -1
    if dni not in datos["estudiantes"]:
        datos["estudiantes"][dni] = {"nombre": nombre, "email": email}
    datos["ultimo_id"] = datos["ultimo_id"] + 1
    if fecha is None:
        fecha = os.environ.get("SOLICITUDES_FECHA") or str(datetime.date.today())
    solicitud = {"id": datos["ultimo_id"], "dni": dni, "tipo": tipo, "prioridad": prioridad,
                 "desc": descripcion, "estado": ESTADO_PENDIENTE, "resp": None, "fecha": fecha}
    datos["solicitudes"].append(solicitud)
    guardar_datos()
    print("OK: solicitud " + str(solicitud["id"]) + " registrada")
    return solicitud["id"]


def cambiar_estado(id_solicitud, nuevo_estado):
    solicitud = None
    for candidata in datos["solicitudes"]:
        if candidata["id"] == id_solicitud:
            solicitud = candidata
    if solicitud is None:
        print("ERROR: no existe la solicitud " + str(id_solicitud))
        return False
    if solicitud["estado"] == ESTADO_PENDIENTE:
        if nuevo_estado == ESTADO_EN_PROCESO or nuevo_estado == ESTADO_RECHAZADA:
            solicitud["estado"] = nuevo_estado
        else:
            print("ERROR: transicion invalida " + ESTADO_PENDIENTE + " -> " + nuevo_estado)
            return False
    elif solicitud["estado"] == ESTADO_EN_PROCESO:
        if nuevo_estado == ESTADO_RESUELTA or nuevo_estado == ESTADO_RECHAZADA:
            solicitud["estado"] = nuevo_estado
        else:
            print("ERROR: transicion invalida " + ESTADO_EN_PROCESO + " -> " + nuevo_estado)
            return False
    else:
        print("ERROR: la solicitud ya esta cerrada")
        return False
    guardar_datos()
    print("OK: solicitud " + str(id_solicitud) + " ahora " + nuevo_estado)
    return True


def asignar_responsable(id_solicitud, responsable):
    if responsable not in RESPONSABLES:
        print("ERROR: responsable invalido")
        return False
    solicitud = None
    for candidata in datos["solicitudes"]:
        if candidata["id"] == id_solicitud:
            solicitud = candidata
    if solicitud is None:
        print("ERROR: no existe la solicitud " + str(id_solicitud))
        return False
    if solicitud["estado"] in ESTADOS_CERRADOS:
        print("ERROR: la solicitud ya esta cerrada")
        return False
    solicitud["resp"] = responsable
    guardar_datos()
    print("OK: solicitud " + str(id_solicitud) + " asignada a " + responsable)
    return True


def buscar_solicitudes(estado=None, tipo=None, prioridad=None):
    encontradas = []
    for solicitud in datos["solicitudes"]:
        cumple = True
        if estado is not None and solicitud["estado"] != estado:
            cumple = False
        if tipo is not None and solicitud["tipo"] != tipo:
            cumple = False
        if prioridad is not None and solicitud["prioridad"] != prioridad:
            cumple = False
        if cumple:
            encontradas.append(solicitud)
    for solicitud in encontradas:
        nombre = datos["estudiantes"][solicitud["dni"]]["nombre"]
        responsable = "-"
        if solicitud["resp"] is not None:
            responsable = solicitud["resp"]
        print("#" + str(solicitud["id"]) + " | " + solicitud["fecha"] + " | " + nombre + " | "
              + solicitud["tipo"] + " | " + solicitud["prioridad"] + " | " + solicitud["estado"]
              + " | " + responsable)
    print(str(len(encontradas)) + " resultado(s)")
    return encontradas


def imprimir_reporte():
    print("=== REPORTE ===")
    print("Total: " + str(len(datos["solicitudes"])))
    print("-- Por estado --")
    for estado in ESTADOS:
        cantidad = 0
        for solicitud in datos["solicitudes"]:
            if solicitud["estado"] == estado:
                cantidad = cantidad + 1
        print(estado + ": " + str(cantidad))
    print("-- Por tipo --")
    for tipo in TIPOS:
        cantidad = 0
        for solicitud in datos["solicitudes"]:
            if solicitud["tipo"] == tipo:
                cantidad = cantidad + 1
        print(tipo + ": " + str(cantidad))
    print("-- Por prioridad --")
    for prioridad in PRIORIDADES:
        cantidad = 0
        for solicitud in datos["solicitudes"]:
            if solicitud["prioridad"] == prioridad:
                cantidad = cantidad + 1
        print(prioridad + ": " + str(cantidad))
    sin_responsable = 0
    for solicitud in datos["solicitudes"]:
        if solicitud["resp"] is None and solicitud["estado"] not in ESTADOS_CERRADOS:
            sin_responsable = sin_responsable + 1
    print("Sin responsable (abiertas): " + str(sin_responsable))


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
        estado = tipo = prioridad = None
        for argumento in argumentos[2:]:
            if argumento.startswith("--estado="):
                estado = argumento[len("--estado="):]
            if argumento.startswith("--tipo="):
                tipo = argumento[len("--tipo="):]
            if argumento.startswith("--prioridad="):
                prioridad = argumento[len("--prioridad="):]
        buscar_solicitudes(estado, tipo, prioridad)
    elif comando == "reporte":
        imprimir_reporte()
    else:
        print("ERROR: comando desconocido " + comando)


main()
