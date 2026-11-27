"""Construcción en Blender de una SECCIÓN a partir de su trazado (trazado.py): suelo continuo que sigue el terreno
(calzada, veredas, bordillos), y mobiliario colocado sobre el bordillo de ESA sección. Los edificios ya modelados se
conservan tal cual (salvados); lo que cada sección agregue a mano va en su propio script.

Alturas: calzada a +0,07 m del terreno del lienzo, vereda a +0,25 m (las mismas que la BASE: las costuras coinciden).
"""

import math
import os
import sys

import bpy
import shapely
from mathutils import Vector
from shapely.geometry import Point, Polygon, box

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Constructor, altura_suelo  # noqa: E402

SOBRE = 0.07
ALTO_VEREDA = 0.18
CELDA = 3.0
COLORES = {"calzada": "#77706b", "vereda": "#bfbab2", "bordillo": "#b3aca3", "amarillo": "#e0b43a"}


def _poligonos(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon" and not p.is_empty]


def superficie(c, geom, rol, color, dz):
    """Malla de la geometría partida en celdas de CELDA m (sigue el terreno), triángulos mirando hacia arriba."""
    x0, y0, x1, y1 = geom.bounds
    n = 0
    gx = math.floor(x0 / CELDA) * CELDA
    while gx < x1:
        gy = math.floor(y0 / CELDA) * CELDA
        while gy < y1:
            pedazo = geom.intersection(box(gx, gy, gx + CELDA, gy + CELDA))
            for p in _poligonos(pedazo):
                tris = shapely.constrained_delaunay_triangles(p)
                for t in tris.geoms:
                    q = list(t.exterior.coords)[:3]
                    if (q[1][0] - q[0][0]) * (q[2][1] - q[0][1]) - (q[1][1] - q[0][1]) * (q[2][0] - q[0][0]) < 0:
                        q = [q[0], q[2], q[1]]
                    c.poligono([(x, y, altura_suelo(x, y) + dz) for x, y in q], rol, color)
                    n += 1
            gy += CELDA
        gx += CELDA
    return n


def bordillos(c, vereda, calzada, plaza):
    """Cara vertical del bordillo en cada tramo del borde de la vereda que da a la calzada o a la plaza."""
    zc, zv = SOBRE - 0.05, SOBRE + ALTO_VEREDA
    tramos = []
    for p in _poligonos(vereda):
        for anillo in [p.exterior] + list(p.interiors):
            pts = list(anillo.coords)
            for a, b in zip(pts, pts[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L < 1e-3:
                    continue
                m = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                if m.distance(calzada) > 0.05 and m.distance(plaza) > 0.05:
                    continue
                nx, ny = (b[1] - a[1]) / L, -(b[0] - a[0]) / L
                if not calzada.buffer(0.01).contains(Point(m.x + nx * 0.1, m.y + ny * 0.1)) and \
                        not plaza.buffer(0.01).contains(Point(m.x + nx * 0.1, m.y + ny * 0.1)):
                    a, b = b, a
                za, zb = altura_suelo(*a), altura_suelo(*b)
                c.poligono([(a[0], a[1], za + zc), (b[0], b[1], zb + zc), (b[0], b[1], zb + zv), (a[0], a[1], za + zv)],
                           "piedra", COLORES["bordillo"])
                tramos.append((a, b))
    return tramos


def suelo(nombre_obj, g, col):
    c = Constructor(nombre_obj + "_calzada")
    n1 = superficie(c, g["calzada"], "calzada", COLORES["calzada"], SOBRE + 0.003)
    c.objeto(col)
    c = Constructor(nombre_obj + "_veredas")
    n2 = superficie(c, g["vereda"], "vereda", COLORES["vereda"], SOBRE + ALTO_VEREDA + 0.003)
    tramos = bordillos(c, g["vereda"], g["calzada"], g["plaza"])
    c.objeto(col)
    if not g["plaza"].is_empty:
        # fondo bajo la plaza: el pavimento de P01 (a +0,14 m) redondea las esquinas de su polígono y entre él y la vereda
        # de la sección quedaban huecos negros (revisión por MCP, 2026-11-24). Queda debajo de todo lo demás.
        c = Constructor(nombre_obj + "_fondo_plaza")
        superficie(c, g["plaza"].buffer(0.6, join_style="mitre").difference(g["calzada"]).intersection(g["limite"]),
                   "vereda", COLORES["vereda"], SOBRE + 0.02)
        c.objeto(col)
    print(f"[seccion] suelo: {n1} triángulos de calzada, {n2} de vereda, {len(tramos)} tramos de bordillo")
    return tramos


def linea_de_bordillo(vereda, calzada, retiro):
    """Recorridos (listas de puntos) a `retiro` m del bordillo, dentro de la vereda, solo frente a la calzada."""
    interior = vereda.buffer(-retiro, join_style="round")
    res = []
    for p in _poligonos(interior):
        for anillo in [p.exterior] + list(p.interiors):
            pts = list(anillo.coords)
            actual = []
            for q in pts:
                if Point(q).distance(calzada) < retiro + 0.15:
                    actual.append(q)
                elif len(actual) > 1:
                    res.append(actual)
                    actual = []
                else:
                    actual = []
            if len(actual) > 1:
                res.append(actual)
    return res


def a_lo_largo(recorrido, paso, inicio):
    """Puntos cada `paso` m sobre el recorrido, con su dirección."""
    out, acum, sig = [], 0.0, inicio
    for a, b in zip(recorrido, recorrido[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        while sig <= acum + L and L > 1e-6:
            t = (sig - acum) / L
            out.append(((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)))
            sig += paso
        acum += L
    return out


def bvh_modelos(caja, excluir=("BASE",)):
    """BVH de lo ya exportado (de los dos agentes) cerca de la caja, para no chocar con muros ni balcones."""
    import glob
    from mathutils.bvhtree import BVHTree
    import bmesh
    from kit.datos import RAIZ, reparto
    rep = reparto()
    antes = set(bpy.data.objects)
    for r in glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "*.glb")):
        mid = os.path.basename(r)[:-4]
        if mid in excluir or mid.startswith("S_"):
            continue
        m = next((x for x in rep["manzanas"] if x["id"] == mid), None) or \
            next((x for x in rep.get("espacios", []) if x["id"] == mid), None)
        pts = ([p for e in m["edificios"] for p in e["huella"]] if m and m.get("edificios") else
               (m.get("poligono") if m else None))
        if not pts:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) < caja[0] - 20 or min(xs) > caja[2] + 20 or max(ys) < caja[1] - 20 or min(ys) > caja[3] + 20:
            continue
        bpy.ops.import_scene.gltf(filepath=r)
    nuevos = [o for o in set(bpy.data.objects) - antes if o.type == "MESH"]
    bm = bmesh.new()
    dg = bpy.context.evaluated_depsgraph_get()
    for o in nuevos:
        me = o.evaluated_get(dg).to_mesh()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
    bvh = BVHTree.FromBMesh(bm)
    for o in set(bpy.data.objects) - antes:
        bpy.data.objects.remove(o, do_unlink=True)
    return bvh


def libre(bvh, x, y, radio=0.7):
    z = altura_suelo(x, y)
    for h in (0.6, 1.6, 2.8, 4.0):
        hit = bvh.find_nearest(Vector((x, y, z + h)), radio)
        if hit[0] is not None:
            return False
    return True


def cebras(c, g, retiro=2.2, largo=3.0):
    """Paso de cebra en cada calle de la sección, justo antes de cada cruce: franjas de 0,5 m cada 1 m, de bordillo a
    bordillo (recortadas a la calzada real)."""
    from shapely.geometry import LineString
    calles = [(n, LineString(e), w) for n, e, w in g["calles"]]
    hechas, pasos = [], []
    n = 0
    for i, (na, la, wa) in enumerate(calles):
        for j, (nb, lb, wb) in enumerate(calles):
            if i == j:
                continue
            x = la.intersection(lb)
            if x.is_empty or x.geom_type != "Point":
                continue
            # la calle `a` se cruza a (medio ancho de b + retiro) del cruce, a cada lado
            for sg in (-1, 1):
                s = la.project(x) + sg * (wb + retiro + largo / 2)
                if s < 0 or s > la.length:
                    continue
                p = la.interpolate(s)
                q = la.interpolate(min(la.length, s + 0.5)) if s + 0.5 <= la.length else la.interpolate(s - 0.5)
                ux, uy = q.x - p.x, q.y - p.y
                L = math.hypot(ux, uy) or 1
                ux, uy = ux / L, uy / L
                if s + 0.5 > la.length:
                    ux, uy = -ux, -uy
                if any(math.hypot(p.x - a, p.y - b) < 4 for a, b in hechas) or not g["calzada"].contains(p):
                    continue
                vx, vy = -uy, ux
                # un paso nuevo no puede cruzarse con otro ya dibujado (R0168: dos cebras en X en la esquina de la plaza)
                huella_paso = Polygon([(p.x + vx * (-wa - 1) - ux * largo / 2, p.y + vy * (-wa - 1) - uy * largo / 2),
                                       (p.x + vx * (wa + 1) - ux * largo / 2, p.y + vy * (wa + 1) - uy * largo / 2),
                                       (p.x + vx * (wa + 1) + ux * largo / 2, p.y + vy * (wa + 1) + uy * largo / 2),
                                       (p.x + vx * (-wa - 1) + ux * largo / 2, p.y + vy * (-wa - 1) + uy * largo / 2)])
                if any(huella_paso.intersection(o).area > 1.5 for o in pasos):
                    continue
                pasos.append(huella_paso)
                hechas.append((p.x, p.y))
                k = -wa - 1.0
                while k < wa + 1.0:
                    franja = Polygon([(p.x + vx * k - ux * largo / 2, p.y + vy * k - uy * largo / 2),
                                      (p.x + vx * (k + 0.5) - ux * largo / 2, p.y + vy * (k + 0.5) - uy * largo / 2),
                                      (p.x + vx * (k + 0.5) + ux * largo / 2, p.y + vy * (k + 0.5) + uy * largo / 2),
                                      (p.x + vx * k + ux * largo / 2, p.y + vy * k + uy * largo / 2)])
                    for f in _poligonos(franja.intersection(g["calzada"].buffer(-0.3))):
                        pts = list(f.exterior.coords)[:-1]
                        if f.exterior.is_ccw is False:
                            pts.reverse()
                        c.poligono([(xx, yy, altura_suelo(xx, yy) + SOBRE + 0.02) for xx, yy in pts],
                                   "pintura_acento", "#ecebe6")
                    k += 1.0
                n += 1
    return n


def cebra_en(c, g, x, y, ux, uy, wa, largo=3.0):
    """Paso de cebra puesto a mano: centro (x, y), dirección de la calle (ux, uy), medio ancho de calzada wa."""
    vx, vy = -uy, ux
    k = -wa - 1.0
    while k < wa + 1.0:
        franja = Polygon([(x + vx * k - ux * largo / 2, y + vy * k - uy * largo / 2),
                          (x + vx * (k + 0.5) - ux * largo / 2, y + vy * (k + 0.5) - uy * largo / 2),
                          (x + vx * (k + 0.5) + ux * largo / 2, y + vy * (k + 0.5) + uy * largo / 2),
                          (x + vx * k + ux * largo / 2, y + vy * k + uy * largo / 2)])
        for f in _poligonos(franja.intersection(g["calzada"].buffer(-0.3))):
            pts = list(f.exterior.coords)[:-1]
            if f.exterior.is_ccw is False:
                pts.reverse()
            c.poligono([(xx, yy, altura_suelo(xx, yy) + SOBRE + 0.02) for xx, yy in pts], "pintura_acento", "#ecebe6")
        k += 1.0


def salvar_mobiliario(g, rutas, retiro=0.7, tolerancia=1.0):
    """Modelos SALVADOS de la sección: sus árboles, faroles y postes de vereda que quedaron a más de `tolerancia` m del
    bordillo se corren a `retiro` m de él (usuario: "árboles y postes siempre cerca del borde de la acera"). Se
    reescribe cada GLB con el mismo formato. No toca la vereda de la plaza (la amuebla su dueño)."""
    from shapely.ops import nearest_points
    import trazado as T
    curb = g["vereda"].boundary.intersection(g["calzada"].buffer(0.05))
    lado_plaza = g["plaza"].buffer(T.VEREDA_PLAZA + 0.5)
    total = 0
    for ruta in rutas:
        if not os.path.exists(ruta):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=ruta)
        n = 0
        for o in list(bpy.data.objects):
            if o.type != "MESH" or not any(k in o.name.lower() for k in ("arbol", "farol", "poste")):
                continue
            pts = [o.matrix_world @ v.co for v in o.data.vertices]
            if not pts:
                continue
            zmin = min(p.z for p in pts)
            bajo = [p for p in pts if p.z < zmin + 0.4]
            # solo piezas sueltas: un objeto con una FILA de árboles (p. ej. M040_arboles_plaza) se movía entero hacia
            # el bordillo más cercano a su centro, y en cada corrida otra vez, hasta dejar los árboles en la calzada
            # (revisión por MCP, 2026-11-24). Las filas ya las pone su script junto al bordillo.
            if max(abs(p.x - q.x) + abs(p.y - q.y) for p in bajo[::max(1, len(bajo) // 40)]
                   for q in bajo[::max(1, len(bajo) // 40)]) > 2.0:
                continue
            x, y = sum(p.x for p in bajo) / len(bajo), sum(p.y for p in bajo) / len(bajo)
            p = Point(x, y)
            if not g["vereda"].contains(p) or lado_plaza.contains(p):
                continue
            q = nearest_points(curb, p)[0]
            d = p.distance(q)
            if d <= tolerancia:
                continue
            tx, ty = q.x + (x - q.x) / d * retiro, q.y + (y - q.y) / d * retiro
            o.location.x += tx - x
            o.location.y += ty - y
            o.location.z += altura_suelo(tx, ty) - altura_suelo(x, y)
            n += 1
        if n:
            for o in bpy.context.scene.objects:
                o.select_set(True)
            bpy.ops.export_scene.gltf(filepath=ruta, export_format="GLB", use_selection=True, export_yup=True,
                                      export_apply=True, export_normals=True, export_materials="EXPORT")
        print(f"[seccion] {os.path.basename(ruta)}: {n} piezas de vereda al bordillo")
        total += n
    return total
