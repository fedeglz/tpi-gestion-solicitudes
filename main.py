# Sistema de Gestion de Solicitudes Academicas - version inicial
import sys
import json
import os
import datetime

DB = {"solicitudes": [], "estudiantes": {}, "ultimo_id": 0}
RUTA = os.environ.get("SOLICITUDES_DB", "data/solicitudes.json")
# RUTA = "C:/Users/fede/Desktop/solicitudes.json"
# TODO: agregar mas tipos de solicitud


def cargar():
    global DB
    try:
        f = open(RUTA)
        DB = json.load(f)
        f.close()
    except:
        pass


def guardar():
    carpeta = os.path.dirname(RUTA)
    if carpeta != "" and not os.path.exists(carpeta):
        os.makedirs(carpeta)
    f = open(RUTA, "w")
    json.dump(DB, f)
    f.close()


def reg(dni, n, mail, t, p, d, fecha=None):
    # registra una solicitud nueva
    if dni == "" or n == "" or d == "":
        print("ERROR: datos incompletos")
        return -1
    if t != "constancia" and t != "equivalencia" and t != "reclamo" and t != "otro":
        print("ERROR: tipo invalido")
        return -1
    if p != "baja" and p != "media" and p != "alta":
        print("ERROR: prioridad invalida")
        return -1
    if "@" not in mail:
        print("ERROR: email invalido")
        return -1
    if dni not in DB["estudiantes"]:
        DB["estudiantes"][dni] = {"nombre": n, "email": mail}
    DB["ultimo_id"] = DB["ultimo_id"] + 1
    if fecha == None:
        fecha = os.environ.get("SOLICITUDES_FECHA") or str(datetime.date.today())
    s = {"id": DB["ultimo_id"], "dni": dni, "tipo": t, "prioridad": p,
         "desc": d, "estado": "Pendiente", "resp": None, "fecha": fecha}
    DB["solicitudes"].append(s)
    guardar()
    print("OK: solicitud " + str(s["id"]) + " registrada")
    return s["id"]


def cambiar(i, ne):
    s = None
    for x in DB["solicitudes"]:
        if x["id"] == i:
            s = x
    if s == None:
        print("ERROR: no existe la solicitud " + str(i))
        return False
    if s["estado"] == "Pendiente":
        if ne == "En proceso" or ne == "Rechazada":
            s["estado"] = ne
        else:
            print("ERROR: transicion invalida Pendiente -> " + ne)
            return False
    elif s["estado"] == "En proceso":
        if ne == "Resuelta" or ne == "Rechazada":
            s["estado"] = ne
        else:
            print("ERROR: transicion invalida En proceso -> " + ne)
            return False
    else:
        print("ERROR: la solicitud ya esta cerrada")
        return False
    guardar()
    print("OK: solicitud " + str(i) + " ahora " + ne)
    return True


def asig(i, r):
    if r != "Alumnado" and r != "Bedelia" and r != "Tecnica":
        print("ERROR: responsable invalido")
        return False
    s = None
    for x in DB["solicitudes"]:
        if x["id"] == i:
            s = x
    if s == None:
        print("ERROR: no existe la solicitud " + str(i))
        return False
    if s["estado"] == "Resuelta" or s["estado"] == "Rechazada":
        print("ERROR: la solicitud ya esta cerrada")
        return False
    s["resp"] = r
    guardar()
    print("OK: solicitud " + str(i) + " asignada a " + r)
    return True


def buscar(e=None, t=None, p=None):
    res = []
    for x in DB["solicitudes"]:
        ok = True
        if e != None and x["estado"] != e:
            ok = False
        if t != None and x["tipo"] != t:
            ok = False
        if p != None and x["prioridad"] != p:
            ok = False
        if ok:
            res.append(x)
    for x in res:
        n = DB["estudiantes"][x["dni"]]["nombre"]
        r = "-"
        if x["resp"] != None:
            r = x["resp"]
        print("#" + str(x["id"]) + " | " + x["fecha"] + " | " + n + " | " + x["tipo"]
              + " | " + x["prioridad"] + " | " + x["estado"] + " | " + r)
    print(str(len(res)) + " resultado(s)")
    return res


def rep():
    print("=== REPORTE ===")
    print("Total: " + str(len(DB["solicitudes"])))
    print("-- Por estado --")
    for e in ["Pendiente", "En proceso", "Resuelta", "Rechazada"]:
        n = 0
        for x in DB["solicitudes"]:
            if x["estado"] == e:
                n = n + 1
        print(e + ": " + str(n))
    print("-- Por tipo --")
    for t in ["constancia", "equivalencia", "reclamo", "otro"]:
        n = 0
        for x in DB["solicitudes"]:
            if x["tipo"] == t:
                n = n + 1
        print(t + ": " + str(n))
    print("-- Por prioridad --")
    for p in ["alta", "media", "baja"]:
        n = 0
        for x in DB["solicitudes"]:
            if x["prioridad"] == p:
                n = n + 1
        print(p + ": " + str(n))
    sin = 0
    for x in DB["solicitudes"]:
        if x["resp"] == None:
            if x["estado"] != "Resuelta" and x["estado"] != "Rechazada":
                sin = sin + 1
    print("Sin responsable (abiertas): " + str(sin))


def main():
    cargar()
    a = sys.argv
    if len(a) < 2:
        print("Uso: main.py <registrar|estado|asignar|buscar|reporte> ...")
        return
    c = a[1]
    if c == "registrar":
        if len(a) < 8:
            print("ERROR: faltan argumentos")
            return
        reg(a[2], a[3], a[4], a[5], a[6], a[7])
    elif c == "estado":
        try:
            cambiar(int(a[2]), a[3])
        except:
            print("ERROR: argumentos invalidos")
    elif c == "asignar":
        try:
            asig(int(a[2]), a[3])
        except:
            print("ERROR: argumentos invalidos")
    elif c == "buscar":
        e = None
        t = None
        p = None
        for k in range(2, len(a)):
            if a[k].startswith("--estado="):
                e = a[k][9:]
            if a[k].startswith("--tipo="):
                t = a[k][7:]
            if a[k].startswith("--prioridad="):
                p = a[k][12:]
        buscar(e, t, p)
    elif c == "reporte":
        rep()
    else:
        print("ERROR: comando desconocido " + c)


main()
