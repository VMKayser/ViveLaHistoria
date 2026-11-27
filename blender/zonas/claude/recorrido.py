"""Recorrido de auditoría A PIE por una manzana de claude (pedido del usuario 2026-11-12: buscar incoherencias y
glitches). Carga la manzana exportada con todo su contexto (GLB de los dos agentes y BASE) y renderiza vistas a
1,6 m desde la vereda de enfrente y desde la propia vereda en escorzo, que es donde se notan las piezas flotando,
los cables que atraviesan muros y las caras superpuestas.

Uso: blender --background --python blender/zonas/claude/recorrido.py -- M013 [M018 ...]
Salida: revisiones/claude/<MID>/recorrido_NN.jpg
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import datos  # noqa: E402
from kit.datos import RAIZ, altura_suelo, calle_real_cercana, lados  # noqa: E402
from kit.salida import _luz_y_mundo, camara, contexto, dir_revision  # noqa: E402


def recorrer(mid, paso=16.0, max_vistas=14):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = datos.manzana(mid)
    _luz_y_mundo()
    contexto(mid)
    bpy.ops.import_scene.gltf(filepath=os.path.join(RAIZ, "web", "public", "models", "ciudad", "claude", mid + ".glb"))
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 960, 600
    sc.render.image_settings.file_format = "JPEG"
    salida = dir_revision("claude", mid)
    os.makedirs(salida, exist_ok=True)
    vistas = []
    for e in m["edificios"]:
        for l in lados(e["huella"]):
            if not l["a_calle"] or l["largo"] < 6:
                continue
            ax, ay = l["a"]
            ux, uy = (l["b"][0] - ax) / l["largo"], (l["b"][1] - ay) / l["largo"]
            nx, ny = l["normal"]
            cr = calle_real_cercana(ax + nx * 3, ay + ny * 3)
            ancho = cr[1] if cr else 11.0
            s = 3.0
            while s < l["largo"]:
                px, py = ax + ux * s, ay + uy * s
                # desde la vereda propia, en escorzo a lo largo de la fachada
                ex, ey = px + nx * 1.2, py + ny * 1.2
                z = altura_suelo(ex, ey) + 1.75
                vistas.append(((ex, ey, z), (px + ux * 12 + nx * 0.5, py + uy * 12 + ny * 0.5, z + 2.5)))
                # desde la vereda de enfrente, en diagonal
                fx, fy = px + nx * (ancho - 1.0), py + ny * (ancho - 1.0)
                z = altura_suelo(fx, fy) + 1.75
                vistas.append(((fx, fy, z), (px - ux * 6, py - uy * 6, altura_suelo(px, py) + 4.5)))
                s += paso
    if len(vistas) > max_vistas:
        k = len(vistas) / max_vistas
        vistas = [vistas[int(i * k)] for i in range(max_vistas)]
    for i, (pos, mirar) in enumerate(vistas):
        camara(pos, mirar, lente=18)
        sc.render.filepath = os.path.join(salida, f"recorrido_{i:02d}.jpg")
        bpy.ops.render.render(write_still=True)
    print(f"[recorrido] {mid}: {len(vistas)} vistas en {salida}")


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for mid in args:
    recorrer(mid)
