"""Relleno de las CUADRAS reales (BASE, mitad de claude).

El lienzo no trae todos los edificios: en la imagen satelital las cuadras del centro están completamente construidas
(techos de teja, patios chicos), pero en el modelo quedan huecos entre las huellas — tanto en el interior de la
cuadra como, a veces, sobre la calle. El reparto agrupa huellas en "manzanas" M### que no cubren esos huecos.

Método: grilla de 1 m alineada con la trama de calles. Una celda es libre si
- no está en el corredor de ninguna calle real ni a menos de 0,3 m de él,
- no está dentro de ninguna huella (recortada),
- un rayo desde arriba no toca NINGUNA geometría ya modelada (de los dos agentes; incluye atrios, plazas, patios),
- no está en una plaza (P01, Plaza San Francisco),
- la manzana más cercana es de claude.
Las celdas libres se agrupan en rectángulos: los que tocan la calle llevan fachada sencilla hacia ella (casa colonial
de 1–2 plantas), los interiores son casas bajas con tejado o patios con algún árbol.
"""

import functools
import glob
import math
import os
import random
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import Constructor, altura_suelo  # noqa: E402
from kit.datos import RAIZ, _dentro, edificios_recortados, reparto  # noqa: E402

from base_mobiliario import dueno_en  # noqa: E402
from base_plazas import PLAZA_SF  # noqa: E402
from piezas_claude import arbol, casa_sencilla, fachada, tejado_dos_aguas  # noqa: E402

ANG = math.radians(40.0)          # rumbo de la trama (Junín/Arce ~40°, Ravelo ~130°)
# Zonas donde el relleno no pone casas: se declaran en reparto/manzanas.json → "zonas_sin_relleno" (una sola fuente
# para el relleno y para kit/calidad.py). tipo "vacio": nada; tipo "suelo": solo piso empedrado.
@functools.lru_cache(maxsize=None)
def _zonas(tipo):
    return [[tuple(p) for p in z["poligono"]] for z in reparto().get("zonas_sin_relleno", []) if z["tipo"] == tipo]


def _cerca(mid, caja, margen=60.0):
    """¿El modelo `mid` puede tocar la caja? Se decide con el reparto (centro de la manzana o polígono del espacio)."""
    if caja is None:
        return True
    rep = reparto()
    m = next((x for x in rep["manzanas"] if x["id"] == mid), None)
    if m:
        pts = [p for e in m["edificios"] for p in e["huella"]] or [m["centro"]]
    else:
        e = next((x for x in rep.get("espacios", []) if x["id"] == mid), None)
        if not e or not e.get("poligono"):
            return True
        pts = e["poligono"]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return not (max(xs) < caja[0] - margen or min(xs) > caja[2] + margen or max(ys) < caja[1] - margen
                or min(ys) > caja[3] + margen)


def _bvh_modelos(extra=(), caja=None):
    """BVH con los GLB exportados de los dos agentes (todos menos la BASE) para saber dónde ya hay algo modelado.
    caja (x0, y0, x1, y1): solo los modelos cercanos (teselas de la BASE). extra: objetos de la escena actual que
    también cuentan (relleno y plazas de la BASE, para los cables).
    (Antes cargaba solo M*.glb y P*.glb: el relleno no veía AMP_*, PEATONAL ni AMP_S y metía casas junto al templo.)"""
    antes = set(bpy.data.objects)
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb"))):
        mid = os.path.basename(ruta)[:-4]
        if mid.startswith("BASE") or not _cerca(mid, caja):
            continue
        bpy.ops.import_scene.gltf(filepath=ruta)
    nuevos = [o for o in set(bpy.data.objects) - antes if o.type == "MESH"] + list(extra)
    verts, polys = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in nuevos:
        me = o.evaluated_get(dg).to_mesh()
        mw = o.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        o.evaluated_get(dg).to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    for o in set(bpy.data.objects) - antes:
        bpy.data.objects.remove(o, do_unlink=True)
    return bvh


