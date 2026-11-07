"""Pruebas de caracterizacion (caja negra) del comportamiento externo.

Ejecutan `main.py` como lo haria un usuario y verifican salida y datos
persistidos. Se escribieron sobre la version inicial y deben seguir en verde
despues de CADA refactoring (red de seguridad).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CaracterizacionBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = os.path.join(self._tmp.name, "datos", "solicitudes.json")

    def cli(self, *args):
        env = dict(os.environ, SOLICITUDES_DB=self.db, SOLICITUDES_FECHA="2026-03-10")
        r = subprocess.run([sys.executable, "main.py", *args], cwd=RAIZ, env=env,
                           capture_output=True, text=True)
        return r.stdout.strip().splitlines(), r.returncode

    def datos(self):
        with open(self.db, encoding="utf-8") as f:
            return json.load(f)

    def registrar(self, dni="30111222", nombre="Ana Perez", email="ana@mail.com",
                  tipo="constancia", prioridad="alta", desc="Constancia de alumno regular"):
        return self.cli("registrar", dni, nombre, email, tipo, prioridad, desc)


class TestRegistrar(CaracterizacionBase):
    def test_registro_ok_persiste_datos(self):
        salida, codigo = self.registrar()
        self.assertEqual(salida, ["OK: solicitud 1 registrada"])
        self.assertEqual(codigo, 0)
        d = self.datos()
        self.assertEqual(d["ultimo_id"], 1)
        self.assertEqual(d["estudiantes"]["30111222"], {"nombre": "Ana Perez", "email": "ana@mail.com"})
        self.assertEqual(d["solicitudes"][0], {
            "id": 1, "dni": "30111222", "tipo": "constancia", "prioridad": "alta",
            "desc": "Constancia de alumno regular", "estado": "Pendiente",
            "resp": None, "fecha": "2026-03-10"})

    def test_ids_correlativos(self):
        self.registrar()
        salida, _ = self.registrar(dni="30999888", nombre="Luis Gomez", email="luis@mail.com", tipo="reclamo")
        self.assertEqual(salida, ["OK: solicitud 2 registrada"])

    def test_datos_incompletos(self):
        self.assertEqual(self.registrar(nombre="")[0], ["ERROR: datos incompletos"])
        self.assertEqual(self.registrar(dni="")[0], ["ERROR: datos incompletos"])
        self.assertEqual(self.registrar(desc="")[0], ["ERROR: datos incompletos"])
        self.assertFalse(os.path.exists(self.db))

    def test_tipo_invalido(self):
        self.assertEqual(self.registrar(tipo="beca")[0], ["ERROR: tipo invalido"])

    def test_prioridad_invalida(self):
        self.assertEqual(self.registrar(prioridad="urgente")[0], ["ERROR: prioridad invalida"])

    def test_email_invalido(self):
        self.assertEqual(self.registrar(email="ana.mail.com")[0], ["ERROR: email invalido"])

    def test_orden_de_validaciones(self):
        salida, _ = self.registrar(nombre="", tipo="beca", prioridad="x", email="x")
        self.assertEqual(salida, ["ERROR: datos incompletos"])
        salida, _ = self.registrar(tipo="beca", prioridad="x", email="x")
        self.assertEqual(salida, ["ERROR: tipo invalido"])

    def test_estudiante_existente_conserva_sus_datos(self):
        self.registrar()
        self.registrar(nombre="Otro Nombre", email="otro@mail.com")
        self.assertEqual(self.datos()["estudiantes"]["30111222"]["nombre"], "Ana Perez")

    def test_faltan_argumentos(self):
        salida, _ = self.cli("registrar", "30111222", "Ana")
        self.assertEqual(salida, ["ERROR: faltan argumentos"])


class TestCambiarEstado(CaracterizacionBase):
    def setUp(self):
        super().setUp()
        self.registrar()

    def test_flujo_valido_completo(self):
        self.assertEqual(self.cli("estado", "1", "En proceso")[0], ["OK: solicitud 1 ahora En proceso"])
        self.assertEqual(self.cli("estado", "1", "Resuelta")[0], ["OK: solicitud 1 ahora Resuelta"])
        self.assertEqual(self.datos()["solicitudes"][0]["estado"], "Resuelta")

    def test_pendiente_puede_rechazarse(self):
        self.assertEqual(self.cli("estado", "1", "Rechazada")[0], ["OK: solicitud 1 ahora Rechazada"])

    def test_transicion_invalida_desde_pendiente(self):
        self.assertEqual(self.cli("estado", "1", "Resuelta")[0],
                         ["ERROR: transicion invalida Pendiente -> Resuelta"])
        self.assertEqual(self.datos()["solicitudes"][0]["estado"], "Pendiente")

    def test_transicion_invalida_desde_en_proceso(self):
        self.cli("estado", "1", "En proceso")
        self.assertEqual(self.cli("estado", "1", "Pendiente")[0],
                         ["ERROR: transicion invalida En proceso -> Pendiente"])

    def test_estado_desconocido(self):
        self.assertEqual(self.cli("estado", "1", "Inventado")[0],
                         ["ERROR: transicion invalida Pendiente -> Inventado"])

    def test_solicitud_cerrada(self):
        self.cli("estado", "1", "Rechazada")
        self.assertEqual(self.cli("estado", "1", "En proceso")[0], ["ERROR: la solicitud ya esta cerrada"])

    def test_solicitud_inexistente(self):
        self.assertEqual(self.cli("estado", "99", "En proceso")[0], ["ERROR: no existe la solicitud 99"])

    def test_argumentos_invalidos(self):
        self.assertEqual(self.cli("estado", "abc", "En proceso")[0], ["ERROR: argumentos invalidos"])
        self.assertEqual(self.cli("estado", "1")[0], ["ERROR: argumentos invalidos"])


class TestAsignar(CaracterizacionBase):
    def setUp(self):
        super().setUp()
        self.registrar()

    def test_asignacion_ok(self):
        self.assertEqual(self.cli("asignar", "1", "Bedelia")[0], ["OK: solicitud 1 asignada a Bedelia"])
        self.assertEqual(self.datos()["solicitudes"][0]["resp"], "Bedelia")

    def test_reasignacion(self):
        self.cli("asignar", "1", "Bedelia")
        self.cli("asignar", "1", "Tecnica")
        self.assertEqual(self.datos()["solicitudes"][0]["resp"], "Tecnica")

    def test_responsable_invalido_tiene_prioridad_sobre_inexistente(self):
        self.assertEqual(self.cli("asignar", "99", "Rectorado")[0], ["ERROR: responsable invalido"])

    def test_solicitud_inexistente(self):
        self.assertEqual(self.cli("asignar", "99", "Bedelia")[0], ["ERROR: no existe la solicitud 99"])

    def test_solicitud_cerrada(self):
        self.cli("estado", "1", "Rechazada")
        self.assertEqual(self.cli("asignar", "1", "Bedelia")[0], ["ERROR: la solicitud ya esta cerrada"])

    def test_argumentos_invalidos(self):
        self.assertEqual(self.cli("asignar", "uno", "Bedelia")[0], ["ERROR: argumentos invalidos"])


class TestBuscar(CaracterizacionBase):
    def setUp(self):
        super().setUp()
        self.registrar()
        self.registrar(dni="30999888", nombre="Luis Gomez", email="luis@mail.com",
                       tipo="reclamo", prioridad="media", desc="Reclamo de nota")
        self.registrar(dni="30111222", tipo="equivalencia", prioridad="baja", desc="Equivalencia")
        self.cli("estado", "2", "En proceso")
        self.cli("asignar", "2", "Alumnado")

    def test_sin_filtros_lista_todo(self):
        salida, _ = self.cli("buscar")
        self.assertEqual(salida, [
            "#1 | 2026-03-10 | Ana Perez | constancia | alta | Pendiente | -",
            "#2 | 2026-03-10 | Luis Gomez | reclamo | media | En proceso | Alumnado",
            "#3 | 2026-03-10 | Ana Perez | equivalencia | baja | Pendiente | -",
            "3 resultado(s)"])

    def test_filtro_por_estado(self):
        salida, _ = self.cli("buscar", "--estado=Pendiente")
        self.assertEqual(len(salida), 3)
        self.assertEqual(salida[-1], "2 resultado(s)")

    def test_filtros_combinados(self):
        salida, _ = self.cli("buscar", "--estado=Pendiente", "--tipo=equivalencia")
        self.assertEqual(salida, [
            "#3 | 2026-03-10 | Ana Perez | equivalencia | baja | Pendiente | -",
            "1 resultado(s)"])

    def test_sin_resultados(self):
        self.assertEqual(self.cli("buscar", "--prioridad=alta", "--tipo=reclamo")[0], ["0 resultado(s)"])

    def test_filtro_valor_desconocido_no_falla(self):
        self.assertEqual(self.cli("buscar", "--estado=Inventado")[0], ["0 resultado(s)"])


class TestReporte(CaracterizacionBase):
    def test_reporte_vacio(self):
        salida, _ = self.cli("reporte")
        self.assertEqual(salida[:3], ["=== REPORTE ===", "Total: 0", "-- Por estado --"])
        self.assertEqual(salida[-1], "Sin responsable (abiertas): 0")

    def test_reporte_con_datos(self):
        self.registrar()
        self.registrar(dni="30999888", nombre="Luis Gomez", email="luis@mail.com",
                       tipo="reclamo", prioridad="media", desc="Reclamo")
        self.registrar(tipo="otro", prioridad="baja", desc="Consulta")
        self.cli("estado", "1", "Rechazada")
        self.cli("estado", "2", "En proceso")
        self.cli("asignar", "2", "Bedelia")
        salida, _ = self.cli("reporte")
        self.assertEqual(salida, [
            "=== REPORTE ===", "Total: 3",
            "-- Por estado --", "Pendiente: 1", "En proceso: 1", "Resuelta: 0", "Rechazada: 1",
            "-- Por tipo --", "constancia: 1", "equivalencia: 0", "reclamo: 1", "otro: 1",
            "-- Por prioridad --", "alta: 1", "media: 1", "baja: 1",
            "Sin responsable (abiertas): 1"])


class TestCLI(CaracterizacionBase):
    def test_sin_comando_muestra_uso(self):
        salida, codigo = self.cli()
        self.assertEqual(salida, ["Uso: main.py <registrar|estado|asignar|buscar|reporte> ..."])
        self.assertEqual(codigo, 0)

    def test_comando_desconocido(self):
        self.assertEqual(self.cli("borrar")[0], ["ERROR: comando desconocido borrar"])

    def test_errores_no_modifican_datos(self):
        self.registrar()
        antes = self.datos()
        self.cli("estado", "1", "Resuelta")
        self.cli("asignar", "1", "Rectorado")
        self.assertEqual(self.datos(), antes)


if __name__ == "__main__":
    unittest.main()
