"""Casos de uso. Orquesta dominio + repositorio; no imprime ni lee argumentos."""
from .dominio import (Area, ErrorDeNegocio, Estudiante, Solicitud,
                      interpretar, validar_nueva_solicitud)


class ServicioSolicitudes:
    def __init__(self, repositorio, reloj):
        self._repositorio = repositorio   # inyectado (DIP)
        self._reloj = reloj               # inyectado: permite fijar la fecha en pruebas
        self._almacen = repositorio.cargar()

    def registrar(self, nueva):
        tipo, prioridad = validar_nueva_solicitud(nueva)
        self._almacen.estudiantes.setdefault(
            nueva.dni, Estudiante(nueva.dni, nueva.nombre, nueva.email))
        self._almacen.ultimo_id += 1
        solicitud = Solicitud(id=self._almacen.ultimo_id, dni=nueva.dni, tipo=tipo,
                              prioridad=prioridad, descripcion=nueva.descripcion,
                              fecha=self._reloj())
        self._almacen.solicitudes.append(solicitud)
        self._repositorio.guardar(self._almacen)
        return solicitud.id

    def cambiar_estado(self, id_solicitud, destino):
        solicitud = self._obtener(id_solicitud)
        solicitud.cambiar_estado(destino)
        self._repositorio.guardar(self._almacen)

    def asignar_responsable(self, id_solicitud, area_texto):
        area = interpretar(Area, area_texto, "responsable invalido")
        solicitud = self._obtener(id_solicitud)
        solicitud.asignar(area)
        self._repositorio.guardar(self._almacen)

    def buscar(self, filtro):
        return [s for s in self._almacen.solicitudes if s.cumple(filtro)]

    def nombre_de(self, dni):
        return self._almacen.estudiantes[dni].nombre

    def todas(self):
        return list(self._almacen.solicitudes)

    def _obtener(self, id_solicitud):
        for solicitud in self._almacen.solicitudes:
            if solicitud.id == id_solicitud:
                return solicitud
        raise ErrorDeNegocio("no existe la solicitud %s" % id_solicitud)