def construir_relleno(col, cs, agente="claude", caja=None):
    """caja (x0, y0, x1, y1): solo las celdas de esa tesela (BASE por teselas)."""
    z = reparto()["zona"]
    rnd = random.Random(f"relleno-base-{caja}")
    bvh = _bvh_modelos(caja=caja)
    en_caja = (lambda x, y: caja[0] <= x < caja[2] and caja[1] <= y < caja[3]) if caja else (lambda x, y: True)
    huellas = edificios_recortados()
    # espacios del reparto: no se rellenan, salvo las ampliaciones que el relleno completa (AMP_S: alrededor del
    # templo, la esquina y la plazuela solo hay terreno; el rayo desde arriba respeta lo modelado)
    RELLENAR = ("AMP_S",)
    plazas = [PLAZA_SF] + [e["poligono"] for e in reparto().get("espacios", [])
                           if e.get("poligono") and e["id"] not in RELLENAR]
    extra = [e["poligono"] for e in reparto().get("espacios", []) if e["id"] in RELLENAR and e.get("poligono")]
    ux, uy = math.sin(ANG), math.cos(ANG)
    vx, vy = -uy, ux
    # grilla que cubre la zona en coordenadas (u, v)
    esq = [(z["xmin"], z["ymin"]), (z["xmax"], z["ymin"]), (z["xmax"], z["ymax"]), (z["xmin"], z["ymax"])]
    esq += [tuple(p) for pol in extra for p in pol]
    us = [x * ux + y * uy for x, y in esq]
    vs = [x * vx + y * vy for x, y in esq]
    u0, v0 = min(us), min(vs)
    nu, nv = int(max(us) - u0) + 1, int(max(vs) - v0) + 1
    XY = lambda u, v: (ux * u + vx * v, uy * u + vy * v)

    def en_calle(x, y, margen):
        return any(C.cubre(x, y, C.w + margen) for C in cs)

    libre = bytearray(nu * nv)
    solo_suelo = []                                        # celdas de zonas "suelo" (sin casas, con piso)

    for i in range(nu):
        for j in range(nv):
            x, y = XY(u0 + i + 0.5, v0 + j + 0.5)
            if not en_caja(x, y):
                continue
            if not (z["xmin"] < x < z["xmax"] and z["ymin"] < y < z["ymax"]) and not any(_dentro(x, y, pol) for pol in extra):
                continue
            if en_calle(x, y, 0.3):
                continue
            # zonas sin relleno: la celda entera (centro y esquinas) debe quedar afuera
            esquinas = [XY(u0 + i + du, v0 + j + dv) for du in (0.0, 1.0) for dv in (0.0, 1.0)] + [(x, y)]
            if any(_dentro(px, py, r) for r in _zonas("vacio") for px, py in esquinas):
                continue
            if any(_dentro(x, y, r) for r in _zonas("suelo")):    # zonas de solo suelo: se empiedran aparte
                solo_suelo.append((i, j))
                continue
            if any(_dentro(x, y, p) for p in plazas):
                continue
            hit = bvh.ray_cast(Vector((x, y, 400.0)), Vector((0, 0, -1)), 800.0)
            if hit[0] is not None:
                continue
            libre[i * nv + j] = 1
    # quitar celdas dentro de huellas (rápido: por caja de cada huella)
    for h in huellas:
        hu = [p[0] * ux + p[1] * uy for p in h]
        hv = [p[0] * vx + p[1] * vy for p in h]
        for i in range(max(0, int(min(hu) - u0) - 1), min(nu, int(max(hu) - u0) + 2)):
            for j in range(max(0, int(min(hv) - v0) - 1), min(nv, int(max(hv) - v0) + 2)):
                if libre[i * nv + j]:
                    x, y = XY(u0 + i + 0.5, v0 + j + 0.5)
                    if _dentro(x, y, h):
                        libre[i * nv + j] = 0
    c = Constructor("BASE_relleno")
    usado = bytearray(nu * nv)
    casa = bytearray(nu * nv)          # celdas ocupadas por casas del relleno (para saber qué muros quedan a la vista)
    n_casas = n_patios = 0
    items = []
    # 1.ª pasada: rectángulos y qué va en cada uno (casa o patio)
    for i in range(nu):
        for j in range(nv):
            k = i * nv + j
            if not libre[k] or usado[k]:
                continue
            w = 0
            lim_w = rnd.randint(6, 12)
            while i + w < nu and w < lim_w and libre[(i + w) * nv + j] and not usado[(i + w) * nv + j]:
                w += 1
            h = 0
            lim_h = rnd.randint(6, 12)
            while j + h < nv and h < lim_h and all(libre[(i + t) * nv + j + h] and not usado[(i + t) * nv + j + h]
                                                   for t in range(w)):
                h += 1
            for t in range(w):
                for s in range(h):
                    usado[(i + t) * nv + j + s] = 1
            if w * h < 6 or min(w, h) < 2:
                continue
            pu0, pu1, pv0, pv1 = u0 + i + 0.05, u0 + i + w - 0.05, v0 + j + 0.05, v0 + j + h - 0.05
            rect = [XY(pu0, pv0), XY(pu1, pv0), XY(pu1, pv1), XY(pu0, pv1)]   # CCW
            cx, cy = XY((pu0 + pu1) / 2, (pv0 + pv1) / 2)
            # toda la zona (la BASE es de claude): al sur de Arenales también, porque codex no tiene relleno y los
            # huecos entre sus huellas quedaban sin suelo, algunos sobre la calle (recorrido 2026-11-13). Los templos y
            # atrios ya modelados no se tocan (el rayo desde arriba los encuentra) y se reservan los tramos con foto
            # que todavía no modeló nadie (RESERVAS).
            if any(_dentro(cx, cy, r) for r in _zonas("vacio")):
                continue
            # ¿algún lado toca la calle? (a 1,2 m hacia afuera del lado ya es corredor)
            lados_calle = []
            for a_, b_ in zip(rect, rect[1:] + rect[:1]):
                L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
                nx, ny = (b_[1] - a_[1]) / L, -(b_[0] - a_[0]) / L        # normal hacia afuera (CCW)
                mx, my = (a_[0] + b_[0]) / 2 + nx * 1.2, (a_[1] + b_[1]) / 2 + ny * 1.2
                if en_calle(mx, my, 0.0) and L >= 3:
                    lados_calle.append({"a": a_, "b": b_, "largo": L, "normal": (nx, ny), "i": len(lados_calle),
                                        "a_calle": True})
            es_casa = bool(lados_calle) or rnd.random() < 0.75
            if es_casa:
                for t in range(w):
                    for s in range(h):
                        casa[(i + t) * nv + j + s] = 1
            items.append((rect, w, h, cx, cy, lados_calle, es_casa))

    def _abierto(x, y, nx, ny):
        """Delante del muro (0,8–3 m) no hay huella, ni geometría modelada, ni otra casa del relleno."""
        for d in (0.8, 1.6, 3.0):
            px, py = x + nx * d, y + ny * d
            if en_calle(px, py, 0.0):
                return True
            if any(_dentro(px, py, o) for o in huellas):
                return False
            if bvh.ray_cast(Vector((px, py, 400.0)), Vector((0, 0, -1)), 800.0)[0] is not None:
                return False
            i_, j_ = int(px * ux + py * uy - u0), int(px * vx + py * vy - v0)
            if 0 <= i_ < nu and 0 <= j_ < nv and casa[i_ * nv + j_]:
                return False
        return True

    # 2.ª pasada: construir
    for rect, w, h, cx, cy, lados_calle, es_casa in items:
        if any(_dentro(cx, cy, r) for r in _zonas("suelo")):
            # Suelo continuo, sin viviendas, árboles ni volúmenes añadidos.
            # El resto de los GLB ya contiene los edificios documentados.
            ni, nj = max(1, math.ceil(w / 3)), max(1, math.ceil(h / 3))
            for i_ in range(ni):
                for j_ in range(nj):
                    puntos = []
                    for a_, b_ in ((i_, j_), (i_ + 1, j_), (i_ + 1, j_ + 1), (i_, j_ + 1)):
                        x_ = rect[0][0] + (rect[1][0] - rect[0][0]) * a_ / ni + (rect[3][0] - rect[0][0]) * b_ / nj
                        y_ = rect[0][1] + (rect[1][1] - rect[0][1]) * a_ / ni + (rect[3][1] - rect[0][1]) * b_ / nj
                        puntos.append((x_, y_, altura_suelo(x_, y_) + 0.13))
                    c.poligono(puntos, "adoquin", "#c9c0aa")
            n_patios += 1
            continue
        zs_ = [altura_suelo(*p) for p in rect]
        zb, zr = min(zs_), max(zs_)
        muro = rnd.choice(["#f6f4ef", "#f6f4ef", "#f4efe4", "#f3e6d3", "#efe3c4"])
        if es_casa:
            # muros que dan a un patio o a un espacio abierto cerca de la calle: ventanas, sin puertas
            # (recorrido a pie por Loa, 2026-11-13: quedaban muros ciegos de 8–10 m a la vista)
            vistos = []
            hechos = {(round(l["a"][0], 3), round(l["a"][1], 3)) for l in lados_calle}
            for a_, b_ in zip(rect, rect[1:] + rect[:1]):
                if (round(a_[0], 3), round(a_[1], 3)) in hechos:
                    continue
                L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
                if L < 3:
                    continue
                nx, ny = (b_[1] - a_[1]) / L, -(b_[0] - a_[0]) / L
                mx, my = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
                if en_calle(mx, my, 12.0) and _abierto(mx, my, nx, ny):
                    vistos.append({"a": a_, "b": b_, "largo": L, "normal": (nx, ny), "i": 0, "a_calle": True})
            pisos = 2 if lados_calle and rnd.random() < 0.6 else 1
            alto_piso = 4.2
            alto = pisos * alto_piso
            c.prisma(rect, zb - 0.5, zr + alto, "muro", muro, tapa=True)
            # cumbrera paralela al frente más largo a la calle (si no, el hastial y sus aleros asoman a la calle)
            frente = max(lados_calle, key=lambda l: l["largo"]) if lados_calle else None
            cum = (frente["b"][0] - frente["a"][0], frente["b"][1] - frente["a"][1]) if frente else None
            tejado_dos_aguas(c, rect, zr + alto, pendiente=rnd.choice([18, 22, 25]), vuelo=0.3,
                             hastial="muro", color_hastial=muro, alto_max=2.0, cumbrera=cum)
            for l in lados_calle:
                f = fachada(c, l)
                nvn = max(1, round(l["largo"] / 3.6))
                vanos = [l["largo"] * (q + 0.5) / nvn for q in range(nvn)]
                casa_sencilla(f, 0.0, l["largo"], pisos, alto_piso, zr - f.suelo, muro=("muro", muro),
                              zocalo_alto=rnd.choice([0.8, 1.0, 1.2]), vanos=vanos,
                              balcones=[v for v in vanos if rnd.random() < 0.4], puertas=vanos[::2],
                              remate="alero", desde=zb - 0.5 - f.suelo)
            for l in vistos:
                f = fachada(c, l)
                nvn = max(1, round(l["largo"] / 4.5))
                vanos = [l["largo"] * (q + 0.5) / nvn for q in range(nvn)]
                casa_sencilla(f, 0.0, l["largo"], pisos, alto_piso, zr - f.suelo, muro=("muro", muro),
                              zocalo_alto=0.9, vanos=vanos, balcones=[], puertas=[], remate="cornisa",
                              desde=zb - 0.5 - f.suelo, comercio=False)
            n_casas += 1
        else:
            c.tapa(rect, zr + 0.05, "adoquin", rnd.choice(["#c4ab90", "#b9a08a", "#cdb79c"]))
            if w * h > 16 and rnd.random() < 0.6:
                arbol(c, cx, cy, altura_suelo(cx, cy), alto=rnd.uniform(4.5, 7), copa=rnd.uniform(2.6, 4.2),
                      semilla=rnd.randint(0, 999))
            n_patios += 1
    # zonas "suelo": piso empedrado continuo donde no hay nada modelado (filas de celdas unidas)
    filas = {}
    for i, j in solo_suelo:
        x, y = XY(u0 + i + 0.5, v0 + j + 0.5)
        if bvh.ray_cast(Vector((x, y, 400.0)), Vector((0, 0, -1)), 800.0)[0] is None:
            filas.setdefault(j, []).append(i)
    for j, iis in filas.items():
        iis.sort()
        ini = prev = iis[0]
        for i in iis[1:] + [None]:
            if i is not None and i == prev + 1:
                prev = i
                continue
            pts = [XY(u0 + ini, v0 + j), XY(u0 + prev + 1, v0 + j), XY(u0 + prev + 1, v0 + j + 1), XY(u0 + ini, v0 + j + 1)]
            c.poligono([(px, py, altura_suelo(px, py) + 0.13) for px, py in pts], "adoquin", "#c9c0aa")
            if i is not None:
                ini = prev = i
    print(f"[BASE] relleno: {n_casas} casas, {n_patios} patios, {len(solo_suelo)} celdas de solo suelo")
    return [c.objeto(col)]
