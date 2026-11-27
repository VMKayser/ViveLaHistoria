"""Extrae las huellas (planta) y alturas de los edificios del lienzo FBX dentro de una zona.

El FBX trae cada edificio como un prisma (isla de malla). Para cada isla:
  huella = borde de las caras superiores, base = z mínima, altura = z máxima - z mínima.

Uso (desde la raíz del proyecto):
  ~/apps/blender-5.2.3-linux-x64/blender --background --python blender/scripts/extraer_huellas.py -- XMIN YMIN XMAX YMAX
Salidas: reparto/edificios_lienzo.json y reparto/terreno.json (rejilla de alturas del terreno)
"""

import json
import os
import sys

import bmesh
import bpy

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FBX = os.path.join(RAIZ, "urban-export_-19.0460_-65.2578_2230m.fbx")


def islas(bm):
    visto = set()
    for v in bm.verts:
        if v.index in visto:
            continue
        grupo, pila = [], [v]
        visto.add(v.index)
        while pila:
            a = pila.pop()
            grupo.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in visto:
                    visto.add(b.index)
                    pila.append(b)
        yield grupo


def anillo_superior(verts):
    caras = {f for v in verts for f in v.link_faces if f.normal.z > 0.9}
    if not caras:
        return None
    ztop = max(v.co.z for f in caras for v in f.verts)
    caras = {f for f in caras if min(v.co.z for v in f.verts) > ztop - 0.5}
    borde = [e for f in caras for e in f.edges if sum(1 for g in e.link_faces if g in caras) == 1]
    if len(borde) < 3:
        return None
    sig = {}
    for e in borde:
        a, b = e.verts
        sig.setdefault(a, []).append(b)
        sig.setdefault(b, []).append(a)
    # recorre el anillo más largo
    inicio = max(sig, key=lambda v: (v.co.x, v.co.y))
    anillo, prev, cur = [inicio], None, inicio
    for _ in range(len(borde) + 1):
        opciones = [w for w in sig[cur] if w is not prev]
        if not opciones:
            break
        prev, cur = cur, opciones[0]
        if cur is inicio:
            break
        anillo.append(cur)
    return anillo, ztop


def guardar_terreno():
    """Rejilla regular de alturas del TERRAIN del lienzo (para apoyar fachadas y calles en la pendiente)."""
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    t = bpy.data.objects["TERRAIN"]
    vs = [t.matrix_world @ v.co for v in t.data.vertices]
    bvh = BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in t.data.polygons])
    paso, mitad = 5.0, 1110.0
    n = int(2 * mitad / paso) + 1
    filas = []
    for j in range(n):
        y = -mitad + j * paso
        fila = []
        for i in range(n):
            hit = bvh.ray_cast(Vector((-mitad + i * paso, y, 3000.0)), Vector((0, 0, -1)))
            fila.append(round(hit[0].z, 2) if hit[0] is not None else 0.0)
        filas.append(fila)
    with open(os.path.join(RAIZ, "reparto", "terreno.json"), "w") as fh:
        json.dump({"origen": [-mitad, -mitad], "paso": paso, "n": n, "z": filas}, fh, separators=(",", ":"))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    xmin, ymin, xmax, ymax = (float(a) for a in args) if len(args) == 4 else (-350, -410, -50, 110)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX)
    salida = []
    for o in bpy.data.objects:
        if not o.name.startswith("BUILDINGS"):
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bm.verts.ensure_lookup_table()
        bm.normal_update()
        for grupo in islas(bm):
            cx = sum(v.co.x for v in grupo) / len(grupo)
            cy = sum(v.co.y for v in grupo) / len(grupo)
            if not (xmin - 20 <= cx <= xmax + 20 and ymin - 20 <= cy <= ymax + 20):
                continue
            r = anillo_superior(grupo)
            if not r:
                continue
            anillo, ztop = r
            zbase = min(v.co.z for v in grupo)
            salida.append({
                "clase": o.name.replace("BUILDINGS_", "").lower(),
                "base_z": round(zbase, 2),
                "altura": round(ztop - zbase, 2),
                "huella": [[round(v.co.x, 2), round(v.co.y, 2)] for v in anillo],
            })
        bm.free()
    os.makedirs(os.path.join(RAIZ, "reparto"), exist_ok=True)
    guardar_terreno()
    with open(os.path.join(RAIZ, "reparto", "edificios_lienzo.json"), "w") as fh:
        json.dump(salida, fh, separators=(",", ":"))
    print(f"edificios extraídos: {len(salida)}")


main()
