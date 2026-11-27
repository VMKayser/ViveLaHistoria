#!/usr/bin/env python3
"""BASE incremental por teselas (pedido del usuario, 2026-11-13: "no puede ser que haya que reexportar todo cada vez").

La BASE (calzadas, veredas, relleno de cuadras, postes, cables) se parte en teselas de LADO m. Cada tesela guarda una
huella (hash) de todo lo que la afecta:
  - el código de la BASE y del kit,
  - reparto/calles_reales.json y las partes del reparto que usa (espacios, zonas sin relleno, manzanas cercanas),
  - los GLB de los dos agentes que tocan la tesela (más un margen).
Al correr, solo se regeneran las teselas cuya huella cambió (en paralelo), y después se ensamblan en BASE.glb.

Uso:
  python3 scripts/base.py              # incremental (lo normal)
  python3 scripts/base.py --todo       # fuerza todas las teselas
  python3 scripts/base.py --procesos 3 # cuántos Blender en paralelo (por defecto 2; la PC tiene poca memoria)
  python3 scripts/base.py --solo-ver   # muestra qué teselas cambiarían, sin construir
"""

import argparse
import ast
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLENDER = os.path.expanduser("~/apps/blender-5.2.3-linux-x64/blender")
LADO = 150.0
MARGEN = 60.0
CARPETA = os.path.join(RAIZ, "web", "public", "models", "ciudad", "claude", "base_teselas")
INDICE = os.path.join(CARPETA, "indice.json")
CODIGO = (glob.glob(os.path.join(RAIZ, "blender", "zonas", "claude", "base_*.py"))
          + [os.path.join(RAIZ, "blender", "zonas", "claude", "BASE.py")]
          + glob.glob(os.path.join(RAIZ, "blender", "kit", "*.py"))
          + glob.glob(os.path.join(RAIZ, "secciones", "*.json")))       # polígonos de las secciones nuevas


def _sha(*partes):
    h = hashlib.sha1()
    for p in partes:
        h.update(p if isinstance(p, bytes) else json.dumps(p, sort_keys=True).encode())
    return h.hexdigest()


def _sha_archivo(ruta):
    with open(ruta, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def zona_total(rep):
    """Caja de la zona + ampliaciones (igual que base_suelo._zona)."""
    z = rep["zona"]
    cajas = [(z["xmin"], z["ymin"], z["xmax"], z["ymax"])]
    src = open(os.path.join(RAIZ, "blender", "zonas", "claude", "base_suelo.py")).read()
    for linea in src.splitlines():
        if linea.startswith("AMPLIACIONES"):
            cajas += [tuple(c) for c in ast.literal_eval(linea.split("=", 1)[1].strip())]
    for e in rep.get("espacios", []):
        if e["id"].startswith("AMP_") and e.get("poligono"):
            xs, ys = [p[0] for p in e["poligono"]], [p[1] for p in e["poligono"]]
            cajas.append((min(xs) - 15, min(ys) - 15, max(xs) + 15, max(ys) + 15))
    m = 20
    return (min(c[0] for c in cajas) - m, min(c[1] for c in cajas) - m, max(c[2] for c in cajas) + m,
            max(c[3] for c in cajas) + m)


def bbox_modelo(rep, mid):
    m = next((x for x in rep["manzanas"] if x["id"] == mid), None)
    if m:
        pts = [p for e in m["edificios"] for p in e["huella"]] or [m["centro"]]
    else:
        e = next((x for x in rep.get("espacios", []) if x["id"] == mid), None)
        if not e or not e.get("poligono"):
            return None
        pts = e["poligono"]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def teselas(rep):
    x0, y0, x1, y1 = zona_total(rep)
    res = []
    i = 0
    x = x0
    while x < x1:
        j = 0
        y = y0
        while y < y1:
            res.append((f"T_{i:02d}_{j:02d}", (round(x, 2), round(y, 2), round(min(x + LADO, x1), 2), round(min(y + LADO, y1), 2))))
            y += LADO
            j += 1
        x += LADO
        i += 1
    return res


def huella_tesela(rep, caja, cod, calles):
    glbs = []
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb"))):
        mid = os.path.basename(ruta)[:-4]
        if mid.startswith("BASE"):
            continue
        b = bbox_modelo(rep, mid)
        if b is None or not (b[2] < caja[0] - MARGEN or b[0] > caja[2] + MARGEN or b[3] < caja[1] - MARGEN
                             or b[1] > caja[3] + MARGEN):
            glbs.append((os.path.relpath(ruta, RAIZ), _sha_archivo(ruta)))
    reparto_rel = {"espacios": rep.get("espacios", []), "zonas_sin_relleno": rep.get("zonas_sin_relleno", []),
                   "zona": rep["zona"], "frontera": rep.get("frontera")}
    return _sha(cod, calles, reparto_rel, glbs, list(caja))


def construir(nombre, caja):
    t0 = time.time()
    cmd = [BLENDER, "--background", "--python", os.path.join(RAIZ, "blender", "zonas", "claude", "BASE.py"), "--",
           "--tesela", *[str(v) for v in caja], nombre]
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    ok = f"tesela {nombre} lista" in r.stdout
    if not ok:
        print(r.stdout[-2000:], r.stderr[-2000:], file=sys.stderr)
    return nombre, ok, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--procesos", type=int, default=2)
    ap.add_argument("--solo-ver", action="store_true")
    a = ap.parse_args()
    rep = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))
    os.makedirs(CARPETA, exist_ok=True)
    indice = json.load(open(INDICE)) if os.path.exists(INDICE) else {}
    cod = _sha(*[open(f, "rb").read() for f in sorted(CODIGO)])
    calles = _sha_archivo(os.path.join(RAIZ, "reparto", "calles_reales.json"))
    todas = teselas(rep)
    huellas = {n: huella_tesela(rep, c, cod, calles) for n, c in todas}
    pendientes = [(n, c) for n, c in todas if a.todo or indice.get(n) != huellas[n]
                  or not os.path.exists(os.path.join(CARPETA, n + ".glb"))]
    print(f"[base] {len(todas)} teselas de {LADO:.0f} m; {len(pendientes)} por regenerar")
    if a.solo_ver:
        for n, c in pendientes:
            print("  ", n, c)
        return
    if not pendientes:
        print("[base] nada que regenerar")
        return
    hechas = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, a.procesos)) as ex:
        for nombre, ok, dt in ex.map(lambda nc: construir(*nc), pendientes):
            hechas += 1
            if ok:
                indice[nombre] = huellas[nombre]
                json.dump(indice, open(INDICE, "w"), indent=1, sort_keys=True)
            print(f"[base] {hechas}/{len(pendientes)} {nombre} {'ok' if ok else 'ERROR'} ({dt / 60:.1f} min; "
                  f"total {(time.time() - t0) / 60:.1f} min)", flush=True)
    print("[base] ensamblando BASE.glb…", flush=True)
    r = subprocess.run([BLENDER, "--background", "--python", os.path.join(RAIZ, "blender", "zonas", "claude", "BASE.py"),
                        "--", "--ensamblar", "--sin-render"], cwd=RAIZ, capture_output=True, text=True)
    print([l for l in r.stdout.splitlines() if "exportado" in l] or r.stderr[-1500:])


if __name__ == "__main__":
    main()
