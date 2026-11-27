"""Prepara el mapa para la herramienta de fotos (web/src/app/mapa).

- Convierte el lienzo FBX a GLB (una malla por material) -> web/public/mapa/raw/lienzo.glb
- Extrae calles y lugares con nombre de OSM, proyectados al sistema del FBX y
  apoyados sobre el terreno -> web/public/mapa/calles.json y lugares.json

Uso (desde la raíz del proyecto):
  ~/apps/blender-5.2.3-linux-x64/blender --background --python blender/scripts/preparar_mapa.py
  cd web && npm run mapa      # comprime el GLB

Coordenadas: metros, X = este, Y = norte, Z = altura (sistema Blender del FBX).
Ver geo.py / web/src/mapa/geo.ts para la conversión lat/lon <-> metros.
"""

import json
import lzma
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(__file__))
from geo import a_metros  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FBX = os.path.join(RAIZ, "urban-export_-19.0460_-65.2578_2230m.fbx")
OSM = os.path.join(RAIZ, "Sucre.osm.geojson.xz")
SALIDA = os.path.join(RAIZ, "web", "public", "mapa")
MITAD = 1115.0  # medio lado del lienzo en metros

# Tipos de vía que se dibujan (los senderos y escaleras también ayudan a ubicarse)
VIAS = {
    "primary", "secondary", "tertiary", "residential", "unclassified", "living_street",
    "pedestrian", "service", "trunk", "primary_link", "secondary_link", "tertiary_link",
    "footway", "steps", "path", "track", "cycleway",
}


def importar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=FBX)


def bvh_terreno():
    t = bpy.data.objects["TERRAIN"]
    m = t.matrix_world
    verts = [m @ v.co for v in t.data.vertices]
    polys = [tuple(p.vertices) for p in t.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def altura(bvh, x, y):
    hit = bvh.ray_cast(Vector((x, y, 2000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0


def densificar(pts, paso=6.0):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        n = max(1, int(d // paso))
        for i in range(1, n + 1):
            out.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n))
    return out


def dentro(x, y):
    return abs(x) < MITAD and abs(y) < MITAD


def nombre(p):
    return p.get("name") or p.get("name:es") or ""


def extraer_osm(bvh):
    datos = json.load(lzma.open(OSM))
    calles, lugares = [], []
    for f in datos["features"]:
        p, g = f["properties"], f["geometry"]
        if p.get("highway") in VIAS and g["type"] == "LineString":
            pts = [a_metros(lat, lon) for lon, lat in g["coordinates"]]
            if not any(dentro(x, y) for x, y in pts):
                continue
            pts = densificar(pts)
            calles.append({
                "nombre": nombre(p),
                "tipo": p["highway"],
                "puntos": [[round(x, 2), round(y, 2), round(altura(bvh, x, y) + 0.6, 2)] for x, y in pts],
            })
        elif nombre(p) and g["type"] in ("Point", "MultiPolygon") and "highway" not in p:
            if g["type"] == "Point":
                lon, lat = g["coordinates"]
            else:
                anillo = g["coordinates"][0][0]
                lon = sum(c[0] for c in anillo) / len(anillo)
                lat = sum(c[1] for c in anillo) / len(anillo)
            x, y = a_metros(lat, lon)
            if not dentro(x, y):
                continue
            tipo = next((f"{k}={p[k]}" for k in ("amenity", "tourism", "historic", "leisure", "building", "shop", "office", "place", "landuse") if k in p), "")
            lugares.append({"nombre": nombre(p), "tipo": tipo, "x": round(x, 1), "y": round(y, 1), "z": round(altura(bvh, x, y), 1)})
    return calles, lugares


def unir_por_material():
    """El FBX trae ~440 objetos (cada árbol aparte); se unen por material para la web."""
    grupos = {}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.materials:
            grupos.setdefault(o.data.materials[0].name, []).append(o)
    for mat, objs in grupos.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        objs[0].name = mat


def main():
    importar()
    os.makedirs(os.path.join(SALIDA, "raw"), exist_ok=True)
    bvh = bvh_terreno()
    calles, lugares = extraer_osm(bvh)
    with open(os.path.join(SALIDA, "calles.json"), "w") as fh:
        json.dump(calles, fh, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(SALIDA, "lugares.json"), "w") as fh:
        json.dump(lugares, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"calles: {len(calles)}  lugares: {len(lugares)}")

    unir_por_material()
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(SALIDA, "raw", "lienzo.glb"),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_normals=True,
    )


main()
