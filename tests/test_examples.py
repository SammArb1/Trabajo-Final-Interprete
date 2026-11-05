# PRUEBAS DE LOS PROGRAMAS DE EJEMPLO: cada examples/*.src debe producir exactamente
# la salida guardada en tests/expected/<nombre>.out y terminar con código 0.

import glob
import os
import subprocess
import sys
import unittest

from helpers import ROOT

EJEMPLOS = sorted(glob.glob(os.path.join(ROOT, "examples", "*.src")))


class TestEjemplos(unittest.TestCase):

    def test_existen_los_cinco_ejemplos(self):
        nombres = [os.path.basename(e) for e in EJEMPLOS]
        self.assertEqual(len(nombres), 5, nombres)


def _crear_prueba(ruta):
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    esperado = os.path.join(ROOT, "tests", "expected", nombre + ".out")

    def prueba(self):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), ruta],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(esperado, encoding="utf-8") as f:
            self.assertEqual(p.stdout, f.read())

    return nombre, prueba


for _ruta in EJEMPLOS:
    _nombre, _fn = _crear_prueba(_ruta)
    setattr(TestEjemplos, f"test_ejemplo_{_nombre}", _fn)


if __name__ == "__main__":
    unittest.main()
