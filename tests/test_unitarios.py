"""Pruebas unitarias de la version refactorizada (dominio, servicio, reporte, repositorio).

El servicio se prueba con un repositorio EN MEMORIA: gracias a la inyeccion de
dependencias (DIP) no hace falta tocar el disco.
"""
import json
import os
import tempfile
import unittest

from gestion_solicitudes import reporte
from gestion_solicitudes.dominio import (Area, ErrorDeNegocio, Estado, FiltroBusqueda,
                                         NuevaSolicitud, Prioridad, Solicitud, Tipo)
from gestion_solicitudes.repositorio import Almacen, RepositorioJSON
from gestion_solicitudes.servicio import ServicioSolicitudes


class RepositorioEnMemoria:
    def __init__(self):
        self.almacen = Almacen()
        self.guardados = 0

    def cargar(self):
        return self.almacen

    def guardar(self, almacen):
        self.almacen = almacen
        self.guardados += 1


def nueva(**cambios):
    datos = dict(dni="30111222", nombre="Ana Perez", email="ana@mail.com",
                 tipo="constancia", prioridad="alta", descripcion="Constancia")
    datos.update(cambios)
    return NuevaSolicitud(**datos)


def servicio():
    repo = RepositorioEnMemoria()
    return ServicioSolicitudes(repo, lambda: "2026-03-10"), repo


class TestSolicitudDominio(unittest.TestCase):
    def solicitud(self, estado=Estado.PENDIENTE):
        return Solicitud(1, "1", Tipo.OTRO, Prioridad.BAJA, "x", "2026-03-10", estado)

    def test_flujo_valido(self):
        s = self.solicitud()
        s.cambiar_estado("En proceso")
        s.cambiar_estado("Resuelta")
        self.assertEqual(s.estado, Estado.RESUELTA)
        self.assertTrue(s.esta_cerrada)

    def test_transicion_invalida(self):
        with self.assertRaisesRegex(ErrorDeNegocio, "transicion invalida Pendiente -> Resuelta"):
            self.solicitud().cambiar_estado("Resuelta")

    def test_cerrada_no_cambia_ni_se_asigna(self):
        s = self.solicitud(Estado.RECHAZADA)
        with self.assertRaisesRegex(ErrorDeNegocio, "cerrada"):
            s.cambiar_estado("En proceso")
        with self.assertRaisesRegex(ErrorDeNegocio, "cerrada"):
            s.asignar(Area.BEDELIA)

    def test_cumple_filtro(self):
        s = self.solicitud()
        self.assertTrue(s.cumple(FiltroBusqueda()))
        self.assertTrue(s.cumple(FiltroBusqueda(estado="Pendiente", tipo="otro")))
        self.assertFalse(s.cumple(FiltroBusqueda(prioridad="alta")))


class TestServicio(unittest.TestCase):
    def test_registrar_asigna_id_fecha_y_persiste(self):
        svc, repo = servicio()
        self.assertEqual(svc.registrar(nueva()), 1)
        self.assertEqual(svc.registrar(nueva(tipo="otro")), 2)
        self.assertEqual(repo.guardados, 2)
        self.assertEqual(repo.almacen.solicitudes[0].fecha, "2026-03-10")

    def test_registrar_invalido_no_persiste(self):
        svc, repo = servicio()
        for datos in (dict(nombre=""), dict(tipo="beca"), dict(prioridad="x"), dict(email="x")):
            with self.assertRaises(ErrorDeNegocio):
                svc.registrar(nueva(**datos))
        self.assertEqual(repo.guardados, 0)

    def test_asignar_y_cambiar_estado(self):
        svc, repo = servicio()
        svc.registrar(nueva())
        svc.asignar_responsable(1, "Bedelia")
        svc.cambiar_estado(1, "En proceso")
        s = repo.almacen.solicitudes[0]
        self.assertEqual((s.responsable, s.estado), (Area.BEDELIA, Estado.EN_PROCESO))

    def test_errores_de_busqueda_y_area(self):
        svc, _ = servicio()
        with self.assertRaisesRegex(ErrorDeNegocio, "no existe la solicitud 5"):
            svc.cambiar_estado(5, "En proceso")
        with self.assertRaisesRegex(ErrorDeNegocio, "responsable invalido"):
            svc.asignar_responsable(5, "Rectorado")

    def test_buscar_con_filtros(self):
        svc, _ = servicio()
        svc.registrar(nueva())
        svc.registrar(nueva(tipo="reclamo", prioridad="baja"))
        self.assertEqual(len(svc.buscar(FiltroBusqueda())), 2)
        self.assertEqual([s.id for s in svc.buscar(FiltroBusqueda(tipo="reclamo"))], [2])


class TestReporte(unittest.TestCase):
    def test_formato_de_fila(self):
        s = Solicitud(7, "1", Tipo.RECLAMO, Prioridad.MEDIA, "x", "2026-03-10",
                      Estado.EN_PROCESO, Area.TECNICA)
        self.assertEqual(reporte.formatear_solicitud(s, "Luis"),
                         "#7 | 2026-03-10 | Luis | reclamo | media | En proceso | Tecnica")

    def test_reporte_cuenta_abiertas_sin_responsable(self):
        svc, _ = servicio()
        svc.registrar(nueva())
        svc.registrar(nueva(tipo="otro"))
        svc.asignar_responsable(2, "Bedelia")
        lineas = reporte.generar_reporte(svc.todas())
        self.assertIn("Total: 2", lineas)
        self.assertEqual(lineas[-1], "Sin responsable (abiertas): 1")


class TestRepositorioJSON(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ruta = os.path.join(self._tmp.name, "sub", "datos.json")

    def test_archivo_inexistente_devuelve_almacen_vacio(self):
        self.assertEqual(RepositorioJSON(self.ruta).cargar().ultimo_id, 0)

    def test_guardar_y_cargar_ida_y_vuelta(self):
        svc = ServicioSolicitudes(RepositorioJSON(self.ruta), lambda: "2026-03-10")
        svc.registrar(nueva())
        svc.asignar_responsable(1, "Tecnica")
        recargado = ServicioSolicitudes(RepositorioJSON(self.ruta), lambda: "x")
        self.assertEqual(recargado.todas()[0].responsable, Area.TECNICA)

    def test_compatibilidad_con_formato_de_la_version_inicial(self):
        os.makedirs(os.path.dirname(self.ruta))
        legado = {"solicitudes": [{"id": 1, "dni": "1", "tipo": "otro", "prioridad": "baja",
                                   "desc": "x", "estado": "Pendiente", "resp": None,
                                   "fecha": "2026-01-01"}],
                  "estudiantes": {"1": {"nombre": "N", "email": "n@m.com"}}, "ultimo_id": 1}
        with open(self.ruta, "w") as f:
            json.dump(legado, f)
        repo = RepositorioJSON(self.ruta)
        repo.guardar(repo.cargar())
        with open(self.ruta) as f:
            self.assertEqual(json.load(f), legado)


if __name__ == "__main__":
    unittest.main()
