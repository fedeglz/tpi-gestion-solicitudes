"""Modelo de dominio y reglas de negocio. No conoce archivos ni consola."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorDeNegocio(Exception):
    """Regla de negocio incumplida. El mensaje es el que ve el usuario."""


class Estado(Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    RESUELTA = "Resuelta"
    RECHAZADA = "Rechazada"


class Tipo(Enum):
    CONSTANCIA = "constancia"
    EQUIVALENCIA = "equivalencia"
    RECLAMO = "reclamo"
    OTRO = "otro"


class Prioridad(Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Area(Enum):
    ALUMNADO = "Alumnado"
    BEDELIA = "Bedelia"
    TECNICA = "Tecnica"


# Abierto/Cerrado (OCP): un estado nuevo se agrega aqui, sin tocar la logica.
TRANSICIONES = {
    Estado.PENDIENTE: (Estado.EN_PROCESO, Estado.RECHAZADA),
    Estado.EN_PROCESO: (Estado.RESUELTA, Estado.RECHAZADA),
}


def interpretar(enum_clase, texto, mensaje_error):
    """Convierte texto a miembro del Enum o lanza ErrorDeNegocio."""
    for miembro in enum_clase:
        if miembro.value == texto:
            return miembro
    raise ErrorDeNegocio(mensaje_error)


@dataclass(frozen=True)
class Estudiante:
    dni: str
    nombre: str
    email: str


@dataclass(frozen=True)
class NuevaSolicitud:
    """Parameter Object con los datos de alta (texto crudo, aun sin validar)."""
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


@dataclass
class Solicitud:
    id: int
    dni: str
    tipo: Tipo
    prioridad: Prioridad
    descripcion: str
    fecha: str
    estado: Estado = Estado.PENDIENTE
    responsable: Optional[Area] = None

    @property
    def esta_cerrada(self):
        return self.estado not in TRANSICIONES

    def cumple(self, filtro):
        return ((filtro.estado is None or self.estado.value == filtro.estado)
                and (filtro.tipo is None or self.tipo.value == filtro.tipo)
                and (filtro.prioridad is None or self.prioridad.value == filtro.prioridad))

    def cambiar_estado(self, destino):
        if self.esta_cerrada:
            raise ErrorDeNegocio("la solicitud ya esta cerrada")
        if destino not in [e.value for e in TRANSICIONES[self.estado]]:
            raise ErrorDeNegocio("transicion invalida %s -> %s" % (self.estado.value, destino))
        self.estado = interpretar(Estado, destino, "estado invalido")

    def asignar(self, area):
        if self.esta_cerrada:
            raise ErrorDeNegocio("la solicitud ya esta cerrada")
        self.responsable = area


def validar_nueva_solicitud(nueva):
    """Devuelve (Tipo, Prioridad) validados; lanza ErrorDeNegocio si hay datos invalidos."""
    if nueva.dni == "" or nueva.nombre == "" or nueva.descripcion == "":
        raise ErrorDeNegocio("datos incompletos")
    tipo = interpretar(Tipo, nueva.tipo, "tipo invalido")
    prioridad = interpretar(Prioridad, nueva.prioridad, "prioridad invalida")
    if "@" not in nueva.email:
        raise ErrorDeNegocio("email invalido")
    return tipo, prioridad
