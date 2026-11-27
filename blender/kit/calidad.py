"""Control de calidad automático de la ciudad (pedido del usuario, 2026-11-13: "que en el futuro no se pueda repetir").

Carga los GLB exportados y busca, con geometría real, los errores que el usuario encontró caminando:

  MURO_LIENZO     volumen genérico del lienzo (muro blanco por defecto) que el visor NO oculta y que pisa algo modelado
  CABLE_MURO      un cable atraviesa un muro, techo o torre
  POSTE_PEGADO    un poste/farol a menos de 0,35 m de una pared, o dentro de un edificio
  ARBOL_FLOTA     un árbol cuyo tronco no apoya en el suelo (> 0,3 m)
  ARBOL_MURO      la copa o el tronco de un árbol dentro de un edificio
  SIAMESES        dos edificios de objetos distintos que se interpenetran (no solo se tocan)
  RELLENO_PROHIB  casa de relleno genérico dentro de una zona marcada "sin_relleno" en el reparto
  VEREDA_ANGOSTA  calle con vereda < VEREDA_MIN

Uso:
  blender -b -P blender/kit/calidad.py -- <agente|todos> [ID ...]        (ID = M###, AMP_*, BASE, PEATONAL…)
Salida: revisiones/<agente>/calidad.txt (una línea por hallazgo, con coordenadas) y un resumen por tipo.
Regla (AGENTS.md): no se commitea un GLB con hallazgos nuevos de estos tipos.
"""

import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit.datos import RAIZ, altura_suelo, calles_reales  # noqa: E402

VEREDA_MIN = 2.0
TODO_BVH = None
MOBILIARIO = ("cables", "postes", "semaforo", "vereda", "puesto", "letrero", "pino", "arbol", "carpa", "plaza",
              "BASE_piso", "BASE_calzada", "BASE_marcas", "explanada", "atrio", "detalles", "mirador")
# partes de un edificio que se apoyan en sus muros (no cuentan como "siameses" con su propio edificio)
PARTES = ("techos_patio", "_detalles", "_mirador")


# ---------------------------------------------------------------------------------------------------- carga
def cargar(agente, ids):
    objs = []
    rutas = sorted(glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb")))
    for r in rutas:
        ag, mid = r.split(os.sep)[-2], os.path.basename(r)[:-4]
        if ids and mid not in ids:
            continue
        if agente not in ("todos", ag) and mid != "BASE" and not ids:
            continue
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=r)
        for o in set(bpy.data.objects) - antes:
            o["glb"], o["agente"] = mid, ag
            if o.type == "MESH":
                objs.append(o)
    return objs


