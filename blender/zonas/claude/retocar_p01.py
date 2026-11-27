"""Rehace el interior de la Plaza 25 de Mayo (P01) a pedido del usuario: R0151–R0159 ("idéntica a la real").

P01 nació como script de codex. El usuario ordenó que claude la rehaga igual a las fotos, sea de quien sea: este script abre
el P01.glb ya exportado, conserva el trazado (jardines, caminos, paseo, fuentes y monumentos con su posición OSM) y
reemplaza todo lo que se ve de cerca por piezas hechas a mano (piezas_plaza.py): piso de losas gris-beige con cinta de
pizarra, óvalo de pizarra con el monumento a Sucre, quioscos de arenisca, faroles, bancos, rejas forjadas con bordillo,
canteros, árboles viejos, podados y palmeras. Es repetible: si P01.glb se vuelve a exportar, se vuelve a correr.

    ~/apps/blender-5.2.3-linux-x64/blender -b -P blender/zonas/claude/retocar_p01.py
"""
import json
import math
import os
import random
import sys
import time

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import datos, paleta, Constructor  # noqa: E402
from kit.datos import altura_suelo  # noqa: E402
import piezas_plaza as pp  # noqa: E402

RUTA = os.path.join(datos.RAIZ, "web", "public", "models", "ciudad", "codex", "P01.glb")
CONTORNO = [(-238.34, -212.45), (-171.57, -271.01), (-114.38, -204.12), (-184.85, -144.43)]   # igual que P01.py
CENTRO = (-176.72, -208.93)
PIEDRA_BLANCA = "#e4e0d6"
LOSA = "#c2bdb2"                    # losa de piedra gris-beige de la plaza (R0134, R0143, R0144)
R_EXPLANADA = 18.0                  # radio de la explanada de losas alrededor del monumento (R0143: el piso es mucho más amplio)
PREFIJOS_REEMPLAZO = ("P01c_", "P01_arbol_", "P01_banco_", "P01_farol_", "P01_quiosco_", "P01_fuente_",
                      "P01_monumento_", "P01_reja_jardin_", "P01_franja_pizarra")


ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _cargar_asset(nombre):
    """Importa assets/<nombre>.glb y devuelve el objeto de malla (modelo real CC0, ver recursos/LICENCIAS.md)."""
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, nombre + ".glb"))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    malla = [o for o in nuevos if o.type == "MESH"][0]
    me = malla.data
    me.transform(malla.matrix_world)
    malla.parent = None
    malla.matrix_world.identity()
    for o in nuevos:
        if o is not malla:
            bpy.data.objects.remove(o, do_unlink=True)
    return malla


def colocar_assets(lista):
    """Copia cada asset (nombre, x, y, z, rumbo, escala) en su lugar; los copias comparten la malla."""
    base = {}
    for i, (nombre, x, y, z, rumbo, escala) in enumerate(lista):
        if nombre not in base:
            base[nombre] = _cargar_asset(nombre)
            base[nombre].hide_set(False)
        o = bpy.data.objects.new(f"P01c_plaza_{nombre}_{i}", base[nombre].data)
        bpy.context.scene.collection.objects.link(o)
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, rumbo)
        o.scale = (escala,) * 3
    for o in base.values():
        bpy.data.objects.remove(o, do_unlink=True)


def _objeto(c, suavizar=False):
    ob = c.objeto(bpy.context.scene.collection)
    if suavizar:
        for cara in ob.data.polygons:
            if ob.data.materials[cara.material_index].name.split("__")[0] in ("follaje", "follaje_claro"):
                cara.use_smooth = True
    return ob


