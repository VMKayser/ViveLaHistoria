"""Vistas a pie de UNA sección (skill desarrollo-por-seccion): carga los GLB exportados (de los dos agentes y la
BASE) que tocan la caja de la sección y renderiza las cámaras de las correcciones del usuario tal como él las vio
(posición, rumbo, inclinación y FOV de `revision.json`), más cámaras libres.

Uso:
  blender -b -P blender/zonas/claude/vistas_seccion.py -- <nombre> <x0> <y0> <x1> <y1> R0127 R0128 \
      [libre:x,y,z,rumbo,inclinacion ...]
Salida: revisiones/claude/secciones/<nombre>/<R####|libre_N>.jpg
"""

import glob
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit.datos import RAIZ, reparto  # noqa: E402
from kit.salida import _luz_y_mundo  # noqa: E402

MARGEN = 120.0


def _caja_modelo(rep, mid):
    m = next((x for x in rep["manzanas"] if x["id"] == mid), None)
    if m:
        pts = [p for e in m["edificios"] for p in e["huella"]] or [m["centro"]]
    else:
        e = next((x for x in rep.get("espacios", []) if x["id"] == mid), None)
        if not e or not e.get("poligono"):
            return None
        pts = e["poligono"]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def cargar(caja):
    rep = reparto()
    for r in sorted(glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb"))):
        mid = os.path.basename(r)[:-4]
        b = _caja_modelo(rep, mid)
        if b and (b[2] < caja[0] - MARGEN or b[0] > caja[2] + MARGEN or b[3] < caja[1] - MARGEN
                  or b[1] > caja[3] + MARGEN):
            continue
        bpy.ops.import_scene.gltf(filepath=r)


def camara(x, y, z, rumbo, incl, fov_v=68.0, aspecto=1.6):
    cam = bpy.data.cameras.new("cam")
    cam.sensor_fit = "VERTICAL"
    cam.angle_y = math.radians(fov_v)
    cam.clip_start, cam.clip_end = 0.05, 3000
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector((x, y, z))
    r, i = math.radians(rumbo), math.radians(incl)
    d = Vector((math.sin(r) * math.cos(i), math.cos(r) * math.cos(i), math.sin(i)))
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    sc = bpy.context.scene
    sc.render.resolution_y = 560
    sc.render.resolution_x = int(560 * aspecto)
    return ob


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    nombre, caja, resto = args[0], tuple(float(v) for v in args[1:5]), args[5:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _luz_y_mundo()
    cargar(caja)
    sc = bpy.context.scene
    sc.render.image_settings.file_format = "JPEG"
    salida = os.path.join(RAIZ, "revisiones", "claude", "secciones", nombre)
    os.makedirs(salida, exist_ok=True)
    k = 0
    for a in resto:
        if a.startswith("libre:"):
            x, y, z, rumbo, incl = (float(v) for v in a[6:].split(","))
            camara(x, y, z, rumbo, incl)
            k += 1
            archivo = f"libre_{k:02d}"
        else:
            rv = json.load(open(os.path.join(RAIZ, "coordinacion", "revisiones", a, "revision.json")))
            cm = rv["escena"]["camara"]
            p = cm["lienzo"]
            camara(p["x"], p["y"], p["z"], cm["rumbo_grados"], cm["inclinacion_grados"], cm["fov_vertical_grados"],
                   min(2.0, cm.get("aspecto", 1.6)))
            archivo = a
        sc.render.filepath = os.path.join(salida, archivo + ".jpg")
        bpy.ops.render.render(write_still=True)
        print(f"[vistas] {archivo}")


main()
