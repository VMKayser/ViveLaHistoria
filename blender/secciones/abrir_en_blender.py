"""Abre una SECCIÓN en Blender con interfaz y conecta el addon MCP (blender-mcp, puerto 9876 en localhost) para
trabajarla en vivo desde Claude Code (servidor MCP "blender", `uvx blender-mcp`).

Uso: blender -P blender/secciones/abrir_en_blender.py -- plaza_25_mayo
     (scripts/abrir_seccion.sh plaza_25_mayo lo lanza con la NVIDIA)
"""

import glob
import json
import os
import sys

import bpy

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
nombre = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "plaza_25_mayo"
sec = json.load(open(os.path.join(RAIZ, "secciones", nombre + ".json")))
xs = [p[0] for p in sec["limite"]]
ys = [p[1] for p in sec["limite"]]
caja = (min(xs) - 40, min(ys) - 40, max(xs) + 40, max(ys) + 40)
rep = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))

# escena vacía sin volver a las preferencias de fábrica (desactivarían el addon MCP)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
import addon_utils  # noqa: E402
addon_utils.enable("blender_mcp", default_set=True, persistent=True)
for r in sorted(glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb"))):
    mid = os.path.basename(r)[:-4]
    m = next((x for x in rep["manzanas"] if x["id"] == mid), None) or \
        next((x for x in rep.get("espacios", []) if x["id"] == mid), None)
    pts = ([p for e in m["edificios"] for p in e["huella"]] if m and m.get("edificios") else (m or {}).get("poligono"))
    if mid != "BASE" and pts:
        px, py = [p[0] for p in pts], [p[1] for p in pts]
        if max(px) < caja[0] or min(px) > caja[2] or max(py) < caja[1] or min(py) > caja[3]:
            continue
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=r)
    nueva = bpy.data.collections.new(mid)
    bpy.context.scene.collection.children.link(nueva)
    for o in set(bpy.data.objects) - antes:
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        nueva.objects.link(o)
print("[seccion] cargada", nombre)


def _conectar():
    try:
        bpy.ops.blendermcp.start_server()
        print("[seccion] MCP conectado en localhost:9876")
    except Exception as e:  # noqa: BLE001
        print("[seccion] no se pudo iniciar el MCP:", e)
    return None


bpy.app.timers.register(_conectar, first_interval=2.0)
