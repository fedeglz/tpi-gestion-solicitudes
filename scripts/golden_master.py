"""Genera una transcripcion reproducible (comandos + salidas + datos finales).

Uso:  python scripts/golden_master.py docs/evidencias/golden_<version>.txt
Se ejecuta en `estado-inicial` y en `estado-refactorizado`; ambos archivos
deben ser IDENTICOS (diff vacio) => el comportamiento externo se conserva.
"""
import json
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ESCENARIO = [
    [], ["borrar"], ["reporte"], ["buscar"],
    ["registrar", "30111222", "Ana Perez", "ana@mail.com", "constancia", "alta", "Constancia regular"],
    ["registrar", "30999888", "Luis Gomez", "luis@mail.com", "reclamo", "media", "Reclamo de nota"],
    ["registrar", "30111222", "Ana Perez", "ana@mail.com", "equivalencia", "baja", "Equivalencia de Algebra"],
    ["registrar", "30555111", "Sol Diaz", "sol@mail.com", "otro", "alta", "Consulta general"],
    ["registrar", "", "Sin Dni", "x@mail.com", "otro", "alta", "x"],
    ["registrar", "1", "N", "x@mail.com", "beca", "alta", "x"],
    ["registrar", "1", "N", "x@mail.com", "otro", "urgente", "x"],
    ["registrar", "1", "N", "sin-arroba", "otro", "alta", "x"],
    ["registrar", "1", "N"],
    ["estado", "1", "En proceso"], ["estado", "1", "Pendiente"], ["estado", "1", "Resuelta"],
    ["estado", "1", "En proceso"], ["estado", "2", "Resuelta"], ["estado", "2", "Rechazada"],
    ["estado", "2", "En proceso"], ["estado", "77", "En proceso"], ["estado", "x", "En proceso"],
    ["estado", "3", "Inventado"],
    ["asignar", "1", "Bedelia"], ["asignar", "3", "Tecnica"], ["asignar", "3", "Alumnado"],
    ["asignar", "3", "Rectorado"], ["asignar", "99", "Rectorado"], ["asignar", "99", "Bedelia"],
    ["asignar", "2", "Bedelia"], ["asignar", "q", "Bedelia"],
    ["buscar"], ["buscar", "--estado=Pendiente"], ["buscar", "--tipo=otro"],
    ["buscar", "--prioridad=alta", "--estado=Resuelta"], ["buscar", "--estado=Inventado"],
    ["reporte"],
]


def main(destino):
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "datos", "solicitudes.json")
        env = dict(os.environ, SOLICITUDES_DB=db, SOLICITUDES_FECHA="2026-03-10")
        lineas = []
        for args in ESCENARIO:
            r = subprocess.run([sys.executable, "main.py", *args], cwd=RAIZ, env=env,
                               capture_output=True, text=True)
            lineas.append("$ main.py " + " ".join(repr(a) for a in args))
            lineas.extend(r.stdout.rstrip("\n").splitlines())
            lineas.append("[exit=%d]" % r.returncode)
        with open(db, encoding="utf-8") as f:
            lineas.append("== DATOS FINALES ==")
            lineas.append(json.dumps(json.load(f), indent=1, sort_keys=True, ensure_ascii=False))
    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print("Escrito", destino, "(%d lineas)" % len(lineas))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "golden.txt")
