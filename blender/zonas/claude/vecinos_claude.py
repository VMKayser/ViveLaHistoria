"""Recorte de edificios contra el muro real del vecino (control de calidad: SIAMESES).

`kit/medianeras.py` recorta cada edificio con los planos de SU huella, pero cuando la huella de una casa se mete en la
del vecino (datos del lienzo) un tejado o una cornisa de la casa baja entra 0,2–2,4 m en el muro de la casa alta. Aquí se
mira la geometría ya construida: por cada par de edificios de la manzana, los vértices de A metidos más de 0,2 m dentro de
B se cortan con el plano del muro de B más cercano (todo lo de A que queda del lado de adentro de ese muro se quita).

Se corta solo si A está claramente del lado de afuera de ese muro (casa vecina, no un edificio envuelto por otro); si no, se
deja y se informa por consola para revisarlo a mano.

Uso (antes de exportar):  from vecinos_claude import preparar;  preparar(col, mid)
"""

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

from mathutils import Vector

from kit import medianeras
from kit.datos import altura_suelo

# Criterios de kit/calidad.py (no se importa: ese módulo ejecuta main() al importarse y reinicia la escena de Blender).
MOBILIARIO = ("cables", "postes", "semaforo", "vereda", "puesto", "letrero", "pino", "arbol", "carpa", "plaza",
              "BASE_piso", "BASE_calzada", "BASE_marcas", "explanada", "atrio", "detalles", "mirador")
PARTES = ("techos_patio", "_detalles", "_mirador")


def es_mobiliario(o):
    n = o.name.lower()
    return any(k.lower() in n for k in MOBILIARIO)


def bvh_de(objs):
    verts, polys = [], []
    for o in objs:
        mw = o.matrix_world
        b = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[b + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys) if polys else None


def dentro_malla(bvh, p, caja):
    """Punto encerrado por la malla en las cuatro direcciones horizontales (mismo criterio que el control de calidad)."""
    if not (caja[0] < p.x < caja[3] and caja[1] < p.y < caja[4] and caja[2] < p.z < caja[5]):
        return False
    for d in ((1, 0.001, 0), (-1, -0.001, 0), (0.001, 1, 0), (-0.001, -1, 0)):
        if bvh.ray_cast(p, Vector(d).normalized(), 200.0)[0] is None:
            return False
    return True

PROFUNDIDAD = 0.2        # igual que el control de calidad
MAX_BORRADO = 0.85       # si el corte borraría más de esta parte de A, A está casi enterrado: no se toca y se informa


def _edificios(col):
    return [o for o in col.all_objects if o.type == "MESH" and not es_mobiliario(o) and not o.name.startswith("BASE_")
            and not any(k in o.name for k in PARTES)]


def _caja(vs):
    return (min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs),
            max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs))


def _bvh_muros(o):
    """BVH solo con las caras verticales (muros) de o, en coordenadas de mundo."""
    mw = o.matrix_world
    verts = [mw @ v.co for v in o.data.vertices]
    polys = [list(p.vertices) for p in o.data.polygons if abs((mw.to_3x3() @ p.normal).z) < 0.3]
    return BVHTree.FromPolygons(verts, polys) if polys else None


def _cortar(a, planos, bb, cb):
    """Parte a por cada plano y borra solo las caras que quedan del lado de adentro Y dentro del volumen del vecino
    (bb/cb: su BVH y su caja). Devuelve la fracción de caras borradas (si es enorme no se aplica)."""
    mw, mwi = a.matrix_world, a.matrix_world.inverted()
    bm = bmesh.new()
    bm.from_mesh(a.data)
    n0 = len(bm.faces)
    for co, no in planos:
        co_l = mwi @ co
        no_l = (mwi.to_3x3() @ no).normalized()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=0.0005, plane_co=co_l,
                               plane_no=no_l, clear_inner=False, clear_outer=False)
    bm.faces.ensure_lookup_table()
    fuera = []
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        if (not planos or any((c - co).dot(no) < -0.01 for co, no in planos)) and dentro_malla(bb, c, cb):
            fuera.append(f)
    fraccion = len(fuera) / max(n0, 1)
    if fraccion > MAX_BORRADO or not fuera:
        bm.free()
        return fraccion, 0
    bmesh.ops.delete(bm, geom=fuera, context="FACES")
    sueltos = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=sueltos, context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context="VERTS")
    bm.to_mesh(a.data)
    bm.free()
    a.data.update()
    return fraccion, len(fuera)


def _quitar_hondas(a, bb, cb):
    """Último recurso: borra las caras de a que todavía tienen un vértice metido más de PROFUNDIDAD en el vecino
    (son esquinas de tejado o cornisa que asoman por dentro del muro del otro). Devuelve cuántas caras borró."""
    mw = a.matrix_world
    bm = bmesh.new()
    bm.from_mesh(a.data)
    malas = set()
    for v in bm.verts:
        p = mw @ v.co
        if p.z < altura_suelo(p.x, p.y) + 0.1 or not dentro_malla(bb, p, cb):
            continue
        q = bb.find_nearest(p)
        if q[0] is not None and q[3] > PROFUNDIDAD:
            malas.update(v.link_faces)
    if not malas or len(malas) > 0.5 * len(bm.faces):
        bm.free()
        return 0
    n = len(malas)
    bmesh.ops.delete(bm, geom=list(malas), context="FACES")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context="VERTS")
    bm.to_mesh(a.data)
    bm.free()
    a.data.update()
    return n


