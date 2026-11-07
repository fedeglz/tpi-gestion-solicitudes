"""Persistencia. Unico modulo que conoce el formato JSON y el sistema de archivos."""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Protocol

from .dominio import Area, Estado, Estudiante, Prioridad, Solicitud, Tipo


class ErrorDeDatos(Exception):
    """El archivo de datos existe pero no se puede interpretar."""


@dataclass
class Almacen:
    """Estado completo que se carga y se guarda de una sola vez."""
    solicitudes: List[Solicitud] = field(default_factory=list)
    estudiantes: Dict[str, Estudiante] = field(default_factory=dict)
    ultimo_id: int = 0


class Repositorio(Protocol):
    """Abstraccion de la que depende el servicio (DIP)."""
    def cargar(self) -> Almacen: ...
    def guardar(self, almacen: Almacen) -> None: ...


class RepositorioJSON:
    def __init__(self, ruta):
        self._ruta = ruta

    def cargar(self):
        if not os.path.exists(self._ruta):
            return Almacen()
        try:
            with open(self._ruta, encoding="utf-8") as archivo:
                crudo = json.load(archivo)
            return Almacen(
                solicitudes=[self._a_solicitud(s) for s in crudo["solicitudes"]],
                estudiantes={dni: Estudiante(dni, e["nombre"], e["email"])
                             for dni, e in crudo["estudiantes"].items()},
                ultimo_id=crudo["ultimo_id"])
        except (OSError, ValueError, KeyError, TypeError) as causa:
            # Antes se ignoraba en silencio y el siguiente guardado PISABA los datos.
            raise ErrorDeDatos("archivo de datos corrupto: %s" % self._ruta) from causa

    def guardar(self, almacen):
        carpeta = os.path.dirname(self._ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        crudo = {
            "solicitudes": [self._a_dict(s) for s in almacen.solicitudes],
            "estudiantes": {dni: {"nombre": e.nombre, "email": e.email}
                            for dni, e in almacen.estudiantes.items()},
            "ultimo_id": almacen.ultimo_id}
        with open(self._ruta, "w", encoding="utf-8") as archivo:
            json.dump(crudo, archivo)

    @staticmethod
    def _a_dict(s):
        return {"id": s.id, "dni": s.dni, "tipo": s.tipo.value, "prioridad": s.prioridad.value,
                "desc": s.descripcion, "estado": s.estado.value,
                "resp": s.responsable.value if s.responsable else None, "fecha": s.fecha}

    @staticmethod
    def _a_solicitud(d):
        return Solicitud(id=d["id"], dni=d["dni"], tipo=Tipo(d["tipo"]),
                         prioridad=Prioridad(d["prioridad"]), descripcion=d["desc"],
                         fecha=d["fecha"], estado=Estado(d["estado"]),
                         responsable=Area(d["resp"]) if d["resp"] else None)
