"""Perfil de fachadas de UNA calle (herramienta de sección, skill desarrollo-por-seccion): recorre el eje real de la
calle cada `paso` m y, a 1,6 m de altura, lanza un rayo a cada lado contra lo exportado (edificios de los dos agentes,
sin mobiliario ni BASE). Así se ven los tramos sin fachada (huecos al cielo, lotes vacíos) y las fachadas que invaden
la vereda o quedan retiradas.

Uso: blender -b -P blender/zonas/claude/frente_calle.py -- "<nombre de la calle>" [x0 y0 x1 y1] [--paso 1]
Salida (stdout): tramos "izq/der t0–t1: hueco | fachada a d m (esperado w/2)".
"""

import glob
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit.datos import RAIZ, altura_suelo, calles_reales  # noqa: E402

FUERA = ("arbol", "poste", "cable", "farol", "pino", "banco", "bolardo", "semaforo", "toldo", "puesto", "letrero",
         "vereda", "piso", "BASE_plaza", "P01_", "explanada", "detalles", "carpa", "quitasol", "BASE")

args = sys.argv[sys.argv.index("--") + 1:]
nombre = args[0]
caja = tuple(float(v) for v in args[1:5]) if len(args) >= 5 and not args[1].startswith("--") else None
paso = float(args[args.index("--paso") + 1]) if "--paso" in args else 1.0

bpy.ops.wm.read_factory_settings(use_empty=True)
for r in glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb")):
    if not r.endswith("BASE.glb"):
        bpy.ops.import_scene.gltf(filepath=r)
dg = bpy.context.evaluated_depsgraph_get()
bm = bmesh.new()
for o in bpy.data.objects:
    if o.type != "MESH" or any(k.lower() in o.name.lower() for k in FUERA):
        continue
    me = o.evaluated_get(dg).to_mesh()
    me.transform(o.matrix_world)
    bm.from_mesh(me)
bvh = BVHTree.FromBMesh(bm)

for c in calles_reales():
    if c["nombre"] != nombre:
        continue
    eje = c["eje"]
    if caja and not any(caja[0] <= p[0] <= caja[2] and caja[1] <= p[1] <= caja[3] for p in eje):
        continue
    w = c["ancho"] / 2
    print(f"=== {nombre}  ancho {c['ancho']}  vereda {c['vereda']}  de {eje[0]} a {eje[-1]}")
    for sg, lado in ((1, "izq"), (-1, "der")):
        t, tramos = 0.0, []
        for p, q in zip(eje, eje[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            nx, ny = -uy * sg, ux * sg
            s = 0.0
            while s < L:
                x, y = p[0] + ux * s, p[1] + uy * s
                if caja and not (caja[0] <= x <= caja[2] and caja[1] <= y <= caja[3]):
                    s += paso
                    continue
                z = altura_suelo(x, y) + 1.6
                hit = bvh.ray_cast(Vector((x, y, z)), Vector((nx, ny, 0)), w + 6)
                d = hit[3] if hit[0] else None
                estado = "hueco" if d is None else ("invade" if d < w - 0.25 else ("retirada" if d > w + 0.6 else "ok"))
                if tramos and tramos[-1][2] == estado:
                    tramos[-1][1] = t + s
                    if d is not None:
                        tramos[-1][3].append(d)
                else:
                    tramos.append([t + s, t + s, estado, [d] if d is not None else [], (round(x, 1), round(y, 1))])
                s += paso
            t += L
        for t0, t1, est, ds, xy in tramos:
            extra = f" d≈{sorted(ds)[len(ds) // 2]:.2f} (esperado {w:.2f})" if ds else ""
            print(f"  {lado} t {t0:6.1f}–{t1:6.1f} ({t1 - t0:5.1f} m) desde {xy}: {est}{extra}")
