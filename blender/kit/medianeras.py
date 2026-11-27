"""Recorte a medianeras al exportar (control de calidad, 2026-11-13).

Problema: cornisas, aleros, balcones, techos y volúmenes de un edificio se metían en el vecino ("siameses": el
usuario los vio como edificios que "quieren combinarse" en la transición). Regla: cada edificio vive dentro de su
huella; solo puede volar hasta VUELO_CALLE metros sobre los lados que dan a la calle (aleros, balcones, cornisas).

`exportar()` llama a `limpiar(col, mid)` antes de escribir el GLB: cada objeto de la colección cuya huella se conoce
(propiedad "huella" que pone `Constructor.objeto(..., huella=...)`, o nombre igual al id de un edificio de la manzana)
se corta con un plano vertical en cada lado convexo de su huella:
  - lado medianero (no da a la calle): plano sobre el lado (+2 cm);
  - lado a la calle: plano a VUELO_CALLE m afuera.
Los lados cóncavos no se cortan (un plano infinito amputaría otra ala del edificio).
"""

import json

import bmesh
import bpy
from mathutils import Vector

from . import datos

VUELO_CALLE = 1.0
HOLGURA = 0.02


def _ccw(h):
    h = [tuple(p[:2]) for p in h]
    if len(h) > 2 and h[0] == h[-1]:
        h = h[:-1]
    a = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(h, h[1:] + h[:1]))
    return h if a > 0 else list(reversed(h))


def planos(huella):
    """[(punto, normal hacia afuera)] de los lados convexos de la huella, corridos según den o no a la calle."""
    h = _ccw(huella)
    res = []
    for l in datos.lados(h):
        a, b, n = Vector((*l["a"], 0)), Vector((*l["b"], 0)), Vector((*l["normal"], 0))
        # convexo: todos los demás vértices quedan del lado de adentro
        if any((Vector((p[0], p[1], 0)) - a).dot(n) > 0.05 for p in h):
            continue
        d = VUELO_CALLE if l["a_calle"] else HOLGURA
        res.append((a + n * d, n))
    return res


def recortar(ob, huella):
    pl = planos(huella)
    if not pl or ob.type != "MESH":
        return 0
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    mw, mwi = ob.matrix_world, ob.matrix_world.inverted()
    antes = len(bm.faces)
    for co, no in pl:
        co_l = mwi @ co
        no_l = (mwi.to_3x3() @ no).normalized()
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co_l, plane_no=no_l, clear_outer=True)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return antes


def _dentro(x, y, pts):
    c = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def _dist_borde(x, y, pts):
    d = 1e9
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        ex, ey = x2 - x1, y2 - y1
        L2 = ex * ex + ey * ey or 1e-9
        t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / L2))
        d = min(d, ((x - x1 - t * ex) ** 2 + (y - y1 - t * ey) ** 2) ** 0.5)
    return d


def quitar_dentro_de_otros(ob, propia, ajenas, margen=0.15):
    """Borra las caras del objeto cuyo centro cae dentro de la huella de OTRO edificio (más de `margen` adentro):
    es geometría que se mete en el vecino y no se ve. Devuelve cuántas caras borró."""
    cajas = []
    for h in ajenas:
        xs, ys = [p[0] for p in h], [p[1] for p in h]
        cajas.append((min(xs), min(ys), max(xs), max(ys), h))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    borrar = []
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        if propia and _dentro(c.x, c.y, propia) and _dist_borde(c.x, c.y, propia) > margen:
            continue                                    # sigue dentro de su propia huella
        for x0, y0, x1, y1, h in cajas:
            if x0 < c.x < x1 and y0 < c.y < y1 and _dentro(c.x, c.y, h) and _dist_borde(c.x, c.y, h) > margen:
                borrar.append(f)
                break
    if borrar:
        bmesh.ops.delete(bm, geom=borrar, context="FACES")
        bm.to_mesh(ob.data)
        ob.data.update()
    bm.free()
    return len(borrar)


def limpiar(col, mid):
    """Recorta a medianeras todos los objetos de la colección con huella conocida. Devuelve cuántos recortó."""
    huellas = {}
    try:
        m = datos.manzana(mid) if hasattr(datos, "manzana") else None
    except Exception:
        m = None
    if m is None:
        rep = datos.reparto()
        m = next((x for x in rep["manzanas"] if x["id"] == mid), None)
    if m:
        huellas = {e["id"]: e["huella"] for e in m.get("edificios", [])}
    n = 0
    for ob in col.all_objects:
        h = None
        if "huella" in ob.keys():
            h = json.loads(ob["huella"])
        elif ob.name in huellas:
            h = datos.recortar_a_calles(huellas[ob.name]) or huellas[ob.name]
        if h and len(h) >= 3:
            recortar(ob, h)
            n += 1
    # lo que se mete en la huella de OTRO edificio (de esta u otra manzana) se borra
    rep = datos.reparto()
    todas = [(e["id"], e["huella"]) for x in rep["manzanas"] for e in x.get("edificios", [])]
    propias = {}
    for ob in col.all_objects:
        if ob.type != "MESH":
            continue
        if "huella" in ob.keys():
            propias[ob.name] = (json.loads(ob["huella"]), False)
        elif ob.name in huellas:
            propias[ob.name] = (huellas[ob.name], True)
    for ob in col.all_objects:
        if ob.name not in propias:
            continue                                     # mobiliario, techos, detalles: no se tocan
        propia, del_reparto = propias[ob.name]
        # objetos con huella propia (Peatonal, ampliaciones) reemplazan huellas viejas del lienzo: solo se comparan con
        # los demás objetos de su colección; los edificios del reparto, con todas las huellas del reparto
        ajenas = [h for n_, (h, _) in propias.items() if n_ != ob.name]
        if del_reparto:
            ajenas += [h for eid, h in todas if eid != ob.name and h != propia and eid not in propias]
        quitar_dentro_de_otros(ob, propia, ajenas)
    return n
