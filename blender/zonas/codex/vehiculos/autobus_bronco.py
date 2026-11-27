"""Minibús BRONCO construido desde la lámina del usuario (2026-11-24).

Blender: X hacia el frente, Y a la izquierda, Z arriba. Origen a ras del suelo.
La vista lateral de acceso determina los seis vanos, los arcos de rueda y la puerta.
Frente y trasera determinan pilotos, bandas, lunetas y parachoques. El lateral
izquierdo y la distribución interior se interpretan, como documenta bronco.json.
No carga/manipula ciudad, reparto, kit ni manifiestos de manzanas.

blender -b -t 2 -P blender/zonas/codex/vehiculos/autobus_bronco.py -- [--sin-render]
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

DIRECTORIO = Path(__file__).resolve().parent
RAIZ = DIRECTORIO.parents[3]
sys.path.insert(0, str(DIRECTORIO))
sys.path.insert(0, str(RAIZ / "blender" / "kit"))
from paleta import material  # noqa: E402
from acabados_bronco import contorno_redondeado, curvar_cabina, techo_curvo, ruedas_detalladas  # noqa: E402
from rig_bronco import preparar_movimiento  # noqa: E402

D = json.loads((DIRECTORIO / "bronco.json").read_text())
SALIDA = RAIZ / "web/public/models/ciudad/codex/vehiculos"
REVISION = RAIZ / "revisiones/codex/autobus_bronco"
SALIDA.mkdir(parents=True, exist_ok=True)
REVISION.mkdir(parents=True, exist_ok=True)
M = {}
GRUPOS = {}


def vacio(nombre, posicion=(0, 0, 0), padre=None):
    o = bpy.data.objects.new(nombre, None)
    bpy.context.collection.objects.link(o)
    o.location = posicion
    if padre:
        o.parent = padre
    return o


def asignar(o, mat, grupo="carroceria"):
    if mat:
        o.data.materials.append(mat)
    o.parent = GRUPOS[grupo]
    o.matrix_parent_inverse = o.parent.matrix_world.inverted()
    return o


def malla(nombre, vertices, caras, mat, grupo="carroceria"):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(vertices, [], caras)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(o)
    return asignar(o, mat, grupo)


def caja(nombre, centro, medidas, mat, bisel=0, grupo="carroceria"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centro)
    o = bpy.context.object
    o.name = nombre
    o.dimensions = medidas
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bisel:
        mod = o.modifiers.new("Cantos suaves", "BEVEL")
        mod.width = bisel
        mod.segments = 2 if grupo == "interior" else 3
        mod.affect = "EDGES"
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod = o.modifiers.new("Normales de panel", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return asignar(o, mat, grupo)


def cilindro(nombre, centro, radio, fondo, mat, eje="Z", lados=32, grupo="carroceria"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=lados, radius=radio, depth=fondo,
                                      end_fill_type="NGON", location=centro)
    o = bpy.context.object
    o.name = nombre
    if eje == "Y":
        o.rotation_euler.x = math.pi / 2
    elif eje == "X":
        o.rotation_euler.y = math.pi / 2
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return asignar(o, mat, grupo)


def tubo(nombre, puntos, radio, mat, grupo="carroceria", cerrado=False, resolucion=1):
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 1
    cu.bevel_depth = radio
    cu.bevel_resolution = resolucion
    sp = cu.splines.new("POLY")
    sp.points.add(len(puntos) - 1)
    for p, co in zip(sp.points, puntos):
        p.co = (*co, 1)
    sp.use_cyclic_u = cerrado
    o = bpy.data.objects.new(nombre, cu)
    bpy.context.collection.objects.link(o)
    return asignar(o, mat, grupo)


def panel(nombre, contorno, mat, grupo="carroceria", espesor=0.018):
    """Polígono plano, triangulado para admitir pasos de rueda cóncavos."""
    vs = [Vector(p) for p in contorno]
    tris = tessellate_polygon([vs])
    indices = {tuple(p): i for i, p in enumerate(vs)}
    caras = [[v if isinstance(v, int) else indices[tuple(v)] for v in tri] for tri in tris]
    o = malla(nombre, contorno, caras, mat, grupo)
    if espesor:
        mod = o.modifiers.new("Chapa", "SOLIDIFY")
        mod.thickness = espesor
        mod.offset = 0
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o


def y_lado(z, signo):
    return signo * (1.07 - max(0, z - 1.72) * 0.067)


def lateral(nombre, perfil, signo, mat, grupo="carroceria", salida=0):
    return panel(nombre, [(x, y_lado(z, signo) + signo * salida, z) for x, z in perfil], mat, grupo)


def borde_lateral(nombre, perfil, signo, mat, radio=0.012, salida=0.018, grupo="carroceria"):
    return tubo(nombre, [(x, y_lado(z, signo) + signo * salida, z) for x, z in perfil], radio, mat,
                grupo, cerrado=True)


def frente_x(z):
    return 3.17 - max(0, z - 1.72) * 0.435


def frontal(nombre, perfil_yz, mat, salida=0.0, grupo="carroceria"):
    return panel(nombre, [(frente_x(z) + salida, y, z) for y, z in perfil_yz], mat, grupo)


def crear_materiales():
    for nombre, rol in [("blanco", "metal"), ("techo", "metal"), ("azul", "pintura_acento"),
                        ("azul_claro", "pintura_acento"), ("goma", "hierro"),
                        ("asientos", "hierro"), ("llanta", "metal"), ("pasamanos", "metal")]:
        M[nombre] = material(rol, D["colores"][nombre])
    for nombre, rol, color in [("oscuro", "hierro", "#25272d"), ("marco", "metal", "#b7b0a6"),
                               ("piso", "hierro", "#575459"), ("tapizado", "hierro", "#56545a"),
                               ("ambar", "pintura_acento", "#fca322"),
                               ("rojo", "pintura_acento", "#cf3028"),
                               ("faro", "metal", "#e3e8f3"),
                               ("amarillo", "pintura_acento", "#f5d16e"),
                               ("grafico", "letrero", "#f9f2e8"),
                               ("celeste", "letrero", "#8dd7f1")]:
        M[nombre] = material(rol, color)
    M["vidrio"] = material("vidrio", "#55545e")
    bs = M["vidrio"].node_tree.nodes.get("Principled BSDF")
    bs.inputs["Alpha"].default_value = 0.32
    bs.inputs["Roughness"].default_value = 0.22
    M["vidrio"].diffuse_color = (*M["vidrio"].diffuse_color[:3], 0.32)
    M["vidrio"].surface_render_method = "DITHERED"
    M["vidrio"].use_transparent_shadow = True
    for nombre in ["blanco", "techo", "azul", "azul_claro"]:
        M[nombre].node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.57
    # El grano se conserva al exportar: normal PBR CC0, con UV de revolución.
    M["neumatico"] = material("hierro", "#323031")
    bs = M["neumatico"].node_tree.nodes.get("Principled BSDF")
    bs.inputs["Roughness"].default_value = .83
    tex = M["neumatico"].node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(DIRECTORIO / D["acabados"]["textura_goma"]), check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    tex.image.pack()
    normal = M["neumatico"].node_tree.nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = D["acabados"]["normal_goma_intensidad"]
    M["neumatico"].node_tree.links.new(tex.outputs["Color"], normal.inputs["Color"])
    M["neumatico"].node_tree.links.new(normal.outputs["Normal"], bs.inputs["Normal"])
    for nombre, metalico, rugosidad in [("llanta", .55, .39), ("marco", .58, .32)]:
        bs = M[nombre].node_tree.nodes.get("Principled BSDF")
        bs.inputs["Metallic"].default_value = metalico
        bs.inputs["Roughness"].default_value = rugosidad


def perfil_bajo(a, b):
    """Borde de chapa recortado alrededor de los dos neumáticos."""
    xs = {a, b}
    for eje in D["ejes"]:
        for i in range(41):
            x = eje - 0.612 + 1.224 * i / 40
            if a < x < b:
                xs.add(x)
    puntos = []
    for x in sorted(xs):
        z = 0.48
        for eje in D["ejes"]:
            if abs(x - eje) < 0.612:
                z = max(z, D["centro_rueda_z"] + math.sqrt(max(0, 0.612 ** 2 - (x - eje) ** 2)))
        puntos.append((x, z))
    return puntos


def carroceria():
    # Piso continuo de pasajeros excepto la caja de escalera de acceso.
    caja("Piso central", (-.02, .16, .91), (6.1, 1.20, .11), M["piso"], grupo="interior")
    caja("Piso derecha posterior", (-1.53, -.59, .91), (3.04, .30, .11), M["piso"], grupo="interior")
    caja("Piso cabina", (1.89, -.59, .91), (2.24, .30, .11), M["piso"], grupo="interior")
    # Pasos de rueda cerrados por dentro; el neumático no atraviesa el piso.
    for signo in [-1, 1]:
        tramos_piso = [(-3.07, -2.26), (-1.0, .02), (.75, 1.29), (2.55, 3.07)] if signo == -1 else [
            (-3.07, -2.26), (-1.0, 1.29), (2.55, 3.07)]
        for a, b in tramos_piso:
            if b > a:
                caja("Piso de borde", ((a + b) / 2, signo * .89, .91), (b - a, .26, .11), M["piso"], grupo="interior")
        for x in D["ejes"]:
            arco = [(x + .60 * math.cos(t), D["centro_rueda_z"] + .60 * math.sin(t))
                    for t in [math.pi * i / 32 for i in range(33)]]
            vs = [(xx, signo * yy, zz) for yy in [.745, 1.045] for xx, zz in arco]
            pozo = malla("Bóveda interior guardabarros", vs,
                         [(i, i + 1, i + 34, i + 33) for i in range(32)], M["piso"], "interior")
            mod = pozo.modifiers.new("Chapa de paso de rueda", "SOLIDIFY")
            mod.thickness = .02
            bpy.context.view_layer.objects.active = pozo
            bpy.ops.object.modifier_apply(modifier=mod.name)
            panel("Cierre interior del guardabarros", [(xx, signo * .745, zz) for xx, zz in arco],
                  M["piso"], "interior")
    caja("Bastidor", (0, 0, 0.47), (5.95, 1.45, 0.17), M["oscuro"], 0.04, "interior")
    for x in D["ejes"]:
        cilindro("Eje", (x, 0, 0.53), 0.10, 1.95, M["oscuro"], "Y", grupo="interior")
    for signo in [-1, 1]:
        tramos = [(-3.15, 0.02), (0.75, 3.15)] if signo == -1 else [(-3.15, 3.15)]
        for a, b in tramos:
            perfil = perfil_bajo(a, b)
            lateral("Chapa azul con pasos de rueda", perfil + [(b, 1.105), (a, 1.105)], signo, M["azul"])
            # Franjas contiguas sin superficies superpuestas: la flecha se recorta
            # también en la chapa blanca y no deja sombra/acné en WebGL.
            quiebre = min(b, 2.37)
            borde_azul = [(a, 1.49), (quiebre, 1.49)]
            if b > 2.37:
                borde_azul.append((b, 1.175))
            lateral("Cintura blanca", borde_azul + [(b, 1.77), (a, 1.77)], signo, M["blanco"])
            banda = [(a, 1.175), (b, 1.175)] + list(reversed(borde_azul))
            # Quitar vértices repetidos en la punta de la flecha.
            banda = [p for i, p in enumerate(banda) if i == 0 or p != banda[i - 1]]
            lateral("Banda azul superior", banda, signo, M["azul"])
            lateral("Filete blanco", [(a, 1.105), (b, 1.105), (b, 1.175), (a, 1.175)], signo, M["blanco"])
            # La moldura termina en el labio del guardabarros, sin barras que
            # crucen el hueco abierto por delante del neumático.
            intervalos = [(a, b)]
            for eje in D["ejes"]:
                siguientes = []
                for u, v in intervalos:
                    if v <= eje - .615 or u >= eje + .615:
                        siguientes.append((u, v))
                    else:
                        if u < eje - .615:
                            siguientes.append((u, eje - .615))
                        if v > eje + .615:
                            siguientes.append((eje + .615, v))
                intervalos = siguientes
            for u, v in intervalos:
                lateral("Nervio inferior", [(u, .68), (v, .68), (v, .704), (u, .704)], signo,
                        M["azul_claro"], salida=0.018)
        for eje in D["ejes"]:
            arco = [(eje + .614 * math.cos(t), y_lado(1, signo) + signo * .025,
                     D["centro_rueda_z"] + .614 * math.sin(t))
                    for t in [math.pi * i / 40 for i in range(41)]]
            tubo("Labio de guardabarros", arco, .024, M["azul_claro"])
            caja("Faldón de goma", (eje - .58, signo * .90, .35), (.055, .29, .38),
                 M["goma"], .01, "interior")
        # Huecos reales: solo pilares y vidrio, sin cubo macizo detrás.
        ventanas = list(D["ventanas_traseras"]) + [[.84, 1.66]]
        if signo == 1:
            ventanas = list(D["ventanas_traseras"]) + [[.02, .75], [.84, 1.66]]
        for i, (a, b) in enumerate(ventanas):
            perfil = [(a, 1.79), (b, 1.79), (b, 2.75), (a + (.10 if i == 0 else 0), 2.75)]
            perfil = contorno_redondeado(perfil, .045, D["acabados"]["segmentos_redondeo"])
            borde_lateral("Goma de ventanilla", perfil, signo, M["goma"], .026, .008)
            borde_lateral("Marco aluminio", perfil, signo, M["marco"], .014, .035)
            lateral("Cristal lateral", perfil, signo, M["vidrio"], "cristales", .007)
            if i in [1, 2]:
                tubo("Guía ventana corredera", [(a, y_lado(2.46, signo) + signo * .026, 2.46),
                                               (b, y_lado(2.46, signo) + signo * .026, 2.46)],
                     .009, M["marco"])
        # Pilares blancos separan de forma estructural cada abertura.
        pilares = [(-3.16, -2.98), (-2.27, -2.20), (-1.51, -1.44), (-.77, -.70),
                   (-.06, .02), (.75, .84), (1.66, 1.76)]
        for a, b in pilares:
            lateral("Pilar blanco", [(a, 1.74), (b, 1.74), (b, 2.82), (a, 2.82)], signo, M["blanco"])
        # Ventanilla trapezoidal de la cabina, A inclinado.
        perfil = [(1.76, 1.79), (3.10, 1.79), (2.67, 2.75), (1.76, 2.75)]
        perfil = contorno_redondeado(perfil, .055, D["acabados"]["segmentos_redondeo"])
        borde_lateral("Marco de cabina oscuro", perfil, signo, M["goma"], .032)
        borde_lateral("Marco de cabina aluminio", perfil, signo, M["marco"], .014, .038)
        lateral("Cristal de cabina", perfil, signo, M["vidrio"], "cristales", .005)
        lateral("Pilar A", [(3.10, 1.74), (3.19, 1.74), (2.76, 2.83), (2.65, 2.83)], signo, M["blanco"])
        lateral("Cinturón superior de ventanas", [(-3.15, 2.76), (2.76, 2.76), (2.71, 2.87), (-3.10, 2.87)],
                signo, M["blanco"])
        # Tapa de servicio, manilla y uniones de chapa.
        borde_lateral("Tapa motor", [(-.99, .56), (-.52, .56), (-.52, .82), (-.99, .82)],
                      signo, M["azul_claro"], .009, .024)
        caja("Manilla de cabina", (1.92, signo * 1.09, 1.36), (.19, .026, .072), M["oscuro"], .012)
        caja("Brillo manilla", (1.92, signo * 1.107, 1.37), (.13, .014, .018), M["llanta"], .005)
        lateral("Junta puerta cabina", [(1.73, 1.18), (1.74, 1.18), (1.74, 1.72), (1.73, 1.72)],
                signo, M["azul_claro"], salida=.027)
    # Hombros elípticos y tangencias continuas, controlados desde la referencia.
    techo_curvo(malla, M)
    # Cintillo que enlaza el parabrisas con el borde delantero del techo.
    # Cierra el encuentro sin ranuras entre marcos y cubierta curva.
    vs = []
    for nivel in range(4):
        t = nivel / 3
        for j in range(33):
            y = -.96 + 1.92*j/32
            yn = abs(y)/.96
            k = 0 if yn <= .62 else 1-math.sqrt(max(0, 1-((yn-.62)/.38)**2))
            z = 2.76*(1-t) + (2.86-.05*k)*t
            x = frente_x(2.76)*(1-t) + 2.76*t
            vs.append((x,y,z))
    malla("Cintillo frontal curvo", vs, [(i*33+j,i*33+j+1,(i+1)*33+j+1,(i+1)*33+j)
                                        for i in range(3) for j in range(32)], M["blanco"])
    caja("Cielo interior", (-.15, 0, 2.91), (5.54, 1.84, .045), M["blanco"], .05, "interior")


def ruedas():
    ruedas_detalladas(D, M, GRUPOS, malla, vacio, cilindro)


def frente():
    # Encuentro de la piel frontal con las chapas de ambos flancos. Las tiras
    # siguen el mismo redondeo y cierran la esquina a todas las alturas.
    zs = [.48, .61, 1.105, 1.175, 1.20, 1.49, 1.67, 1.77]
    for signo in [-1, 1]:
        for a, b in zip(zs, zs[1:]):
            ancho = 1.06 if (a+b)/2 < 1.20 else 1.04
            vs = [(3.15,y_lado(a,signo),a), (frente_x(a),signo*ancho,a),
                  (frente_x(b),signo*ancho,b), (3.15,y_lado(b,signo),b)]
            malla("Encuentro curvo de cabina",vs,[(0,1,2,3)], M["azul" if (a+b)/2 < 1.20 else "blanco"])
    frontal("Panel frontal blanco", [(-1.04, 1.20), (1.04, 1.20), (1.04, 1.67), (-1.04, 1.67)], M["blanco"])
    frontal("Panel faros azul", [(-1.06, .61), (1.06, .61), (1.06, 1.20), (-1.06, 1.20)], M["azul"])
    caja("Parachoques delantero", (3.14, 0, .53), (.24, 2.19, .245), M["azul"], .05)
    caja("Labio superior parachoques", (3.27, 0, .644), (.055, 2.08, .025), M["azul_claro"], .005)
    for signo in [-1, 1]:
        y = signo * .96
        caja("Intermitente frontal marco", (3.182, y, .94), (.045, .17, .29), M["oscuro"], .008)
        caja("Intermitente frontal ámbar", (3.212, y, .94), (.03, .14, .25), M["ambar"], .01)
        caja("Alojamiento doble faro", (3.191, signo * .57, .94), (.04, .64, .235), M["oscuro"], .015)
        for dy, color in [(signo * .145, "faro"), (-signo * .145, "amarillo")]:
            yy = signo * .57 + dy
            caja("Bisel de faro", (3.222, yy, .94), (.031, .26, .185), M["marco"], .013)
            caja("Lente de faro", (3.243, yy, .94), (.02, .212, .141), M[color], .012)
            caja("Centro lente", (3.256, yy, .951), (.007, .14, .082), M[color], .018)
        caja("Respiradero parachoques", (3.291, signo * .43, .59), (.011, .27, .097), M["oscuro"], .008)
    caja("Portaplaca delantero", (3.292, 0, .49), (.035, .42, .22), M["oscuro"], .016)
    caja("Placa delantera", (3.315, 0, .495), (.014, .364, .175), M["blanco"], .012)
    for y in [-.145, .145]:
        cilindro("Tornillo placa", (3.325, y, .555), .009, .008, M["llanta"], "X", 8)
    # Parabrisas de una pieza y banda azul dentro del cristal.
    contorno = contorno_redondeado([(-.955, 1.70), (.955, 1.70), (.895, 2.76), (-.895, 2.76)], .09, D["acabados"]["segmentos_redondeo"])
    frontal("Parabrisas", contorno, M["vidrio"], .012, "cristales")
    pts = [(frente_x(z) + .029, y, z) for y, z in contorno]
    tubo("Burlete parabrisas", pts, .034, M["goma"], cerrado=True)
    tubo("Junquillo parabrisas", [(x + .018, y, z) for x, y, z in pts], .012, M["llanta"], cerrado=True)
    frontal("Franja azul del parabrisas", [(-.885, 2.505), (.885, 2.505), (.875, 2.739), (-.875, 2.739)],
            M["azul"], .031, "decoracion")
    tubo("Filete blanco parabrisas", [(frente_x(2.505) + .043, -.88, 2.505),
                                      (frente_x(2.505) + .043, .88, 2.505)], .008, M["grafico"], "decoracion")
    # Dos limpiaparabrisas apoyados sobre el vidrio.
    for y in [-.51, .51]:
        tubo("Brazo limpiaparabrisas", [(frente_x(1.75) + .068, y - .18, 1.75),
                                        (frente_x(1.88) + .068, y + .04, 1.88)], .013, M["oscuro"])
        tubo("Escobilla limpiaparabrisas", [(frente_x(1.87) + .078, y - .26, 1.87),
                                          (frente_x(1.96) + .078, y + .19, 1.96)], .016, M["goma"])
    # Emblema circular con travesaño horizontal.
    tubo("Emblema frontal", [(3.191, .094 * math.cos(t), 1.405 + .094 * math.sin(t))
                             for t in [2 * math.pi * i / 48 for i in range(48)]],
         .012, M["llanta"], "decoracion", True)
    tubo("Travesaño emblema", [(3.195, -.094, 1.405), (3.195, .094, 1.405)],
         .012, M["llanta"], "decoracion")
    for signo in [-1, 1]:
        tubo("Brazo de espejo", [(2.98, signo * 1.02, 1.82), (3.06, signo * 1.22, 1.82),
                                 (3.06, signo * 1.26, 2.12)], .025, M["oscuro"])
        caja("Espejo retrovisor carcasa", (3.06, signo * 1.29, 2.18), (.17, .13, .38), M["goma"], .025)
        caja("Espejo retrovisor cristal", (2.968, signo * 1.29, 2.18), (.012, .103, .31), M["llanta"], .014)


def trasera():
    for z0, z1, color in [(.48, 1.17, "azul"), (1.17, 1.48, "azul"), (1.48, 1.85, "blanco")]:
        caja("Panel trasero", (-3.16, 0, (z0 + z1) / 2), (.065, 2.12, z1 - z0), M[color], .015)
    caja("Filete blanco trasero", (-3.201, 0, 1.12), (.015, 2.10, .055), M["blanco"])
    # Luna trasera con chaflanes, interior visible.
    perfil = [(-.91, 1.88), (.91, 1.88), (.89, 2.71), (.80, 2.78), (-.80, 2.78), (-.89, 2.71)]
    panel("Luna trasera", [(-3.135, y, z) for y, z in perfil], M["vidrio"], "cristales")
    tubo("Burlete luna trasera", [(-3.158, y, z) for y, z in perfil], .035, M["goma"], cerrado=True)
    tubo("Marco luna trasera", [(-3.171, y, z) for y, z in perfil], .014, M["llanta"], cerrado=True)
    panel("Dintel luneta trasera", [(-3.16, y, z) for y, z in
          [(-1.06, 2.78), (1.06, 2.78), (1.06, 2.89), (-1.06, 2.89)]], M["blanco"], espesor=.025)
    for signo in [-1, 1]:
        # Contorno complementario al chaflán de la luna: sin agujeros ni caras
        # de pilares/dintel superpuestas en el plano posterior.
        panel("Pilar trasero", [(-3.16, signo * y, z) for y, z in
              [(.91, 1.85), (1.06, 1.85), (1.06, 2.78), (.80, 2.78), (.89, 2.71)]],
              M["blanco"], espesor=.025)
        caja("Piloto trasero marco", (-3.213, signo * .87, 1.12), (.055, .225, .54), M["oscuro"], .012)
        for z, h, color in [(1.30, .15, "ambar"), (1.12, .175, "rojo"), (.945, .13, "faro")]:
            caja("Piloto trasero " + color, (-3.249, signo * .87, z), (.026, .175, h), M[color], .01)
        caja("Reflector rojo", (-3.30, signo * .70, .535), (.018, .19, .075), M["rojo"], .006)
    caja("Parachoques trasero", (-3.21, 0, .54), (.155, 2.19, .235), M["azul"], .03)
    caja("Portaplaca trasero", (-3.305, 0, .65), (.025, .42, .265), M["oscuro"], .014)
    caja("Placa trasera", (-3.324, 0, .65), (.014, .35, .20), M["blanco"], .01)
    for y in [-.14, .14]:
        cilindro("Tornillo placa trasera", (-3.336, y, .72), .008, .006, M["llanta"], "X", 8)
    for y in [-.64, .64]:
        tubo("Junta compuerta trasera", [(-3.201, y, 1.48), (-3.201, y, 1.84)], .005, M["marco"])
    cilindro("Escape", (-2.84, .65, .29), .036, .37, M["oscuro"], "X", 16, "interior")


def asiento(x, y, ancho=.42, nombre="Asiento"):
    caja(nombre + " base", (x, y, 1.32), (.43, ancho, .12), M["asientos"], .065, "interior")
    o = caja(nombre + " respaldo", (x - .17, y, 1.74), (.115, ancho, .70), M["asientos"], .065, "interior")
    o.rotation_euler.y = -.08
    caja(nombre + " costura", (x - .105, y, 1.74), (.012, ancho - .075, .48), M["tapizado"], .025, "interior")
    tubo(nombre + " bastidor", [(x - .12, y - ancho * .32, .98), (x - .12, y - ancho * .32, 1.27),
                               (x + .12, y - ancho * .32, 1.27)], .019, M["llanta"], "interior")
    tubo(nombre + " agarradera", [(x - .19, y - ancho * .34, 2.07), (x - .19, y + ancho * .34, 2.07)],
         .014, M["oscuro"], "interior")


def interior_y_puerta():
    for x in [-2.48, -1.70, -.92]:
        for y in [.43, .85, -.64]:
            asiento(x, y, .39)
    for y in [-.65, -.22, .22, .65]:
        asiento(-2.87, y, .40, "Banqueta trasera")
    for y in [.43, .85]:
        asiento(.05, y, .39)
        asiento(.88, y, .39)
    asiento(2.21, .58, .48, "Conductor")
    asiento(1.87, -.57, .48, "Acompañante")
    caja("Tablero de cabina", (2.83, 0, 1.55), (.48, 1.87, .27), M["oscuro"], .06, "interior")
    caja("Instrumentos", (2.57, .55, 1.67), (.10, .57, .16), M["goma"], .03, "interior")
    tubo("Columna dirección", [(2.68, .57, 1.40), (2.39, .57, 1.75)], .034, M["oscuro"], "interior")
    centro = Vector((2.39, .57, 1.75))
    u, v = Vector((.14, 0, .13)), Vector((0, .19, 0))
    tubo("Volante", [centro + u * math.cos(t) + v * math.sin(t)
                     for t in [math.tau * i / 36 for i in range(36)]], .018, M["oscuro"], "interior", True)
    for t in [0, math.tau / 3, 2 * math.tau / 3]:
        tubo("Radio volante", [centro, centro + u * math.cos(t) + v * math.sin(t)], .012, M["oscuro"], "interior")
    # Entrada de tres peldaños, nariz amarilla y caja lateral cerrada.
    for i, (y, z, fondo) in enumerate([(-.98, .45, .20), (-.76, .62, .22), (-.53, .79, .24)]):
        caja(f"Peldaño {i + 1}", (.385, y, z), (.70, fondo, .065), M["piso"], .008, "interior")
        caja(f"Nariz amarilla {i + 1}", (.385, y - fondo / 2, z + .037), (.70, .026, .016),
             M["pasamanos"], .003, "interior")
        caja(f"Contrahuella {i + 1}", (.385, y + fondo / 2, z + .08), (.70, .025, .14), M["oscuro"], grupo="interior")
    for x in [.035, .735]:
        caja("Lateral de caja escalera", (x, -.75, .70), (.025, .59, .43), M["oscuro"], grupo="interior")
        tubo("Pasamanos de acceso", [(x, -.90, .78), (x, -.90, 1.91), (x, -.78, 2.04)],
             .018, M["pasamanos"], "interior")
    lateral("Dintel puerta", [(.02, 2.66), (.75, 2.66), (.75, 2.80), (.02, 2.80)], -1, M["blanco"])
    # Hoja plegada hacia el interior: pivote independiente para futura animación.
    GRUPOS["puerta"] = vacio("puerta_pivote", (.73, -1.055, .45), GRUPOS["raiz"])
    bpy.context.view_layer.update()
    for i, y in enumerate([-.89, -.57]):
        x = .69 if i == 0 else .66
        caja("Hoja plegada inferior", (x, y, 1.07), (.034, .30, 1.16), M["oscuro"], .008, "puerta")
        caja("Hoja plegada cristal", (x, y, 2.11), (.017, .28, .90), M["vidrio"], grupo="puerta")
        for yy in [y - .15, y + .15]:
            tubo("Montante puerta", [(x, yy, .50), (x, yy, 2.63)], .016, M["marco"], "puerta")
        for z in [.50, 1.65, 2.63]:
            tubo("Travesaño puerta", [(x, y - .15, z), (x, y + .15, z)], .014, M["marco"], "puerta")


def rotulo(texto, centro, tamano, signo):
    cu = bpy.data.curves.new(texto, "FONT")
    cu.body = texto
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.size = tamano
    cu.extrude = .0005
    cu.resolution_u = 3
    fuente = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf")
    if fuente.exists():
        cu.font = bpy.data.fonts.load(str(fuente), check_existing=True)
    o = bpy.data.objects.new(texto, cu)
    bpy.context.collection.objects.link(o)
    o.location = centro
    o.rotation_euler = (math.pi / 2, 0, 0) if signo == -1 else (math.pi / 2, 0, math.pi)
    o.scale.x = .95
    asignar(o, M["grafico"], "decoracion")


def graficos():
    # Silueta vectorial del caballo, reconstruida de la lámina.
    caballo = [(-.28, 0), (-.25, .12), (-.22, .22), (-.16, .31), (-.10, .38),
               (-.02, .42), (.01, .49), (.055, .44), (.10, .50), (.11, .42),
               (.17, .40), (.20, .33), (.29, .24), (.28, .19), (.23, .18),
               (.16, .24), (.11, .27), (.07, .22), (.08, .12), (.13, 0)]
    # Filigrana de cuatro lazos con rombos: líneas blancas finas sobre vidrio.
    lazo = [(0, .09), (-.07, .16), (0, .27), (.10, .15), (.04, .08), (.13, -.02),
            (.21, .08), (.13, .17), (.06, .09), (-.03, -.015), (-.13, .08),
            (-.21, -.025), (-.13, -.12), (-.055, -.035), (.04, -.13),
            (-.035, -.23), (-.115, -.13), (-.045, -.055)]
    for signo in [-1, 1]:
        # Flanco izquierdo interpretado con la misma identidad gráfica.
        cx = 1.245
        lateral("Caballo BRONCO", [(cx + signo * -x * .80, 2.15 + z * .80) for x, z in caballo],
                signo, M["grafico"], "decoracion", .050)
        rotulo("BRONCO", (cx, y_lado(2.10, signo) + signo * .065, 2.10), .185, signo)
        # Dos incisiones en la crin y ojo oscuro.
        for dx, z in [(-.10, 2.42), (-.15, 2.37)]:
            tubo("Detalle de crin", [(cx + dx, y_lado(z, signo) + signo * .057, z),
                                    (cx + dx + .05, y_lado(z + .06, signo) + signo * .057, z + .06)],
                 .006, M["asientos"], "decoracion")
        for cx, escala in [(-2.64, .85), (2.22, .88)]:
            for giro in [0, math.pi]:
                puntos = []
                for x, z in lazo:
                    xx = cx + escala * (x * math.cos(giro) - z * math.sin(giro))
                    zz = 2.27 + escala * (x * math.sin(giro) + z * math.cos(giro))
                    puntos.append((xx, y_lado(zz, signo) + signo * .060, zz))
                tubo("Filigrana blanca", puntos, .008, M["grafico"], "decoracion")
    # Insignia alada de la banda azul del parabrisas.
    for radio, altura in [(.105, .069), (.065, .041)]:
        tubo("Sello alado", [(frente_x(2.625 + altura * math.sin(t)) + .052,
                             radio * math.cos(t), 2.625 + altura * math.sin(t))
                            for t in [math.tau * i / 48 for i in range(48)]],
             .006, M["grafico"], "decoracion", True)
    for signo in [-1, 1]:
        for h in [0, .041]:
            perfil = [(signo * .18, 2.60 + h), (signo * .51, 2.60 + h),
                      (signo * .45, 2.65 + h), (signo * .23, 2.65 + h)]
            frontal("Ala celeste", perfil, M["celeste"], .053, "decoracion")
    frontal("Rombo central", [(0, 2.68), (.05, 2.625), (0, 2.57), (-.05, 2.625)], M["grafico"], .055, "decoracion")


def consolidar():
    """Agrupa por material y pivote para limitar llamadas de dibujo en móvil."""
    curvas = [o for o in bpy.context.scene.objects if o.type in {"CURVE", "FONT"}]
    bpy.ops.object.select_all(action="DESELECT")
    for o in curvas:
        o.select_set(True)
    if curvas:
        bpy.context.view_layer.objects.active = curvas[0]
        bpy.ops.object.convert(target="MESH")
    lotes = defaultdict(list)
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            lotes[(o.parent.name, o.data.materials[0].name)].append(o)
    for (padre, mat), obs in lotes.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        if len(obs) > 1:
            bpy.ops.object.join()
        obs[0].name = padre + "__" + mat
        # Los biseles de curvas poligonales pueden producir caras de área cero
        # en sus esquinas. Se limpia la geometría evaluada, antes de exportar.
        bm = bmesh.new()
        bm.from_mesh(obs[0].data)
        bmesh.ops.dissolve_degenerate(bm, dist=0.000001, edges=list(bm.edges))
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        malas = [f for f in bm.faces if f.calc_area() < 1e-11]
        bmesh.ops.delete(bm, geom=malas, context="FACES")
        # Suavizar la curva de cada superficie respetando la separación entre
        # su cara exterior y el canto de chapa; evita reflejos abollados.
        limite = 80 if padre.startswith("rueda_") and mat == M["llanta"].name else 45
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle() > math.radians(limite):
                e.smooth = False
        bm.to_mesh(obs[0].data)
        bm.free()
        if mat != M["neumatico"].name:
            for uv in list(obs[0].data.uv_layers):
                obs[0].data.uv_layers.remove(uv)


def validar():
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    triangulos = 0
    degenerados = 0
    for o in meshes:
        o.data.calc_loop_triangles()
        triangulos += len(o.data.loop_triangles)
        degenerados += sum(t.area < 1e-11 for t in o.data.loop_triangles)
    limites = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    minimo = [min(p[i] for p in limites) for i in range(3)]
    maximo = [max(p[i] for p in limites) for i in range(3)]
    assert degenerados == 0, f"Triángulos degenerados: {degenerados}"
    assert -.015 <= minimo[2] <= .025, f"Ruedas fuera del suelo: {minimo[2]}"
    assert 3.10 <= maximo[2] <= 3.20, f"Altura inesperada: {maximo[2]}"
    if triangulos >= D["acabados"]["presupuesto_triangulos"]:
        print("BRONCO_PRESUPUESTO", sorted([(o.name, len(o.data.loop_triangles)) for o in meshes],
                                         key=lambda t: t[1], reverse=True), flush=True)
    assert triangulos < D["acabados"]["presupuesto_triangulos"], f"Presupuesto: {triangulos}"
    reporte = {"triangulos": triangulos, "mallas": len(meshes), "materiales": len(set(
        m.name for o in meshes for m in o.data.materials)), "triangulos_degenerados": degenerados,
        "limite_min_m": minimo, "limite_max_m": maximo,
        "dimensiones_m": [maximo[i] - minimo[i] for i in range(3)],
        "pivotes_ruedas": [nombre for nombre in GRUPOS if nombre.startswith("rueda_")],
        "validacion_urbana": "No aplica calidad.py de manzanas: vehículo local sin emplazamiento urbano.",
        "interpretacion": D["interpretacion"], "acabados": D["acabados"],
        "normal_goma": {"fuente": "https://ambientcg.com/view?id=Rubber004", "licencia": "CC0 1.0"}}
    (SALIDA / "autobus_bronco.ficha.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False) + "\n")
    print("BRONCO_VALIDACION", json.dumps(reporte, ensure_ascii=False))


def camara(nombre, lugar, objetivo, escala):
    datos = bpy.data.cameras.new(nombre)
    o = bpy.data.objects.new(nombre, datos)
    bpy.context.scene.collection.objects.link(o)
    o.location = lugar
    o.rotation_euler = (Vector(objetivo) - o.location).to_track_quat("-Z", "Y").to_euler()
    datos.type = "ORTHO"
    datos.ortho_scale = escala
    datos.lens = 48
    bpy.context.scene.camera = o
    return o


def estudio():
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.samples = 32
    escena.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for dev in prefs.devices:
            dev.use = dev.type == "CUDA"
        escena.cycles.device = "GPU"
    except Exception:
        escena.cycles.device = "CPU"
    escena.render.resolution_x = 1280
    escena.render.resolution_y = 900
    escena.render.resolution_percentage = 100
    escena.render.image_settings.file_format = "PNG"
    escena.render.film_transparent = False
    escena.world = bpy.data.worlds.new("Estudio lavanda")
    escena.world.use_nodes = True
    escena.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.49, .48, .54, 1)
    escena.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45
    escena.view_settings.view_transform = "AgX"
    suelo = material("calzada", "#b5acb1")
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.012))
    bpy.context.object.name = "ESTUDIO_suelo_no_exportado"
    bpy.context.object.data.materials.append(suelo)
    for nombre, pos, potencia, size, color in [
        ("Principal", (6, -5, 8), 1800, 6, (1, .88, .78)),
        ("Relleno", (-4, -1, 5), 800, 5, (.80, .86, 1)),
        ("Recorte", (1, 5, 6), 1300, 4, (1, .95, .87)),
    ]:
        data = bpy.data.lights.new(nombre, "AREA")
        data.energy, data.shape, data.size, data.color = potencia, "DISK", size, color
        o = bpy.data.objects.new(nombre, data)
        escena.collection.objects.link(o)
        o.location = pos
        o.rotation_euler = (Vector((0, 0, 1.4)) - o.location).to_track_quat("-Z", "Y").to_euler()
    vistas = [("perspectiva", (9, -13, 6), (0, 0, 1.47), 8.3, 1280, 900),
              ("lateral", (0, -12, 1.60), (0, 0, 1.60), 7.8, 1400, 740),
              ("frente", (12, 0, 1.60), (0, 0, 1.60), 4.15, 850, 1050),
              ("trasera", (-12, 0, 1.60), (0, 0, 1.60), 4.15, 850, 1050),
              ("peaton", (7, -10, 1.60), (0, 0, 1.50), 7.9, 1280, 850),
              ("interior", (-1.6, -.1, 2.45), (2.9, .1, 1.4), 4.5, 1100, 850),
              ("rueda", (3.1, -4.2, 1.15), (1.92, -.965, .55), 1.8, 1100, 950)]
    cams = {}
    for nombre, pos, objetivo, escala, rx, ry in vistas:
        cams[nombre] = camara(nombre, pos, objetivo, escala)
    escena.camera = cams["perspectiva"]
    # Referencia empaquetada como imagen, no se usa como textura del modelo.
    ref = DIRECTORIO / D["referencia"]
    if ref.exists():
        im = bpy.data.images.load(str(ref), check_existing=True)
        im.use_fake_user = True
        im.pack()
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = GRUPOS["raiz"]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.shading.color_type = "MATERIAL"
                area.spaces.active.overlay.show_overlays = False
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SALIDA / "autobus_bronco.blend"))
    if "--sin-render" not in sys.argv:
        seleccion = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--vistas=")), None)
        for nombre, pos, objetivo, escala, rx, ry in vistas:
            if nombre == "interior" or (seleccion and nombre not in seleccion):
                continue
            escena.camera = cams[nombre]
            escena.render.resolution_x, escena.render.resolution_y = rx, ry
            escena.render.filepath = str(REVISION / f"{nombre}.png")
            bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    crear_materiales()
    GRUPOS["raiz"] = vacio("autobus_bronco")
    GRUPOS["raiz"]["unidades"] = "metros"
    GRUPOS["raiz"]["frente_blender"] = "+X"
    GRUPOS["raiz"]["origen"] = "suelo, centro longitudinal"
    for nombre in ["carroceria", "interior", "cristales", "decoracion"]:
        GRUPOS[nombre] = vacio(nombre, padre=GRUPOS["raiz"])
    carroceria()
    ruedas()
    frente()
    trasera()
    interior_y_puerta()
    graficos()
    # Convertir las curvas antes de deformar: los marcos y los gráficos siguen
    # exactamente la misma superficie que cristales y chapa.
    bpy.ops.object.select_all(action="DESELECT")
    curvas = [o for o in bpy.context.scene.objects if o.type in {"CURVE", "FONT"}]
    for o in curvas:
        o.select_set(True)
    if curvas:
        bpy.context.view_layer.objects.active = curvas[0]
        bpy.ops.object.convert(target="MESH")
    bpy.context.view_layer.update()
    curvar_cabina(D)
    bpy.context.view_layer.update()
    consolidar()
    bpy.context.view_layer.update()
    validar()
    preparar_movimiento(D, GRUPOS)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(SALIDA / "autobus_bronco.glb"), export_format="GLB",
                              use_selection=True, export_yup=True, export_extras=True,
                              export_animations=True, export_animation_mode="NLA_TRACKS",
                              export_force_sampling=True, export_frame_range=False,
                              export_cameras=False, export_lights=False,
                              export_texcoords=True, export_tangents=True)
    estudio()


if __name__ == "__main__":
    main()