def recortar_vecinos(col, contexto=()):
    """Devuelve la cantidad de edificios recortados. contexto: objetos de manzanas vecinas (solo se usan como 'B')."""
    datos = []
    for o in _edificios(col):
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        if vs:
            datos.append([o, vs, bvh_de([o]), _caja(vs)])
    n_propios = len(datos)
    for o in contexto:
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        if vs:
            datos.append([o, vs, bvh_de([o]), _caja(vs)])
    cortados = 0
    for i in range(n_propios):
        for j in range(len(datos)):
            a, va, _, ca = datos[i]
            b, _, bb, cb = datos[j]
            if a is None or b is None:
                continue
            if i == j or ca[3] < cb[0] or cb[3] < ca[0] or ca[4] < cb[1] or cb[4] < ca[1]:
                continue
            muros = _bvh_muros(b)
            if muros is None:
                continue
            planos, hondos = {}, 0
            for v in va:
                if v.z < altura_suelo(v.x, v.y) + 0.1 or not dentro_malla(bb, v, cb):
                    continue
                q = bb.find_nearest(v)
                if q[0] is None or q[3] <= PROFUNDIDAD:
                    continue
                hondos += 1
                loc, nor, _, _ = muros.find_nearest(v)
                if loc is None:
                    continue
                if (v - loc).dot(nor) >= 0:                      # normal hacia adentro: se invierte para que v quede detrás
                    nor = -nor
                planos[(round(nor.x, 1), round(nor.y, 1), round(loc.dot(nor), 1))] = (loc, nor)
            if not hondos:
                continue
            fraccion, n = _cortar(a, list(planos.values()), bb, cb)
            if fraccion <= MAX_BORRADO:
                extra = _quitar_hondas(a, bb, cb)
                if extra:
                    print(f"[vecinos] {a.name}: {extra} caras con esquinas metidas en {b.name} borradas")
                n += extra
            if n:
                cortados += 1
                print(f"[vecinos] {a.name}: {n} caras metidas en {b.name} borradas ({len(planos)} planos)")
                vs = [a.matrix_world @ v.co for v in a.data.vertices]
                if vs:
                    datos[i] = [a, vs, bvh_de([a]), _caja(vs)]
            elif fraccion > MAX_BORRADO:
                # casi todo el objeto queda dentro del vecino: no se ve; se quita entero para no dejar siameses
                print(f"[vecinos] {a.name} queda {fraccion:.0%} dentro de {b.name}: se quita el objeto entero (oculto)")
                bpy.data.objects.remove(a, do_unlink=True)
                datos[i] = [None, [], None, (1e9, 1e9, 1e9, -1e9, -1e9, -1e9)]
    return cortados


def _importar_vecinas(ids):
    """Importa (solo lectura, para recortar contra ellas) las manzanas vecinas ya exportadas."""
    import os
    from kit.datos import RAIZ
    antes = set(bpy.data.objects)
    for vid in ids:
        ruta = os.path.join(RAIZ, "web", "public", "models", "ciudad", "claude", f"{vid}.glb")
        if os.path.exists(ruta):
            bpy.ops.import_scene.gltf(filepath=ruta)
    nuevos = [o for o in set(bpy.data.objects) - antes]
    return [o for o in nuevos if o.type == "MESH" and not es_mobiliario(o) and not any(k in o.name for k in PARTES)], nuevos


def preparar(col, mid, vecinas=()):
    """Medianeras del kit + recorte contra el muro del vecino. Llamar justo antes de exportar().
    vecinas: IDs de manzanas (claude) ya exportadas con las que esta se toca (se importan solo como referencia)."""
    col = bpy.data.collections[mid]   # la referencia que llega puede estar vieja (detallar() rehace colecciones)
    medianeras.limpiar(col, mid)
    contexto, temporales = _importar_vecinas(vecinas) if vecinas else ([], [])
    try:
        return recortar_vecinos(col, contexto)
    finally:
        for o in temporales:
            bpy.data.objects.remove(o, do_unlink=True)


def quitar_dentro_de_huella(nombre, huella):
    """Borra de la malla `nombre` las caras cuyo centro cae dentro de la huella (polígono (x, y)) de otro edificio.
    Para los casos que el recorte automático no detecta (p. ej. un volumen hecho a mano contra otro)."""
    o = bpy.data.objects[nombre]
    mw = o.matrix_world
    bm = bmesh.new()
    bm.from_mesh(o.data)

    def dentro(x, y):
        c = False
        for (x1, y1), (x2, y2) in zip(huella, huella[1:] + huella[:1]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c

    fuera = [f for f in bm.faces if dentro(*(mw @ f.calc_center_median()).xy)]
    bmesh.ops.delete(bm, geom=fuera, context="FACES")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    print(f"[vecinos] {nombre}: {len(fuera)} caras dentro de la huella vecina borradas")