def islas(o):
    """Componentes conexas de la malla (en coordenadas del mundo): [(verts, caras_material)]."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    bm.verts.ensure_lookup_table()
    mats = [m.name.split("__")[0] if m else "" for m in o.data.materials]
    vistos, res = set(), []
    for f0 in bm.faces:
        if f0.index in vistos:
            continue
        pila, caras = [f0], []
        vistos.add(f0.index)
        while pila:
            f = pila.pop()
            caras.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in vistos:
                        vistos.add(g.index)
                        pila.append(g)
        vs = {v.index: v.co.copy() for f in caras for v in f.verts}
        res.append((list(vs.values()), Counter(mats[f.material_index] if f.material_index < len(mats) else "" for f in caras)))
    bm.free()
    return res


def bvh_de(objs):
    verts, polys = [], []
    for o in objs:
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[b + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys) if polys else None


def es_mobiliario(o):
    n = o.name.lower()
    return any(k.lower() in n for k in MOBILIARIO)


# ---------------------------------------------------------------------------------------------------- chequeos
def dentro_poly(x, y, pts):
    c = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def chequeo_muro_lienzo(edif_bvh, cargados):
    """Volúmenes del lienzo que el visor deja visibles (fuera de la zona y de las huellas de lo cargado) y que tocan
    geometría modelada."""
    rep = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))
    z = rep["zona"]
    huellas = json.load(open(os.path.join(RAIZ, "web", "public", "mapa", "huellas_manzanas.json")))
    polis = [p for k in cargados for p in huellas.get(k, [])]
    out = []
    for e in json.load(open(os.path.join(RAIZ, "reparto", "edificios_lienzo.json"))):
        h = e["huella"]
        cx = sum(p[0] for p in h) / len(h)
        cy = sum(p[1] for p in h) / len(h)
        if z["xmin"] <= cx <= z["xmax"] and z["ymin"] <= cy <= z["ymax"]:
            continue                                        # dentro de la zona la BASE oculta todo el lienzo
        if any(dentro_poly(cx, cy, p) for p in polis):
            continue
        # ¿hay algo modelado dentro de este volumen? (rayos desde arriba en sus vértices y centro)
        zt = altura_suelo(cx, cy) + e.get("altura", 9) - 0.5
        for x, y in [(cx, cy)] + [((p[0] * 3 + cx) / 4, (p[1] * 3 + cy) / 4) for p in h]:
            r = edif_bvh.ray_cast(Vector((x, y, zt + 60)), Vector((0, 0, -1)), 200) if edif_bvh else (None,)
            if r[0] is not None and r[0].z > altura_suelo(x, y) + 1.0:
                out.append(("MURO_LIENZO", "lienzo", f"alto {e.get('altura')}", x, y, r[0].z, "volumen del lienzo visible sobre un modelo"))
                break
    return out


def chequeo_cables(cables, solidos_bvh):
    out = []
    for o in cables:
        for verts, _ in islas(o):
            if len(verts) < 6:
                continue
            # eje del cable: puntos ordenados por la dirección principal
            a = min(verts, key=lambda v: (v.x, v.y))
            b = max(verts, key=lambda v: (v - a).length)
            d = b - a
            L = d.length
            if L < 1.0:
                continue
            d.normalize()
            # el tramo central (sin los 0,4 m de cada punta, donde el cable se ancla) no debe tocar nada sólido
            p0 = a + d * 0.4
            r = solidos_bvh.ray_cast(p0, d, L - 0.8) if solidos_bvh else (None,)
            if r[0] is not None:
                out.append(("CABLE_MURO", o.get("glb"), o.name, r[0].x, r[0].y, r[0].z, f"cable de {L:.1f} m"))
    return out


def _apoya_en(o, c, z):
    """¿Hay otra pieza del mismo objeto justo debajo (cantero, maceta, tramo inferior del tronco de una palmera)?"""
    mw = o.matrix_world
    for v in o.data.vertices:
        w = mw @ v.co
        if abs(w.x - c[0]) < 0.6 and abs(w.y - c[1]) < 0.6 and z - 0.4 < w.z < z + 0.05 and (w.z < z - 0.01 or abs(w.x - c[0]) > 0.05):
            return True
    return False


def chequeo_postes_y_arboles(mobs, solidos_bvh):
    """Postes (islas finas y altas), troncos (islas de rol tronco) y copas (islas de rol follaje)."""
    out = []

    def roza(c, h, alcance, n=8):
        for a in range(0, 360, 360 // n):
            v = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
            r = solidos_bvh.ray_cast(Vector((c[0], c[1], h)), v, alcance) if solidos_bvh else (None,)
            if r[0] is not None:
                return r[0]
        return None

    for o in mobs:
        for verts, mats in islas(o):
            xs = [v.x for v in verts]
            ys = [v.y for v in verts]
            zs = [v.z for v in verts]
            dx, dy, dz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
            c = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
            z0 = altura_suelo(*c)
            rol = mats.most_common(1)[0][0] if mats else ""
            if rol == "tronco" and dz > 1.2 and max(dx, dy) < 1.2:
                apoyo = TODO_BVH.ray_cast(Vector((c[0], c[1], min(zs) + 0.05)), Vector((0, 0, -1)), 0.4) if solidos_bvh else (None,)
                if min(zs) - z0 > 0.3 and apoyo[0] is None and not _apoya_en(o, c, min(zs)):
                    out.append(("ARBOL_FLOTA", o.get("glb"), o.name, c[0], c[1], min(zs), f"{min(zs) - z0:.1f} m sobre el suelo"))
                if roza(c, min(zs) + 1.2, max(dx, dy) / 2 + 0.15):
                    out.append(("ARBOL_MURO", o.get("glb"), o.name, c[0], c[1], min(zs), "tronco contra un muro"))
            elif rol.startswith("follaje") and max(dx, dy) > 0.8:
                r = max(dx, dy) / 2
                h = (max(zs) + min(zs)) / 2
                golpes = 0
                for a in range(0, 360, 45):
                    v = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
                    q = solidos_bvh.ray_cast(Vector((c[0], c[1], h)), v, r * 0.6) if solidos_bvh else (None,)
                    golpes += q[0] is not None
                if golpes >= 2:
                    out.append(("ARBOL_MURO", o.get("glb"), o.name, c[0], c[1], h, "copa metida en un muro"))
            # un poste tiene grosor (fustes de 8 cm o más); una isla de menos de 3 cm es un cable (p. ej. la bajada vertical
            # de un medidor de luz pegada al muro) y no cuenta como poste (pedido del usuario, 2026-11-23)
            elif (rol in ("hierro", "piedra", "metal", "madera") and dz > 2.8 and max(dx, dy) < 1.6 and min(dx, dy) < 0.7
                  and max(dx, dy) >= 0.03):
                arriba = solidos_bvh.ray_cast(Vector((c[0], c[1], min(zs) + 1.0)), Vector((0, 0, 1)), 40) if solidos_bvh else (None,)
                if arriba[0] is not None and arriba[0].z > max(zs) + 0.3:
                    out.append(("POSTE_PEGADO", o.get("glb"), o.name, c[0], c[1], min(zs), "poste dentro de un edificio"))
                elif roza(c, min(zs) + 1.5, 0.35 + max(dx, dy) / 2):
                    out.append(("POSTE_PEGADO", o.get("glb"), o.name, c[0], c[1], min(zs), "a menos de 0,35 m de una pared"))
    return out


def _dentro_malla(bvh, p, caja):
    """Punto encerrado por la malla en las cuatro direcciones horizontales (robusto con mallas sin tapa: los volúmenes
    se exportan abiertos arriba y abajo, y la paridad de cruces fallaba)."""
    if not (caja[0] < p.x < caja[3] and caja[1] < p.y < caja[4] and caja[2] < p.z < caja[5]):
        return False
    for d in ((1, 0.001, 0), (-1, -0.001, 0), (0.001, 1, 0), (-0.001, -1, 0)):
        if bvh.ray_cast(p, Vector(d).normalized(), 200.0)[0] is None:
            return False
    return True


def chequeo_siameses(edificios, prof=0.2):
    """Edificios (objetos distintos) que se INTERPENETRAN: vértices de uno metidos más de `prof` m dentro del otro.
    Tocarse pared con pared es normal y no cuenta."""
    out = []
    datos_ = []
    for o in edificios:
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        if not vs:
            continue
        caja = (min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs),
                max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs))
        datos_.append((o, vs[:: max(1, len(vs) // 400)], bvh_de([o]), caja))
    for i, (oi, vi, bi, ci) in enumerate(datos_):
        for j, (oj, vj, bj, cj) in enumerate(datos_):
            if j <= i or ci[3] < cj[0] or cj[3] < ci[0] or ci[4] < cj[1] or cj[4] < ci[1]:
                continue
            if any(k in oi.name or k in oj.name for k in PARTES) and oi.get("glb") == oj.get("glb"):
                continue
            hondos = []
            for (va, bb, cb) in ((vi, bj, cj), (vj, bi, ci)):
                for v in va:
                    if v.z < altura_suelo(v.x, v.y) + 0.1:      # cimientos y zócalos enterrados: no se ven
                        continue
                    if _dentro_malla(bb, v, cb):
                        q = bb.find_nearest(v)
                        if q[0] is not None and q[3] > prof:
                            hondos.append(v)
            if len(hondos) >= 3:
                c = hondos[0]
                out.append(("SIAMESES", f"{oi.get('glb')}/{oj.get('glb')}", f"{oi.name} × {oj.name}", c.x, c.y, c.z,
                            f"{len(hondos)} vértices metidos > {prof} m"))
    return out


def chequeo_relleno(objs):
    """Paredes de casas de relleno dentro de zonas "sin_relleno" del reparto (por cara, no por isla)."""
    rep = json.load(open(os.path.join(RAIZ, "reparto", "manzanas.json")))
    zonas = [z["poligono"] for z in rep.get("zonas_sin_relleno", [])]
    out = []
    for o in objs:
        if not o.name.startswith("BASE_relleno"):
            continue
        mw = o.matrix_world
        mats = [m.name.split("__")[0] if m else "" for m in o.data.materials]
        for f in o.data.polygons:
            if mats[f.material_index] != "muro" or abs(f.normal.z) > 0.3:
                continue
            c = mw @ f.center
            if c.z < altura_suelo(c.x, c.y) + 0.5:
                continue
            if any(dentro_poly(c.x, c.y, p) for p in zonas):
                out.append(("RELLENO_PROHIB", "BASE", o.name, c.x, c.y, c.z, "pared de relleno en zona sin relleno"))
    return out


def chequeo_veredas():
    return [("VEREDA_ANGOSTA", "calles", c["nombre"], c["eje"][0][0], c["eje"][0][1], 0.0, f"vereda {c['vereda']} m")
            for c in calles_reales() if min(c["vereda"], c.get("vereda_izq", 99), c.get("vereda_der", 99)) < VEREDA_MIN]


# ---------------------------------------------------------------------------------------------------- principal
def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["todos"]
    agente, ids = args[0], set(args[1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = cargar(agente, ids)
    cargados = {o.get("glb") for o in objs}
    cables = [o for o in objs if "cable" in o.name.lower()]
    mobs = [o for o in objs if es_mobiliario(o) and "cable" not in o.name.lower()]
    edificios = [o for o in objs if not es_mobiliario(o) and not o.name.startswith("BASE_")]
    solidos = [o for o in objs if not es_mobiliario(o)]
    solidos_bvh = bvh_de(solidos)
    global TODO_BVH
    TODO_BVH = bvh_de(objs)                                # para apoyos (pisos de plazas, canteros)
    hall = []
    hall += chequeo_muro_lienzo(bvh_de(edificios), cargados)
    hall += chequeo_cables(cables, solidos_bvh)
    hall += chequeo_postes_y_arboles(mobs, solidos_bvh)
    hall += chequeo_siameses(edificios)
    hall += chequeo_relleno(objs)
    hall += chequeo_veredas()
    vistos, unicos = set(), []
    for h in hall:                                         # un hallazgo por tipo y metro cuadrado
        k = (h[0], h[2], round(h[3]), round(h[4]))
        if k not in vistos:
            vistos.add(k)
            unicos.append(h)
    hall = unicos
    salida = os.path.join(RAIZ, "revisiones", agente if agente != "todos" else "claude", "calidad.txt")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w") as fh:
        for t, g, n, x, y, zz, d in hall:
            fh.write(f"{t}\t{g}\t{n}\t({x:.1f}, {y:.1f}, {zz:.1f})\t{d}\n")
    res = Counter(h[0] for h in hall)
    print("[calidad] resumen:", dict(res), "→", salida)


main()
