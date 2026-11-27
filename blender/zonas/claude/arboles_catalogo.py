"""Árboles del catálogo elegidos por el usuario (2026-11-23): coloca un árbol preparado (assets/arbol_<especie>.glb, de
preparar_arboles.py) dentro de un Constructor, como geometría con materiales de rol, igual que los árboles hechos a mano
a los que reemplaza. Cada llamada decide la posición, la altura y la especie: nada se reparte al azar por la ciudad.

    poner(c, "jacaranda", x, y, z, alto=13, semilla=k)
"""
import math
import os
import random

import bpy
from mathutils import Matrix, Vector

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ESPECIES = ("comun", "retorcido", "pino_a", "pino_b", "palmera_canaria", "palmera_canaria_b", "palmera_alta", "jacaranda", "isla")
_cache = {}


def _cargar(especie):
    """(vértices, caras [(índices, rol, color)], radio de la copa) del asset, leído una vez por proceso."""
    if especie in _cache:
        return _cache[especie]
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, f"arbol_{especie}.glb"))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    verts, caras = [], []
    for o in nuevos:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        base = len(verts)
        verts.extend([tuple(mw @ v.co) for v in o.data.vertices])
        mats = []
        for s in o.material_slots:
            nom = (s.material.name if s.material else "follaje__4a6b2c").split(".")[0]
            rol, _, hx = nom.partition("__")
            mats.append((rol, "#" + hx[:6] if hx else None))
        for p in o.data.polygons:
            rol, col = mats[p.material_index] if mats else ("follaje", None)
            caras.append(([base + i for i in p.vertices], rol, col))
    mats_asset = {s.material for o in nuevos if o.type == "MESH" for s in o.material_slots if s.material}
    mallas = {o.data for o in nuevos if o.type == "MESH"}
    for o in nuevos:
        bpy.data.objects.remove(o, do_unlink=True)
    for me in mallas:
        if me.users == 0:
            bpy.data.meshes.remove(me)
    # sus materiales (sin color, solo el nombre del rol) no deben quedar en el archivo: el kit reutilizaría uno blanco
    # con el mismo nombre en lugar de crear el suyo con el color de la paleta
    for m in mats_asset:
        if m.users == 0:
            bpy.data.materials.remove(m)
    radio = max((math.hypot(v[0], v[1]) for v in verts), default=0.3)
    _cache[especie] = (verts, caras, radio)
    return _cache[especie]


def radio_copa(especie, alto):
    """Radio de la copa (m) del árbol a esa altura, para dejarlo libre de muros y fuentes al ubicarlo."""
    return _cargar(especie)[2] * alto


def poner(c, especie, x, y, z, alto, semilla=0, ancho=1.0, rumbo=None, encalado=0.0):
    """Árbol `especie` de `alto` m con la base en (x, y, z). ancho: factor horizontal (árboles podados más anchos).
    encalado: alto (m) del pie pintado con cal, como en la plaza y las veredas de Sucre (0 = sin cal)."""
    verts, caras, _ = _cargar(especie)
    rnd = random.Random(semilla)
    rumbo = rnd.uniform(0, math.tau) if rumbo is None else rumbo
    m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rumbo, 4, "Z") @ Matrix.Diagonal((alto * ancho, alto * ancho, alto, 1))
    bm = c.bm
    nv = [bm.verts.new(m @ Vector(v)) for v in verts]
    for idx, rol, col in caras:
        try:
            f = bm.faces.new([nv[i] for i in idx])
        except ValueError:                                   # cara repetida en el asset
            continue
        f.material_index = c._idx(rol, col)
    if encalado > 0:
        # el pie encalado rodea el tronco: radio medido en el propio asset a 0,5 m de altura
        cerca = [math.hypot(v[0], v[1]) * alto * ancho for v in verts if v[2] * alto < 0.6]
        r = (max(cerca) if cerca else 0.2) + 0.02
        c.cilindro(x, y, z - 0.04, z + encalado, r, "muro", "#f4f1ea", lados=10, radio_arriba=r * 0.95)
