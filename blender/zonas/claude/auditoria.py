"""Auditoría automática de incoherencias de un agente (pedido del usuario 2026-11-12).

Para cada GLB del agente busca, por objeto y por material (rol):
- INVASIÓN: geometría a más de 1,2 m dentro del corredor de una calle real medida desde la línea de fachada (los
  aleros, balcones y cornisas pueden volar hasta 1 m) y por debajo de 3 m (lo que molesta al caminar), o cualquier
  cosa dentro de la calzada. No cuenta el mobiliario de la BASE (postes, cables, semáforos, árboles, faroles).
- FLOTANTES: piezas conectadas (islas de la malla) cuyo punto más bajo está a más de 2,5 m sobre el suelo y que no
  tocan nada debajo en 0,5 m (piezas en el aire).

Uso: blender --background --python blender/zonas/claude/auditoria.py -- claude [M013 ...]
Salida: revisiones/<agente>/auditoria.txt
"""

import glob
import os
import sys
from collections import defaultdict

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit.datos import RAIZ, altura_suelo, calles_reales  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["claude"]
agente, solo = args[0], set(args[1:])
MOBILIARIO = ("BASE_postes", "BASE_cables", "BASE_semaforos", "BASE_plaza", "BASE_piso", "BASE_calzada",
              "BASE_veredas", "BASE_marcas", "arbol", "_arboles")

segs = []
for c in calles_reales():
    e = c["eje"]
    for a, b in zip(e, e[1:]):
        segs.append((a, b, c["ancho"] / 2, c["ancho"] / 2 - c["vereda"], c["nombre"]))


def en_calle(x, y):
    """(profundidad dentro del corredor desde la fachada, ¿en calzada?, calle) del corredor más metido."""
    mejor = None
    for a, b, w, cz, n in segs:
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1
        t = ((x - a[0]) * dx + (y - a[1]) * dy) / L2
        if t < 0 or t > 1:
            continue
        px, py = a[0] + t * dx, a[1] + t * dy
        d = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
        if d < w:
            pen = w - d
            if not mejor or pen > mejor[0]:
                mejor = (pen, d < cz, n)
    return mejor


informe = []
rutas = sorted(glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", agente, "*.glb")))
for ruta in rutas:
    mid = os.path.splitext(os.path.basename(ruta))[0]
    if solo and mid not in solo:
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=ruta)
    obs = [o for o in bpy.data.objects if o.type == "MESH"]
    # BVH de todo (para "toca algo debajo")
    verts, polys = [], []
    for o in obs:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    bvh = BVHTree.FromPolygons(verts, polys) if polys else None
    for o in obs:
        if any(k in o.name for k in MOBILIARIO):
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bm.verts.ensure_lookup_table()
        mats = [m.name if m else "?" for m in o.data.materials]
        # islas conectadas
        visto = set()
        for v0 in bm.verts:
            if v0.index in visto:
                continue
            pila, isla = [v0], []
            visto.add(v0.index)
            while pila:
                v = pila.pop()
                isla.append(v)
                for ed in v.link_edges:
                    w = ed.other_vert(v)
                    if w.index not in visto:
                        visto.add(w.index)
                        pila.append(w)
            rol = "?"
            for f in isla[0].link_faces:
                rol = mats[f.material_index].split("__")[0] if f.material_index < len(mats) else "?"
                break
            cx = sum(v.co.x for v in isla) / len(isla)
            cy = sum(v.co.y for v in isla) / len(isla)
            zmin = min(v.co.z for v in isla)
            zs = altura_suelo(cx, cy)
            # invasión de la calle (solo lo bajo, lo que estorba al caminar)
            peor = None
            for v in isla:
                if v.co.z - zs > 3.0:
                    continue
                r = en_calle(v.co.x, v.co.y)
                if r and (r[1] or r[0] > 1.2) and (not peor or r[0] > peor[0]):
                    peor = r
            if peor and rol not in ("vereda", "calzada", "adoquin", "piedra") or (peor and peor[1]):
                informe.append(f"{mid}\t{o.name}\t{rol}\tINVADE {peor[2]} {'calzada' if peor[1] else 'vereda'} "
                               f"{peor[0]:.1f} m\t({cx:.1f}, {cy:.1f})")
            # flotantes
            if zmin - zs > 2.5 and bvh is not None and len(isla) >= 4:
                abajo = bvh.ray_cast(Vector((cx, cy, zmin - 0.02)), Vector((0, 0, -1)), 0.5)
                lados_ok = False
                for v in isla[:: max(1, len(isla) // 12)]:
                    n = bvh.find_nearest(v.co - Vector((0, 0, 0.05)), 0.06)
                    if n[0] is not None and (n[0] - v.co).length > 1e-4:
                        lados_ok = True
                        break
                if abajo[0] is None and not lados_ok and rol not in ("hierro", "follaje", "follaje_claro"):
                    informe.append(f"{mid}\t{o.name}\t{rol}\tFLOTA {zmin - zs:.1f} m sobre el suelo\t({cx:.1f}, {cy:.1f})")
        bm.free()

salida = os.path.join(RAIZ, "revisiones", agente, "auditoria.txt")
os.makedirs(os.path.dirname(salida), exist_ok=True)
with open(salida, "w") as fh:
    fh.write("\n".join(informe) + "\n")
cuenta = defaultdict(int)
for ln in informe:
    cuenta[ln.split("\t")[0]] += 1
print("[auditoria]", len(informe), "problemas:", dict(cuenta), "→", salida)
