"""Detalles de fachada que se repiten en TODAS las calles de las fotos y que los scripts de manzana no ponen uno a uno:

- gárgolas: canaletas de madera/lata que asoman bajo el pretil de las casas de azotea (cada 3–4,5 m);
- cables por la fachada: 2–3 cables negros a 3,8–4,6 m, sujetos con grampas, con bajadas a los medidores;
- cajas de medidor de luz (blancas, a ~1,6 m) junto a las puertas;
- faroles de pared en algunas esquinas.

Se ejecuta DESPUÉS de construir la manzana: mira la geometría ya hecha (altura real de cada fachada, si tiene alero
de tejas) y agrega un objeto <MID>_detalles. Determinista (semilla = id del edificio + lado).

Uso (antes de exportar):  detallar(col, m)
"""

import math
import os
import random
import sys

import bpy
from mathutils import kdtree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import Constructor  # noqa: E402
from kit.datos import altura_suelo, lados  # noqa: E402

from base_mobiliario import cable  # noqa: E402

CABLE = "#2b2522"


def _nubes(col):
    """KD-trees 2D de todos los vértices de la colección (con su z) y de las caras de teja."""
    pts, zs, tejas, ztejas = [], [], [], []
    for ob in col.all_objects:
        if ob.type != "MESH":
            continue
        mw = ob.matrix_world
        me = ob.data
        vs = [mw @ v.co for v in me.vertices]
        for v in vs:
            pts.append((v.x, v.y))
            zs.append(v.z)
        mats = [m.name if m else "" for m in me.materials]
        for p in me.polygons:
            if p.material_index < len(mats) and mats[p.material_index].startswith("teja"):
                c = mw @ p.center
                tejas.append((c.x, c.y))
                ztejas.append(c.z)

    def arbol(lista):
        kd = kdtree.KDTree(max(1, len(lista)))
        for i, (x, y) in enumerate(lista):
            kd.insert((x, y, 0.0), i)
        kd.balance()
        return kd

    return arbol(pts), zs, arbol(tejas), ztejas


def bvh_coleccion(col):
    """BVH con toda la geometría ya construida de la colección (para rayos de choque)."""
    from mathutils.bvhtree import BVHTree
    verts, polys = [], []
    for ob in col.all_objects:
        if ob.type != "MESH":
            continue
        mw = ob.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in ob.data.vertices]
        polys += [[base + i for i in p.vertices] for p in ob.data.polygons]
    return BVHTree.FromPolygons(verts, polys) if polys else None


def _salientes(bvh, P, n, L, h, paso=0.4, desde=1.6):
    """Cuánto sobresale la fachada (m, hacia la calle) cada 'paso' a lo largo del lado, a la altura h: rayos desde
    'desde' m afuera hacia el muro. Sirve para que los cables rodeen pilastras y balcones y se corten en torres."""
    from mathutils import Vector
    out = []
    k = 0.0
    while k <= L + 1e-6:
        x, y = P(k, desde)
        hit = bvh.ray_cast(Vector((x, y, h)), Vector((-n[0], -n[1], 0.0)), desde + 0.5) if bvh else (None,)
        out.append((k, desde - hit[3] if hit[0] is not None else -0.5))
        k += paso
    return out


