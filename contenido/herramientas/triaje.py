#!/usr/bin/env python3
"""Triaje de un tramo: por página, menciones de lugares de Sucre (alias.json) y de otras ciudades.

Uso: python3 contenido/herramientas/triaje.py 2 150
Sirve para decidir qué secciones se leen completas y cuáles por encima. No reemplaza la lectura.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from buscar import cargar  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
SUCRE = r"chuquisaca|la plata|charcas|sucre"
OTRAS = r"potosi|lima|cuzco|la paz|oruro|cochabamba|tucuman|buenos aires|santa cruz|espana|madrid|quito|chile"


def main():
    ini, fin = int(sys.argv[1]), int(sys.argv[2])
    alias = json.loads((BASE / "alias.json").read_text())
    patrones = {k: re.compile("|".join(v["buscar"])) for k, v in alias.items() if not k.startswith("_")}
    paginas = cargar()
    print("pág  sucre otras  lugares")
    for p in range(ini, fin + 1):
        t = paginas.get(p, "")
        lug = {k: len(r.findall(t)) for k, r in patrones.items()}
        lug = {k: n for k, n in lug.items() if n}
        s, o = len(re.findall(SUCRE, t)), len(re.findall(OTRAS, t))
        print(f"{p:4d} {s:5d} {o:5d}  " + ", ".join(f"{k}:{n}" for k, n in lug.items()))


if __name__ == "__main__":
    main()
