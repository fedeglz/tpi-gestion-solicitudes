"""Punto de entrada: delega todo en la capa CLI."""
import sys

from gestion_solicitudes.cli import main

if __name__ == "__main__":
    main(sys.argv[1:])
