#!/usr/bin/env python3
"""Exportación incremental de manzanas (pedido del usuario, 2026-11-13: "solo exportar lo afectado").

Cada script de manzana/espacio (`blender/zonas/<agente>/<ID>.py`) depende de:
  - sí mismo y de los módulos locales que importa (transitivamente: generica.py, piezas_claude.py, …),
  - el kit (`blender/kit/*.py`), `reparto/calles_reales.json` y su entrada del reparto.
Se guarda un hash de todo eso por ID; solo se reexportan los IDs cuyo hash cambió (en paralelo).

Uso:
  python3 scripts/exportar.py claude              # incremental
  python3 scripts/exportar.py claude M013 AMP_S   # solo esos (si cambiaron); con --forzar, siempre
  python3 scripts/exportar.py claude --solo-ver   # qué se reexportaría
  python3 scripts/exportar.py claude --marcar     # registra los GLB actuales como al día (primera vez)
Después de exportar manzanas, `python3 scripts/base.py` rehace solo las teselas de la BASE afectadas.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLENDER = os.path.expanduser("~/apps/blender-5.2.3-linux-x64/blender")
EXCLUIR = {"BASE"}                       # la BASE va por scripts/base.py


def _sha_bytes(*bs):
    h = hashlib.sha1()
    for b in bs:
        h.update(b)
    return h.hexdigest()


def dependencias(ruta, carpeta, vistos=None):
    """Módulos locales importados por el script (transitivo)."""
    vistos = vistos if vistos is not None else set()
    if ruta in vistos:
        return vistos
    vistos.add(ruta)
    src = open(ruta, encoding="utf-8").read()
    for mod in set(re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", src, re.M)):
        r = os.path.join(carpeta, mod + ".py")
        if os.path.exists(r):
            dependencias(r, carpeta, vistos)
    return vistos


def huella(agente, mid, kit, calles, rep):
    carpeta = os.path.join(RAIZ, "blender", "zonas", agente)
    deps = sorted(dependencias(os.path.join(carpeta, mid + ".py"), carpeta))
    entrada = next((m for m in rep["manzanas"] if m["id"] == mid), None) or \
        next((e for e in rep.get("espacios", []) if e["id"] == mid), None)
    return _sha_bytes(*[open(d, "rb").read() for d in deps], kit.encode(), calles.encode(),
                      json.dumps(entrada, sort_keys=True).encode())


def exportar(agente, mid):
    t0 = time.time()
    r = subprocess.run([BLENDER, "--background", "--python", os.path.join("blender", "zonas", agente, mid + ".py"),
                        "--", "--sin-render"], cwd=RAIZ, capture_output=True, text=True)
    ok = "[kit] exportado" in r.stdout
    if not ok:
        print(r.stdout[-1500:], r.stderr[-1500:], file=sys.stderr)
    return mid, ok, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agente")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--solo-ver", action="store_true")
    ap.add_argument("--procesos", type=int, default=2)
    ap.add_argument("--marcar", action="store_true", help="registrar los GLB actuales como al día, sin exportar")
    a = ap.parse_args()
    rep = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))
    dueno = {m["id"]: m["dueno"] for m in rep["manzanas"]}
    dueno.update({e["id"]: e.get("dueno") for e in rep.get("espacios", [])})
    carpeta = os.path.join(RAIZ, "blender", "zonas", a.agente)
    ids = a.ids or sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(carpeta, "*.py"))
                          if os.path.basename(p)[:-3] in dueno)
    ids = [i for i in ids if i not in EXCLUIR and dueno.get(i) == a.agente]
    kit = _sha_bytes(*[open(f, "rb").read() for f in sorted(glob.glob(os.path.join(RAIZ, "blender", "kit", "*.py")))])
    calles = _sha_bytes(open(os.path.join(RAIZ, "reparto", "calles_reales.json"), "rb").read())
    ruta_idx = os.path.join(RAIZ, "web", "public", "models", "ciudad", a.agente, "exportacion.json")
    idx = json.load(open(ruta_idx)) if os.path.exists(ruta_idx) else {}
    hs = {i: huella(a.agente, i, kit, calles, rep) for i in ids}
    glb = lambda i: os.path.join(RAIZ, "web", "public", "models", "ciudad", a.agente, i + ".glb")
    pend = [i for i in ids if a.forzar or idx.get(i) != hs[i] or not os.path.exists(glb(i))]
    print(f"[exportar] {len(ids)} ids de {a.agente}; {len(pend)} por reexportar: {' '.join(pend)}")
    if a.marcar:
        idx.update({i: hs[i] for i in pend if os.path.exists(glb(i))})
        json.dump(idx, open(ruta_idx, "w"), indent=1, sort_keys=True)
        print("[exportar] marcados como al día")
        return
    if a.solo_ver or not pend:
        return
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, a.procesos)) as ex:
        for k, (mid, ok, dt) in enumerate(ex.map(lambda i: exportar(a.agente, i), pend), 1):
            if ok:
                idx[mid] = hs[mid]
                json.dump(idx, open(ruta_idx, "w"), indent=1, sort_keys=True)
            print(f"[exportar] {k}/{len(pend)} {mid} {'ok' if ok else 'ERROR'} ({dt:.0f} s; total "
                  f"{(time.time() - t0) / 60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()
