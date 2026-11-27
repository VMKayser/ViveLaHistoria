#!/usr/bin/env python3
"""Lista las correcciones del usuario (coordinacion/revisiones/) y arma la cámara para reproducirlas en Blender.

Uso:
    python3 scripts/revisiones.py claude            # pendientes y en curso asignadas a claude
    python3 scripts/revisiones.py codex --todas     # todas las de codex
    python3 scripts/revisiones.py --sin-asignar     # las que no cayeron en ninguna manzana (las reparte claude)

Para cada una imprime el comentario, el lugar, las imágenes y una línea lista para pegar en revisar():
    camaras_extra=[("R0007", (x, y, z), (x, y, z))]
(posición de los ojos y punto mirado, en metros del lienzo: X este, Y norte, Z altura).
"""

import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "coordinacion" / "revisiones"


def camara(rev):
    c = rev["escena"]["camara"]
    p = c["lienzo"]
    r, i = math.radians(c["rumbo_grados"]), math.radians(c["inclinacion_grados"])
    d = rev["escena"].get("distancia_m") or 20.0
    mira = (p["x"] + math.sin(r) * math.cos(i) * d, p["y"] + math.cos(r) * math.cos(i) * d, p["z"] + math.sin(i) * d)
    if rev["escena"].get("centro"):
        q = rev["escena"]["centro"]
        mira = (q["x"], q["y"], q["z"])
    return (round(p["x"], 2), round(p["y"], 2), round(p["z"], 2)), tuple(round(v, 2) for v in mira), c["fov_vertical_grados"]


def main():
    args = sys.argv[1:]
    todas = "--todas" in args
    sin_asignar = "--sin-asignar" in args
    agente = next((a for a in args if not a.startswith("--")), None)
    revs = []
    for f in sorted(CARPETA.glob("R*/revision.json")):
        r = json.loads(f.read_text())
        if sin_asignar and r["lugar"].get("asignado"):
            continue
        if agente and r["lugar"].get("asignado") != agente:
            continue
        if not todas and r["estado"] not in ("pendiente", "en_curso"):
            continue
        revs.append(r)
    if not revs:
        print("No hay correcciones que mostrar.")
        return
    for r in revs:
        lugar = r["lugar"]
        donde = " / ".join(x for x in (lugar.get("manzana"), lugar.get("edificio"), lugar.get("espacio")) if x) or "fuera del reparto"
        pos, mira, fov = camara(r)
        carpeta = CARPETA / r["id"]
        print(f"=== {r['id']} [{r['estado']}] {r['categoria']} · prioridad {r['prioridad']} · {donde} · para {lugar.get('asignado')}")
        print(f"    {r['escena'].get('calle', '')} · {r['autor']} · {r['creada'][:16]}")
        for linea in r["comentario"].splitlines():
            print(f"    > {linea}")
        imgs = [r["archivos"]["recorte"], r["archivos"]["captura"]] + ([r["archivos"]["referencia"]] if r["archivos"]["referencia"] else [])
        print("    imágenes: " + ", ".join(str(carpeta / i) for i in imgs))
        if r["archivos"]["fotos_proyecto"]:
            print("    fotos del proyecto: " + ", ".join(r["archivos"]["fotos_proyecto"]))
        print(f'    revisar(..., camaras_extra=[("{r["id"]}", {pos}, {mira})])   # fov vertical {fov}°')
        print()


if __name__ == "__main__":
    main()
