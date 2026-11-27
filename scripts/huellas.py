#!/usr/bin/env python3
"""Genera web/public/mapa/huellas_manzanas.json a partir de reparto/manzanas.json.

El visor oculta los volúmenes genéricos del lienzo (los "muros blancos por defecto") en las huellas de cada GLB
cargado. Antes este archivo se editaba a mano y las zonas nuevas quedaban afuera (2026-11-13: AMP_S y la Peatonal
mostraban muros del lienzo encima de lo modelado). Ahora se genera siempre desde el reparto:

  - manzana M###      → las huellas de sus edificios del lienzo + `huellas_extra` (lo modelado fuera del lienzo);
  - espacio con polígono (P01, AMP_*, PEATONAL…) → el polígono entero + sus `huellas_lienzo`.

Uso: python3 scripts/huellas.py   (correrlo cada vez que cambie reparto/manzanas.json; lo verifica scripts/calidad.py)
"""

import json
import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _dentro(x, y, pts):
    c = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def _redondear(p):
    return [[round(x, 2), round(y, 2)] for x, y in p]


def generar():
    rep = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))
    out = {}
    lienzo = json.load(open(os.path.join(RAIZ, "reparto", "edificios_lienzo.json")))
    for m in rep["manzanas"]:
        polis = [e["huella"] for e in m["edificios"]] + m.get("huellas_extra", [])
        # volúmenes del lienzo que pisan algún edificio de la manzana (aunque no sean "suyos"): asomarían encima
        polis += [b["huella"] for b in lienzo if b["huella"] not in polis
                  and any(_dentro(x, y, h) for h in polis for x, y in b["huella"])]
        out[m["id"]] = [_redondear(p) for p in polis]
    for e in rep.get("espacios", []):
        polis = ([e["poligono"]] if e.get("poligono") else []) + e.get("huellas_lienzo", [])
        if e.get("poligono"):
            # volúmenes del lienzo que cruzan el borde del espacio: se ocultan enteros (si no, asoma media pared)
            polis += [b["huella"] for b in lienzo if any(_dentro(x, y, e["poligono"]) for x, y in b["huella"])]
        if polis:
            out[e["id"]] = [_redondear(p) for p in polis]
    return out


def main():
    out = generar()
    ruta = os.path.join(RAIZ, "web", "public", "mapa", "huellas_manzanas.json")
    with open(ruta, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} entradas → {os.path.relpath(ruta, RAIZ)}")


if __name__ == "__main__":
    main()
