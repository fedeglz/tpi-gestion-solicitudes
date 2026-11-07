"""Cambio de comportamiento INTENCIONAL (documentado en docs/decisiones-tecnicas.md).

Version inicial: un JSON corrupto se ignoraba y el siguiente guardado pisaba los
datos. Ahora se informa el error y NO se modifica el archivo.
"""
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestArchivoCorrupto(unittest.TestCase):
    def test_archivo_corrupto_se_informa_y_no_se_pisa(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "solicitudes.json")
            with open(ruta, "w") as f:
                f.write("{esto no es json")
            env = dict(os.environ, SOLICITUDES_DB=ruta)
            r = subprocess.run([sys.executable, "main.py", "registrar", "1", "Ana", "a@m.com",
                                "otro", "alta", "x"], cwd=RAIZ, env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "ERROR: archivo de datos corrupto: " + ruta)
            with open(ruta) as f:
                self.assertEqual(f.read(), "{esto no es json")


if __name__ == "__main__":
    unittest.main()