def _bucle_borde(o):
    """Puntos (x, y) del contorno exterior de una malla plana (aristas con una sola cara), en orden."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bm.edges.ensure_lookup_table()
    sig = {}
    for e in bm.edges:
        if len(e.link_faces) == 1:
            a, b = e.verts
            sig.setdefault(a.index, []).append(b.index)
            sig.setdefault(b.index, []).append(a.index)
    mw = o.matrix_world
    pos = {v.index: mw @ v.co for v in bm.verts}
    mejor, usados = [], set()
    for ini in sig:
        if ini in usados:
            continue
        lazo, prev, cur = [ini], None, ini
        usados.add(ini)
        while True:
            nxt = [n for n in sig[cur] if n != prev and n not in usados]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            usados.add(cur)
            lazo.append(cur)
        if len(lazo) > len(mejor):
            mejor = lazo
    bm.free()
    pts = [(pos[i].x, pos[i].y) for i in mejor]
    sim = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, sim[-1]) > 0.3:
            sim.append(p)
    return sim


def _centro_base(o):
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    zmin = min(p.z for p in pts)
    b = [p for p in pts if p.z < zmin + 0.4] or pts
    return sum(p.x for p in b) / len(b), sum(p.y for p in b) / len(b)


def _en_poligono(x, y, poli):
    return datos._dentro(x, y, poli)


def _dist_sendas(x, y, sendas):
    return min(datos._dist_seg(x, y, a, b)[0] for pts in sendas for a, b in zip(pts, pts[1:]))


# --------------------------------------------------------------------------- piso
def piso_losas():
    """El piso de P01 era 'adoquin' (empedrado redondo). Las fotos muestran losas de piedra gris-beige con junta y franjas de
    pizarra (R0134): rol 'vereda'. Repetible: también recolorea la losa que ya puso una corrida anterior."""
    mat = paleta.material("vereda", LOSA)
    n = 0
    for o in bpy.data.objects:
        if o.type != "MESH" or not (o.name.startswith("P01_pavimento") or o.name.startswith("P01_caminos")):
            continue
        for i, m in enumerate(o.data.materials):
            if m and m.name.startswith(("adoquin", "vereda")):
                o.data.materials[i] = mat
                n += 1
    return n


def _cinta(c, p, q, ancho, color, z_extra=0.215):
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    if L < .5:
        return
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    vx, vy = -uy * ancho / 2, ux * ancho / 2
    pasos = max(1, int(L / 2.5))
    for k in range(pasos):
        a = (p[0] + (q[0] - p[0]) * k / pasos, p[1] + (q[1] - p[1]) * k / pasos)
        b = (p[0] + (q[0] - p[0]) * (k + 1) / pasos, p[1] + (q[1] - p[1]) * (k + 1) / pasos)
        quad = [(a[0] - vx, a[1] - vy), (b[0] - vx, b[1] - vy), (b[0] + vx, b[1] + vy), (a[0] + vx, a[1] + vy)]
        c.poligono([(x, y, altura_suelo(x, y) + z_extra) for x, y in quad], "vereda", color)


def cintas_y_oval(sendas):
    """Cinta de pizarra por el eje de cada camino y del paseo; óvalo de pizarra con borde de piedra en torno al monumento."""
    c = Constructor("P01c_pizarra")
    cx, cy = CENTRO
    for pts in sendas:
        for p, q in zip(pts, pts[1:]):
            # no dentro del óvalo central (12 m)
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            if L < 1:
                continue
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            t0 = max(0, (cx - p[0]) * ux + (cy - p[1]) * uy)
            if math.dist(p[:2], (cx, cy)) < 12.5 and math.dist(q[:2], (cx, cy)) < 12.5:
                continue
            _cinta(c, p, q, 1.0, "#5a626d")
    # paseo perimetral: una cinta por lado, a 1,9 m del borde, dejando libres las esquinas
    for a, b in zip(CONTORNO, CONTORNO[1:] + CONTORNO[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        if ((CENTRO[0] - (a[0] + b[0]) / 2) * nx + (CENTRO[1] - (a[1] + b[1]) / 2) * ny) < 0:
            nx, ny = -nx, -ny
        p = (a[0] + ux * 9 + nx * 1.9, a[1] + uy * 9 + ny * 1.9)
        q = (b[0] - ux * 9 + nx * 1.9, b[1] - uy * 9 + ny * 1.9)
        _cinta(c, p, q, .95, "#5a626d")
    # explanada del monumento (R0143/R0144): losa clara con un anillo de pizarra y otro en el borde de la explanada
    pp.disco_suelo(c, cx, cy, .22, 12.3, "vereda", LOSA)
    pp.anillo_plano(c, cx, cy, .225, 9.6, 10.6, "vereda", "#5a626d", n=56)
    pp.anillo_plano(c, cx, cy, .225, R_EXPLANADA - 1.6, R_EXPLANADA - .7, "vereda", "#5a626d", n=72)
    _objeto(c)


# --------------------------------------------------------------------------- jardines
def _inset(loop, d):
    cx = sum(p[0] for p in loop) / len(loop)
    cy = sum(p[1] for p in loop) / len(loop)
    out = []
    for p in loop:
        v = (cx - p[0], cy - p[1])
        L = math.hypot(*v) or 1
        out.append((p[0] + v[0] / L * d, p[1] + v[1] / L * d))
    return out


def reja_bordillo_seto(nombre, loop):
    """Bordillo de piedra blanca, reja forjada con volutas y seto bajo por dentro (bordes de jardín, R0153/R0154/R0159)."""
    c = Constructor(nombre)
    for a, b in zip(loop, loop[1:] + loop[:1]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < .25:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        z_a, z_b = altura_suelo(*a) + .18, altura_suelo(*b) + .18
        n_t = max(1, math.ceil(L / 4.0))
        for k in range(n_t):
            t0, t1 = k / n_t, (k + 1) / n_t
            pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            za, zb = z_a + (z_b - z_a) * t0, z_a + (z_b - z_a) * t1
            zm = (za + zb) / 2
            pp.caja_local(c, (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, zm - .04, zm + .14, ux, uy,
                          math.dist(pa, pb) + .02, .14, "piedra", PIEDRA_BLANCA)             # bordillo blanco
            pp.reja_forjada(c, pa, pb, za + .1, zb + .1)
    _objeto(c)


def setos_y_canteros(nombre, loop, azar, fuera, cesped, libres):
    """Seto bajo por dentro de la reja, arbustos y un cantero de flores en el centro del jardín."""
    c = Constructor(nombre)
    # manchas planas (cobertura y canteros de flores) en un objeto aparte: no son volumen y, mezcladas con los setos,
    # confunden la prueba de "punto dentro" del control de calidad
    cs = Constructor(nombre.replace("P01c_", "P01c_plaza_") + "_suelo")
    ins = _inset(loop, .55)

    def libre(x, y, r=0.0):                     # ni sobre una fuente ni bajo la glorieta
        return all(math.dist((x, y), q) > rr + r for q, rr in libres)
    # seto: paralelo a cada lado de la reja, a 0,6 m hacia dentro (normal del lado, no hacia el centro: en los jardines
    # alargados el corrimiento radial lo sacaba del césped) y sin tocar fuentes, quioscos ni la glorieta
    puestos = []
    # el seto va en cuatro objetos, uno por orientación del lado: un anillo de seto en un solo objeto "encierra" el césped
    setos = [Constructor(f"{nombre}_seto{k}") for k in range(4)]
    for a, b in zip(loop, loop[1:] + loop[:1]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1.6:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -uy, ux
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if not _en_poligono(mx + nx * .6, my + ny * .6, loop):
            nx, ny = -nx, -ny
        n = max(1, int((L - 1.2) / 3.0))
        paso = (L - 1.2) / n
        for k in range(n):
            d = .6 + (k + .5) * paso
            x, y = a[0] + ux * d + nx * .6, a[1] + uy * d + ny * .6
            if not _en_poligono(x, y, loop) or not libre(x, y, paso / 2 + .4):
                continue
            ext = ((x - ux * paso / 2, y - uy * paso / 2), (x + ux * paso / 2, y + uy * paso / 2))
            muestras = [(ext[0][0] + (ext[1][0] - ext[0][0]) * t, ext[0][1] + (ext[1][1] - ext[0][1]) * t) for t in (0, .25, .5, .75, 1)]
            if any(min(datos._dist_seg(*e, *otro)[0] for e in muestras) < .5 for otro in puestos):
                continue                                         # esquina cóncava: no cruzar el tramo del otro lado
            puestos.append(ext)
            z = min(cesped(x - ux * paso / 2, y - uy * paso / 2), cesped(x + ux * paso / 2, y + uy * paso / 2))
            sector = int(((math.degrees(math.atan2(ny, nx)) + 45) % 360) // 90)
            pp.caja_local(setos[sector], x, y, z - .02, z + .26 + .06 * azar.random(), ux, uy, paso + .02, .4, "follaje", "#4a7a30")
    # arbustos sueltos dentro del jardín
    gx = sum(p[0] for p in loop) / len(loop)
    gy = sum(p[1] for p in loop) / len(loop)
    for _ in range(7):
        p = azar.choice(ins)
        t = azar.uniform(.25, .6)
        x, y = p[0] + (gx - p[0]) * t, p[1] + (gy - p[1]) * t
        if not libre(x, y, 1.0):
            continue
        r_ = azar.uniform(.45, .85)
        pp.arbusto(c, x, y, max(cesped(x + i_ * r_, y + j_ * r_) for i_ in (-1, 0, 1) for j_ in (-1, 0, 1)) + r_ * .2, r_, "follaje",
                   azar.choice(("#3c6a2b", "#4a7a30", "#2f5a2a")))
    # cobertura baja: manchas de verdes y flores sobre el césped (barato: polígonos planos), como la plantación de las fotos
    for _ in range(30):
        p = azar.choice(ins)
        t = azar.uniform(.05, .85)
        x, y = p[0] + (gx - p[0]) * t, p[1] + (gy - p[1]) * t
        if not _en_poligono(x, y, loop) or not libre(x, y, 1.3):
            continue
        col = azar.choice(("#3f6e2a", "#2f5a2a", "#5c8a35", "#7a9e3a", "#44762c", "#e8c44a", "#d9677f", "#f0a030"))
        rol = "flor" if col in ("#e8c44a", "#d9677f", "#f0a030") else "cesped"
        a_ = azar.uniform(0, math.tau)
        r = azar.uniform(.5, 1.3)
        pp.elipse_plana(cs, x, y, .02, r, r * azar.uniform(.55, .9), rol, col, math.cos(a_), math.sin(a_), n=10, altura=cesped)
    # cantero de flores: elipse de colores, orientado hacia el centro de la plaza, con flores reales (Quaternius, CC0)
    dx, dy = CENTRO[0] - gx, CENTRO[1] - gy
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    camas = [(gx + ux * 3.0, gy + uy * 3.0, 3.4, 1.7, ["#f1c232", "#e8742c", "#d9402c"], ("flores_naranja", "flores_amarilla")),
             (gx - ux * 4.0, gy - uy * 4.0, 2.2, 1.3, ["#f4d44b", "#f0a030"], ("flores_amarilla", "flores_roja"))]
    for bx, by, rx, ry, cols, tipos in camas:
        if not _en_poligono(bx, by, loop) or not libre(bx, by, rx):
            continue
        pp.parche_flores(cs, bx, by, rx, ry, -uy, ux, cols, altura=cesped)
        k = 0
        for i in range(-int(rx / 1.8), int(rx / 1.8) + 1):
            for j in range(-int(ry / 1.8), int(ry / 1.8) + 1):
                u_, v_ = i * 1.8 + azar.uniform(-.25, .25), j * 1.8 + azar.uniform(-.2, .2)
                if (u_ / rx) ** 2 + (v_ / ry) ** 2 > .85:
                    continue
                x, y = bx - uy * u_ + ux * v_ * 0 + (-uy) * 0, by + ux * u_
                x, y = bx + (-uy) * u_ + ux * v_, by + ux * u_ + uy * v_
                fuera.append((tipos[k % len(tipos)], x, y, cesped(x, y) + .02, azar.uniform(0, math.tau), azar.uniform(.26, .36)))
                k += 1
    # arbustos con flores y plantas grandes junto a la reja, hojas de helecho al pie
    for tipo, cuantos, esc in (("arbusto_flor_rosa", 2, .6), ("arbusto_flor_amarilla", 2, .55), ("planta_grande", 4, .5), ("helecho", 4, .45), ("flores_naranja", 3, .3), ("flores_amarilla", 3, .3)):
        for _ in range(cuantos):
            p = azar.choice(ins)
            t = azar.uniform(.08, .5)
            x, y = p[0] + (gx - p[0]) * t, p[1] + (gy - p[1]) * t
            if _en_poligono(x, y, loop):
                fuera.append((tipo, x, y, cesped(x, y), azar.uniform(0, math.tau), esc * azar.uniform(.9, 1.15)))
    _objeto(c)
    _objeto(cs)
    for cs_ in setos:
        if cs_.bm.faces:
            _objeto(cs_)


def cesped(o):
    """Altura del césped de un jardín (su malla, que no siempre sigue al terreno) para apoyar setos y plantas encima."""
    from mathutils.bvhtree import BVHTree
    deps = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    bm.from_object(o, deps)
    bm.transform(o.matrix_world)
    arbol = BVHTree.FromBMesh(bm)
    bm.free()

    def z(x, y):
        hit = arbol.ray_cast(Vector((x, y, 200.0)), Vector((0, 0, -1)), 400)
        base = altura_suelo(x, y) + .18
        return max(base, hit[0].z) if hit[0] is not None else base
    return z


def explanada(o):
    """R0143: los jardines llegan hasta R_EXPLANADA del monumento, no más cerca; el borde interior queda en arco.
    Los vértices más cercanos se empujan al arco (las caras que quedan dentro se aplastan contra él)."""
    mw = o.matrix_world
    inv = mw.inverted()
    cx, cy = CENTRO
    n = 0
    for v in o.data.vertices:
        p = mw @ v.co
        d = math.hypot(p.x - cx, p.y - cy)
        if d >= R_EXPLANADA - 1e-3 or d < 1e-6:
            continue
        sobre = p.z - altura_suelo(p.x, p.y)
        nx, ny = cx + (p.x - cx) / d * R_EXPLANADA, cy + (p.y - cy) / d * R_EXPLANADA
        v.co = inv @ Vector((nx, ny, altura_suelo(nx, ny) + sobre))
        n += 1
    if n:
        print("[retocar_p01] explanada:", o.name, n, "vértices llevados al arco")


def colocar_dentro(x, y, huella, margen=1.2):
    """Corre un punto hacia el centro de la plaza hasta que quede `margen` m dentro de la huella."""
    for k in range(80):
        if datos._dentro(x, y, huella) and all(
                datos._dentro(x + dx, y + dy, huella) for dx, dy in ((margen, 0), (-margen, 0), (0, margen), (0, -margen))):
            return x, y
        x, y = x + (CENTRO[0] - x) * .02, y + (CENTRO[1] - y) * .02
    return x, y


# Vendedores de las fotos (R0133: carrito de naranjas en el paseo de la esquina norte; R0135: puesto de sombrilla roja
# junto a la calle; otra sombrilla a la derecha de la toma R0133). Posición aproximada de la toma del usuario, rumbo del frente.
# Van al costado del paseo, nunca en el eje del camino.
VENDEDORES = [("carrito", -188.6, -152.5, 0.0), ("sombrilla", -180.2, -149.8, 0.0), ("sombrilla", -190.2, -158.5, 90.0)]
# Glorieta de R0142: rumbo 224° y ~27 m desde la toma del usuario (-181.3, -179.2), a la izquierda de la fuente oeste.
GLORIETA = (-200.1, -198.6)


# --------------------------------------------------------------------------- main
# Nombres: lo que es mobiliario o vegetación suelta de la plaza (plantas, rejas, glorieta) lleva "_plaza_" en el nombre:
# kit/calidad.py lo trata como mobiliario y no como edificio (una planta que asoma entre la reja no es un siamés).
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=RUTA)
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    arboles_borde, arboles_altos, fuentes, monumentos, quioscos = [], [], [], [], []
    for o in objs:
        n = o.name.replace("P01c_", "P01_")          # el script es repetible: lee también lo que él mismo escribió
        if n.endswith("_cal"):
            continue
        if n.startswith(("P01_arbol_borde_", "P01_arbol_podado_")):
            arboles_borde.append(_centro_base(o))
        elif n.startswith(("P01_arbol_alto_", "P01_arbol_viejo_")):
            arboles_altos.append(_centro_base(o))
        elif n.startswith("P01_fuente_"):
            fuentes.append(_centro_base(o))
        elif n.startswith("P01_monumento_") or n.startswith("P01_pedestal_"):
            monumentos.append((n, _centro_base(o)))
        elif n.startswith("P01_quiosco_"):
            quioscos.append(_centro_base(o))
    mastiles = [_centro_base(o) for o in objs if o.name.startswith("P01_mastil_")]
    jardines = [o for o in objs if o.name.startswith("P01_jardin_")]
    for o in jardines:
        explanada(o)
    bucles = [_bucle_borde(o) for o in jardines]
    quitadas = 0
    for o in list(bpy.data.objects):
        if o.name.endswith("_cal") or o.name.startswith(PREFIJOS_REEMPLAZO):
            bpy.data.objects.remove(o, do_unlink=True)
            quitadas += 1
    ruta_calles = os.path.join(datos.RAIZ, "web", "public", "mapa", "calles.json")
    huella = [tuple(p) for e in datos.reparto()["espacios"] if e["id"] == "P01" for p in e["poligono"]]
    sendas = [[tuple(p[:2]) for p in cc["puntos"]] for cc in json.load(open(ruta_calles))
              if cc["tipo"] == "footway" and cc["puntos"] and all(datos._dentro(p[0], p[1], huella) for p in cc["puntos"])]
    azar = random.Random(25051809)
    # una fuente sobre un camino o fuera de los jardines es incoherente: va al centro de un jardín que aún no tenga
    cent = [(sum(p[0] for p in lp) / len(lp), sum(p[1] for p in lp) / len(lp)) for lp in bucles]
    ocupados = {k for k, lp in enumerate(bucles) for f in fuentes if _en_poligono(f[0], f[1], lp)}
    for i, (x, y) in enumerate(fuentes):
        if any(_en_poligono(x, y, lp) for lp in bucles) and _dist_sendas(x, y, sendas) > 3.5:
            continue
        libres = [k for k in range(len(bucles)) if k not in ocupados]
        k = min(libres, key=lambda k: math.dist(cent[k], (x, y)))
        ocupados.add(k)
        print("[retocar_p01] fuente", i, "movida de", (round(x, 1), round(y, 1)), "al jardín", k, [round(v, 1) for v in cent[k]])
        fuentes[i] = cent[k]
    # ningún árbol encima de una fuente, un quiosco o el monumento
    # palmeras: las de la foto R0151, en los jardines alrededor del monumento (se ubican antes que los árboles: copa libre)
    palmas = []
    for grados, r in ((20, 25), (48, 21), (78, 27), (195, 23), (232, 20), (262, 26), (305, 23), (335, 28)):
        x, y = CENTRO[0] + r * math.cos(math.radians(grados)), CENTRO[1] + r * math.sin(math.radians(grados))
        lejos = all(math.dist((x, y), q) > 6.0 for q in fuentes + quioscos + [GLORIETA])   # copa de la palmera canaria: ~5 m
        if any(_en_poligono(x, y, lp) for lp in bucles) and _dist_sendas(x, y, sendas) >= 3.5 and lejos:
            palmas.append((x, y))
    ocup = ([(f, 4.5) for f in fuentes] + [(q, 4.0) for q in quioscos] + [(CENTRO, R_EXPLANADA + 1.0), (GLORIETA, 5.5)]
            + [(p, 3.5) for _, p in monumentos] + [(p, 3.5) for p in palmas])
    arboles_altos[:] = [t for t in arboles_altos if all(math.dist(t, c) > r for c, r in ocup)]
    arboles_borde[:] = [t for t in arboles_borde if all(math.dist(t, c) > r for c, r in ocup)]
    if os.environ.get("DIAG"):
        for nom, lst in (("fuente", fuentes), ("quiosco", quioscos), ("alto", arboles_altos), ("borde", arboles_borde)):
            for x, y in lst:
                print("DIAG", nom, round(x, 1), round(y, 1), "senda", round(_dist_sendas(x, y, sendas), 1),
                      "jardin", any(_en_poligono(x, y, lp) for lp in bucles), "centro", round(math.dist((x, y), CENTRO), 1))

    npiso = piso_losas()
    cintas_y_oval(sendas)

    # monumento central y bustos menores
    ang = math.atan2(CONTORNO[1][1] - CONTORNO[0][1], CONTORNO[1][0] - CONTORNO[0][0])
    ux, uy = math.cos(ang), math.sin(ang)
    fuera = []
    for nombre, (x, y) in monumentos:
        c = Constructor("P01c_" + nombre.replace("P01_", ""))
        z = altura_suelo(x, y) + .2
        if "Sucre" in nombre:
            pp.monumento_sucre(c, x, y, z, ux, uy, fuera)
        else:
            pp.busto_pedestal(c, x, y, z, ux, uy, fuera)
        _objeto(c)
    colocar_assets(fuera)
    for i, (x, y) in enumerate(fuentes):
        c = Constructor(f"P01c_fuente_{i}")
        pp.fuente(c, x, y, altura_suelo(x, y) + .2)
        _objeto(c)
    for i, (x, y) in enumerate(quioscos):
        c = Constructor(f"P01c_quiosco_{i}")
        # frente hacia el paseo más cercano
        lado = min(range(4), key=lambda k: datos._dist_seg(x, y, CONTORNO[k], CONTORNO[(k + 1) % 4])[0])
        a, b = CONTORNO[lado], CONTORNO[(lado + 1) % 4]
        pp.quiosco(c, x, y, altura_suelo(x, y) + .2, math.atan2(b[1] - a[1], b[0] - a[0]))
        _objeto(c)

    # jardines: reja con bordillo, setos, arbustos y canteros
    fuera_jardin = []
    for j, loop in enumerate(bucles):
        reja_bordillo_seto(f"P01c_plaza_reja_jardin_{j}", loop)
        setos_y_canteros(f"P01c_cantero_{j}", loop, azar, fuera_jardin, cesped(jardines[j]),
                         [(f, 3.8) for f in fuentes] + [(q, 2.8) for q in quioscos] + [(GLORIETA, 4.8)]
                         + [(m_, .6) for m_ in mastiles])

    # plantas sueltas: lejos de la reja y el seto del borde, de fuentes, glorieta, bustos y palmeras (sin cruzarse)
    evitar = [(f, 4.4) for f in fuentes] + [(GLORIETA, 5.6)] + [(p, 3.0) for _, p in monumentos] + [(p, 1.2) for p in palmas]

    def borde(x, y):
        return min(datos._dist_seg(x, y, a, b)[0] for lp in bucles for a, b in zip(lp, lp[1:] + lp[:1]))
    antes = len(fuera_jardin)
    fuera_jardin[:] = [a for a in fuera_jardin if borde(a[1], a[2]) >= 1.4 and all(math.dist((a[1], a[2]), q) > r for q, r in evitar)]
    print("[retocar_p01] plantas sueltas:", len(fuera_jardin), "de", antes)
    colocar_assets(fuera_jardin)
    # árboles: viejos (interior) y podados (fila del perímetro), con pie encalado
    for i, (x, y) in enumerate(arboles_altos):
        c = Constructor(f"P01c_arbol_viejo_{i}")
        pp.arbol_viejo(c, x, y, altura_suelo(x, y) + .18, azar, escala=azar.uniform(.9, 1.15))
        _objeto(c, True)
    for i, (x, y) in enumerate(arboles_borde):
        c = Constructor(f"P01c_arbol_podado_{i}")
        pp.arbol_podado(c, x, y, altura_suelo(x, y) + .18, azar, radio=azar.uniform(2.0, 2.5))
        _objeto(c, True)
    # palmeras: las de la foto R0151, en los jardines alrededor del monumento
    n_palma = 0
    for x, y in palmas:
        c = Constructor(f"P01c_arbol_palmera_{n_palma}")
        pp.palmera(c, x, y, altura_suelo(x, y) + .18, azar, alto=azar.uniform(10.5, 13.5))
        _objeto(c, True)
        n_palma += 1

    # mobiliario del paseo: bancos, faroles y papeleras, como en P01.py pero con las piezas de las fotos
    cb = Constructor("P01c_bancos")
    cf = Constructor("P01c_faroles")
    cp = Constructor("P01c_papeleras")
    for lado, (a, b) in enumerate(zip(CONTORNO, CONTORNO[1:] + CONTORNO[:1])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        ux_, uy_ = dx / L, dy / L
        nx, ny = -uy_, ux_
        if ((CENTRO[0] - (a[0] + b[0]) / 2) * nx + (CENTRO[1] - (a[1] + b[1]) / 2) * ny) < 0:
            nx, ny = -nx, -ny
        fx, fy = (ux_, uy_) if (nx, ny) == (-uy_, ux_) else (-ux_, -uy_)          # su izquierda mira al centro
        for k in range(1, 9):
            t = k / 9
            if k % 2 == 0:
                x, y = a[0] + dx * t + nx * 1.6, a[1] + dy * t + ny * 1.6
                pp.banco(cb, x, y, altura_suelo(x, y) + .2, fx, fy)
        for k in (1, 3, 5, 7):
            t = k / 8
            x, y = a[0] + dx * t + nx * .8, a[1] + dy * t + ny * .8
            pp.farol(cf, x, y, altura_suelo(x, y) + .2, fx, fy, doble=(k in (3, 7)))
        for k in (2, 6):
            t = k / 8
            x, y = a[0] + dx * t + nx * 2.6, a[1] + dy * t + ny * 2.6
            pp.papelera(cp, x, y, altura_suelo(x, y) + .2)
    # junto a la reja de los jardines: faroles y bancos que miran al camino, macetas en la entrada
    cm = Constructor("P01c_macetas")
    for loop in bucles:
        gx = sum(p[0] for p in loop) / len(loop)
        gy = sum(p[1] for p in loop) / len(loop)
        for a, b in zip(loop, loop[1:] + loop[:1]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 14:
                continue
            ux_, uy_ = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = uy_, -ux_
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            if (mx - gx) * nx + (my - gy) * ny < 0:
                nx, ny = -nx, -ny                                             # hacia afuera del jardín (el camino)
            for s in (.3, .72):
                x, y = a[0] + (b[0] - a[0]) * s + nx * 1.0, a[1] + (b[1] - a[1]) * s + ny * 1.0
                if math.dist((x, y), CENTRO) < R_EXPLANADA or not _en_poligono(x, y, huella):
                    continue
                pp.farol(cf, x, y, altura_suelo(x, y) + .2, -nx, -ny, doble=False, alto=4.2)
        # macetas con hojas grandes a la entrada: cerca de los dos vértices más lejanos al centro de la plaza
        lejanos = sorted(loop, key=lambda p: -math.dist(p, CENTRO))[:2]
        for p in lejanos:
            v = (p[0] - gx, p[1] - gy)
            Lv = math.hypot(*v) or 1
            x, y = p[0] + v[0] / Lv * .9, p[1] + v[1] / Lv * .9
            if _en_poligono(x, y, huella):
                pp.maceta_pedestal(cm, x, y, altura_suelo(x, y) + .2, ux, uy)
    for c in (cb, cf, cp, cm):
        _objeto(c, c is cm)
    cg = Constructor("P01c_plaza_glorieta")
    pp.glorieta(cg, *GLORIETA, altura_suelo(*GLORIETA) + .2)
    _objeto(cg)
    print("[retocar_p01] glorieta en jardín:", any(_en_poligono(*GLORIETA, lp) for lp in bucles),
          "a", round(_dist_sendas(*GLORIETA, sendas), 1), "m del eje de un camino")
    _inset_todos = [_inset(lp, -1.2) for lp in bucles]          # jardín con su reja y un margen
    cv = Constructor("P01c_vendedores")
    for tipo, x, y, rumbo in VENDEDORES:
        x, y = colocar_dentro(x, y, huella)

        def libre(px, py):
            return (not any(_en_poligono(px, py, lp) for lp in _inset_todos) and _dist_sendas(px, py, sendas) >= 2.0
                    and datos._dentro(px, py, huella))
        if not libre(x, y):                       # el punto más cercano sobre piso libre, al costado del camino
            cand = [(x + i * .5, y + j * .5) for i in range(-12, 13) for j in range(-12, 13)]
            cand = [p for p in cand if libre(*p)]
            if not cand:
                print("[retocar_p01] AVISO: sin lugar para el vendedor", tipo, round(x, 1), round(y, 1))
                continue
            x, y = min(cand, key=lambda p: math.dist(p, (x, y)))
        ux_, uy_ = math.sin(math.radians(rumbo)), math.cos(math.radians(rumbo))
        (pp.carrito_fruta if tipo == "carrito" else pp.puesto_sombrilla)(cv, x, y, altura_suelo(x, y) + .2, ux_, uy_)
    _objeto(cv)

    print(f"[retocar_p01] {quitadas} objetos reemplazados, piso de losas en {npiso} materiales, {n_palma} palmeras, "
          f"{len(arboles_altos)} árboles viejos, {len(arboles_borde)} podados, {len(fuentes)} fuentes, {len(quioscos)} quioscos")
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=RUTA, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_normals=True, export_materials="EXPORT")
    man_ruta = os.path.join(os.path.dirname(RUTA), "manifiesto.json")
    man = json.load(open(man_ruta))
    deps = bpy.context.evaluated_depsgraph_get()
    tris = sum(len(o.evaluated_get(deps).data.loop_triangles) for o in bpy.data.objects if o.type == "MESH")
    man["P01"]["triangulos"] = tris
    man["P01"]["objetos"] = len([o for o in bpy.data.objects if o.type == "MESH"])
    man["P01"]["actualizado"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(man_ruta, "w") as fh:
        json.dump(man, fh, indent=1)
    print(f"[retocar_p01] P01.glb reescrito ({tris} triángulos)")


main()