def detallar(col, m, cables_fachada=True):
    kd, zs, kdt, zt = _nubes(col)
    bvh = bvh_coleccion(col)
    c = Constructor(m["id"] + "_detalles")
    hubo = False
    for e in m["edificios"]:
        for l in lados(e["huella"]):
            if not l["a_calle"] or l["largo"] < 3.0:
                continue
            rnd = random.Random(f"{e['id']}-{l['i']}")
            ax, ay = l["a"]
            bx, by = l["b"]
            L = l["largo"]
            ux, uy = (bx - ax) / L, (by - ay) / L
            nx, ny = l["normal"]
            P = lambda s, d=0.0: (ax + ux * s + nx * d, ay + uy * s + ny * d)
            # altura real de la fachada (máximo z cerca de la línea) y si tiene alero de tejas
            tops = []
            for k in range(int(L) + 1):
                x, y = P(min(L, k + 0.5), -0.2)
                cerca = kd.find_range((x, y, 0.0), 0.6)
                if cerca:
                    tops.append(max(zs[i] for _, i, _ in cerca))
            if not tops:
                continue
            tops.sort()
            ztop = tops[len(tops) // 2]
            mx, my = P(L / 2)
            z0 = altura_suelo(mx, my)
            alto = ztop - z0
            if alto < 3.0:
                continue
            xa, ya = P(L / 2, 0.6)
            con_alero = any(abs(zt[i] - ztop) < 2.5 for _, i, _ in kdt.find_range((xa, ya, 0.0), 1.6))
            # --- gárgolas bajo el pretil
            # (solo casas de azotea de 1–2 plantas: en edificios altos o modernos quedaban sueltas a media fachada)
            if not con_alero and 5.0 < alto <= 9.5:
                s = rnd.uniform(1.0, 2.5)
                while s < L - 0.8:
                    x, y = P(s)
                    zg = ztop - rnd.uniform(0.5, 0.75)
                    # el pretil tiene que estar justo encima: si el muro local es más bajo o más alto, no va
                    cerca = kd.find_range((x, y, 0.0), 0.8)
                    zl = max((zs[i] for _, i, _ in cerca), default=-1e9)
                    if abs(zl - ztop) > 0.6:
                        s += rnd.uniform(3.0, 4.6)
                        continue
                    c.caja_ejes((x + nx * 0.32, y + ny * 0.32, zg), (nx, ny, 0), (ux, uy, 0), (0, 0, 1), 0.7, 0.13, 0.11,
                                "madera", rnd.choice(["#6b4a33", "#7d7a72", "#5b3a26"]))
                    s += rnd.uniform(3.0, 4.6)
                    hubo = True
            # --- cables sujetos a la fachada, con bajadas a los medidores. Coherencia (pedido del usuario): el cable
            # rodea lo que sobresale poco (pilastras, molduras, balcones bajos) separándose del muro, y donde hay un
            # cuerpo saliente grande (torre, torreón, contrafuerte > 0,6 m) termina en una grampa contra él en lugar de
            # atravesarlo.
            if cables_fachada and L >= 4:
                for k in range(rnd.randint(1, 3)):
                    h = z0 + min(alto - 1.2, rnd.uniform(3.7, 4.6)) + k * 0.12
                    d = 0.06 + 0.03 * k
                    perfil = _salientes(bvh, P, (nx, ny), L, h)
                    tramos, actual = [], []
                    for sk, pr in perfil:
                        if pr > 0.6:
                            if len(actual) >= 2:
                                tramos.append(actual)
                            actual = []
                        else:
                            actual.append((sk, pr))
                    if len(actual) >= 2:
                        tramos.append(actual)
                    for tr in tramos:
                        s0, s1 = tr[0][0] + 0.15, tr[-1][0] - 0.15
                        if s1 - s0 < 2.0:
                            continue
                        dd = max(d, max(pr for _, pr in tr) + 0.05)
                        s = s0
                        while s < s1 - 0.3:
                            s2 = min(s1, s + rnd.uniform(3.5, 6.0))
                            pa, pb = P(s, dd), P(s2, dd)
                            cable(c, (pa[0], pa[1], h), (pb[0], pb[1], h), rnd.uniform(0.04, 0.12), radio=0.014, segmentos=4)
                            # grampa que sujeta el cable al muro en cada apoyo
                            g = P(s, dd / 2)
                            c.caja_ejes((g[0], g[1], h + 0.02), (nx, ny, 0), (ux, uy, 0), (0, 0, 1), dd, 0.03, 0.03, "hierro")
                            s = s2
                        g = P(s1, dd / 2)
                        c.caja_ejes((g[0], g[1], h + 0.02), (nx, ny, 0), (ux, uy, 0), (0, 0, 1), dd, 0.03, 0.03, "hierro")
                        hubo = True
                # medidor de luz con su bajada
                if L >= 5:
                    sm = rnd.uniform(1.0, L - 1.0)
                    x, y = P(sm, 0.09)
                    zm = altura_suelo(x, y) + rnd.uniform(1.4, 1.8)
                    c.caja_ejes((x, y, zm), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 0.38, 0.18, 0.52, "moldura", "#e9e5dc")
                    c.caja_ejes((x + nx * 0.05, y + ny * 0.05, zm + 0.08), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 0.2, 0.12, 0.14,
                                "vidrio", "#4a5560")
                    xb, yb = P(sm, 0.07)
                    cable(c, (xb, yb, zm + 0.26), (xb, yb, z0 + 3.9), 0.0, radio=0.012, segmentos=1)
    if hubo:
        return c.objeto(col)
    c.bm.free()
    return None


def techos_con_patio(col, excluir=()):
    """Cambia las azoteas planas GRANDES ya construidas (rol azotea, mirando arriba) por techo de tejas con patio
    (`piezas_claude.techo_colonial`) cuando el contorno lo admite. excluir: prefijos de nombres de objeto que deben
    quedar con azotea (edificios modernos)."""
    import bmesh
    from kit.datos import altura_suelo as _alt
    from piezas_claude import techo_colonial, tejado_dos_aguas
    from generica import rectangularidad
    nuevo = Constructor("techos_patio")
    hubo = False
    for ob in list(col.all_objects):
        if ob.type != "MESH" or any(ob.name.startswith(e) for e in excluir):
            continue
        me = ob.data
        mats = [m.name if m else "" for m in me.materials]
        idx = {i for i, m in enumerate(mats) if m.startswith("azotea")}
        if not idx:
            continue
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        caras = {f for f in bm.faces if f.material_index in idx and f.normal.z > 0.95}
        borrar = []
        vistas = set()
        for f0 in caras:
            if f0 in vistas:
                continue
            # región conexa de caras de azotea a la misma altura
            reg, pila = set(), [f0]
            z0 = f0.calc_center_median().z
            while pila:
                f = pila.pop()
                if f in reg:
                    continue
                reg.add(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g in caras and g not in reg and abs(g.calc_center_median().z - z0) < 0.05:
                            pila.append(g)
            vistas |= reg
            area = sum(f.calc_area() for f in reg)
            if area < 30:
                continue
            borde = [e for e in {e for f in reg for e in f.edges} if sum(1 for g in e.link_faces if g in reg) == 1]
            # ordenar el borde en un solo lazo
            sig = {}
            for e in borde:
                a, b = e.verts
                sig.setdefault(a, []).append(b)
                sig.setdefault(b, []).append(a)
            if any(len(v) != 2 for v in sig.values()):
                continue
            inicio = borde[0].verts[0]
            lazo, prev, cur = [inicio], None, inicio
            while True:
                n = [v for v in sig[cur] if v is not prev]
                nxt = n[0] if n else None
                if nxt is None or nxt is inicio:
                    break
                lazo.append(nxt)
                prev, cur = cur, nxt
                if len(lazo) > len(sig):
                    break
            if len(lazo) != len(sig):
                continue                      # hay más de un lazo (agujeros): se deja la azotea
            mw = ob.matrix_world
            poly = [((mw @ v.co).x, (mw @ v.co).y) for v in lazo]
            zt = (mw @ lazo[0].co).z
            zp = min(_alt(x, y) for x, y in poly)
            if area >= 200 and techo_colonial(nuevo, poly, zt + 0.02, zp, vuelo=0.0):
                borrar += list(reg)
                hubo = True
            elif rectangularidad(poly) > 0.85:
                # casa angosta: tejado bajo a dos aguas detrás del pretil (en el satélite casi todo es teja)
                tejado_dos_aguas(nuevo, poly, zt + 0.02, pendiente=20, vuelo=0.0, alto_max=1.8)
                nuevo.tapa(poly, zt + 0.01, "muro")
                borrar += list(reg)
                hubo = True
        if borrar:
            bmesh.ops.delete(bm, geom=borrar, context="FACES_ONLY")
            bm.to_mesh(me)
            me.update()
        bm.free()
    if hubo:
        return nuevo.objeto(col)
    nuevo.bm.free()
    return None


def relleno_manzana(col, m, celda=1.0, semilla=None):
    """Rellena el INTERIOR de la manzana donde el lienzo no trae edificios: en la imagen satelital las manzanas del
    centro están completamente construidas (casas de una o dos plantas con techo de tejas y patios chicos).

    Rasteriza la manzana (recortada a las calles reales) en una grilla alineada con su lado más largo, marca lo libre
    (fuera de toda huella y a más de 4 m de la calle, para no tapar fachadas) y lo cubre con rectángulos: ~75 %
    casas bajas con tejado a dos aguas, el resto patios con piso y a veces un árbol.

    DESACTIVADO (2026-11-13, control de calidad): rellenaba la envolvente convexa de cada manzana y se metía en las
    vecinas (edificios "siameses" entre manzanas). El interior de las cuadras lo rellena UNA sola fuente: el relleno de
    la BASE (base_relleno.py), que respeta todo lo modelado de los dos agentes."""
    return None
    import json as _json
    from kit.datos import RAIZ, _dentro, altura_suelo as _alt, calle_real_cercana, edificios_recortados, recortar_a_calles
    from piezas_claude import arbol, tejado_dos_aguas
    hm = _json.load(open(os.path.join(RAIZ, "web", "public", "mapa", "huellas_manzanas.json")))
    # contorno de la manzana: envolvente convexa de todas sus huellas, recortada al ancho real de las calles
    pts = sorted({(round(q[0], 2), round(q[1], 2)) for p in hm.get(m["id"], []) for q in p})
    if len(pts) < 3:
        return None

    def cruz(o, a_, b_):
        return (a_[0] - o[0]) * (b_[1] - o[1]) - (a_[1] - o[1]) * (b_[0] - o[0])
    inf, sup = [], []
    for q in pts:
        while len(inf) >= 2 and cruz(inf[-2], inf[-1], q) <= 0:
            inf.pop()
        inf.append(q)
    for q in reversed(pts):
        while len(sup) >= 2 and cruz(sup[-2], sup[-1], q) <= 0:
            sup.pop()
        sup.append(q)
    casco = inf[:-1] + sup[:-1]
    polis = [p for p in [recortar_a_calles(casco, area_min=30)] if p]
    if not polis:
        return None
    rnd = random.Random(semilla or m["id"])
    huellas = edificios_recortados()
    bvh = bvh_coleccion(col)  # lo ya modelado en la manzana (atrios, templos, huellas propias): no se tapa
    from mathutils import Vector as _V
    c = Constructor(m["id"] + "_relleno")
    hubo = False
    for P in polis:
        a, b = max(zip(P, P[1:] + P[:1]), key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        vx, vy = -uy, ux
        us = [(p[0] - a[0]) * ux + (p[1] - a[1]) * uy for p in P]
        vs = [(p[0] - a[0]) * vx + (p[1] - a[1]) * vy for p in P]
        u0, v0 = min(us), min(vs)
        nu, nv = int((max(us) - u0) / celda) + 1, int((max(vs) - v0) / celda) + 1
        bx0, bx1 = min(p[0] for p in P) - 1, max(p[0] for p in P) + 1
        by0, by1 = min(p[1] for p in P) - 1, max(p[1] for p in P) + 1
        cerca = [h for h in huellas if max(q[0] for q in h) > bx0 and min(q[0] for q in h) < bx1
                 and max(q[1] for q in h) > by0 and min(q[1] for q in h) < by1]
        XY = lambda i, j: (a[0] + ux * (u0 + (i + 0.5) * celda) + vx * (v0 + (j + 0.5) * celda),
                           a[1] + uy * (u0 + (i + 0.5) * celda) + vy * (v0 + (j + 0.5) * celda))
        libre = [[False] * nv for _ in range(nu)]
        for i in range(nu):
            for j in range(nv):
                x, y = XY(i, j)
                if not _dentro(x, y, P):
                    continue
                cr = calle_real_cercana(x, y)
                if cr and cr[0] < cr[1] / 2 + 4.0:
                    continue
                if any(_dentro(x, y, h) for h in cerca):
                    continue
                if bvh and bvh.ray_cast(_V((x, y, 600.0)), _V((0, 0, -1)), 1200.0)[0] is not None:
                    continue
                libre[i][j] = True
        # rectángulos voraces
        usado = [[False] * nv for _ in range(nu)]
        for i in range(nu):
            for j in range(nv):
                if not libre[i][j] or usado[i][j]:
                    continue
                w = 0
                while i + w < nu and libre[i + w][j] and not usado[i + w][j] and w < rnd.randint(7, 14):
                    w += 1
                h = 0
                while j + h < nv and h < rnd.randint(6, 12) and all(libre[i + k][j + h] and not usado[i + k][j + h] for k in range(w)):
                    h += 1
                for k in range(w):
                    for t in range(h):
                        usado[i + k][j + t] = True
                if w * h * celda * celda < 9 or min(w, h) * celda < 2.5:
                    continue
                pu0, pu1 = u0 + i * celda + 0.15, u0 + (i + w) * celda - 0.15
                pv0, pv1 = v0 + j * celda + 0.15, v0 + (j + h) * celda - 0.15
                Q = lambda uu, vv: (a[0] + ux * uu + vx * vv, a[1] + uy * uu + vy * vv)
                rect = [Q(pu0, pv0), Q(pu1, pv0), Q(pu1, pv1), Q(pu0, pv1)]
                zs = [_alt(*p) for p in rect]
                zb, zr = min(zs), max(zs)
                if rnd.random() < 0.75:
                    alto = rnd.choice([3.6, 4.0, 4.4, 6.5])
                    muro = rnd.choice(["#f4f1ea", "#f1e9da", "#ece3d2", "#f3e6d3"])
                    c.prisma(rect, zb - 0.5, zr + alto, "muro", muro, tapa=True)
                    if rnd.random() < 0.85:
                        tejado_dos_aguas(c, rect, zr + alto, pendiente=rnd.choice([18, 22, 25]), vuelo=0.25,
                                         hastial="muro", color_hastial=muro, alto_max=2.0)
                else:
                    c.tapa(rect, zr + 0.05, "adoquin", rnd.choice(["#c4ab90", "#b9a08a", "#cdb79c"]))
                    if rnd.random() < 0.5 and w * h > 16:
                        x, y = Q((pu0 + pu1) / 2, (pv0 + pv1) / 2)
                        arbol(c, x, y, _alt(x, y), alto=rnd.uniform(4.5, 7), copa=rnd.uniform(2.6, 4.2), semilla=rnd.randint(0, 999))
                hubo = True
    if hubo:
        return c.objeto(col)
    c.bm.free()
    return None
