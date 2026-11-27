"""Utilidades reutilizables en Blender (`bpy`) para construir, riggear, validar y exportar vehículos 3D.

No asume un vehículo concreto ni rutas fijas de proyecto: recibe los datos geométricos,
perfiles de rueda y materiales desde el script específico de cada diseño.
"""
import json
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


def hex_a_rgba_lineal(color_hex, alpha=1.0):
    h = color_hex.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, alpha)


def material_pbr(nombre, color_hex, rugosidad=0.58, metalico=0.0, alpha=1.0):
    mat = bpy.data.materials.get(nombre)
    if mat is None:
        mat = bpy.data.materials.new(nombre)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    rgba = hex_a_rgba_lineal(color_hex, alpha)
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Metallic"].default_value = metalico
    bsdf.inputs["Alpha"].default_value = alpha
    mat.diffuse_color = rgba
    if alpha < 0.999:
        mat.surface_render_method = "DITHERED"
        mat.use_transparent_shadow = True
    return mat


def configurar_normal_goma(mat, ruta_textura: Path, intensidad=0.25):
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.84
    if ruta_textura and Path(ruta_textura).is_file():
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(ruta_textura), check_existing=True)
        tex.image.colorspace_settings.name = "Non-Color"
        tex.image.pack()
        normal = mat.node_tree.nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = intensidad
        mat.node_tree.links.new(tex.outputs["Color"], normal.inputs["Color"])
        mat.node_tree.links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def interpolar_hermite(perfil, x):
    """Interpolación cúbica de Hermite monótona (Fritsch-Carlson), sin sobreimpulsos."""
    if x <= perfil[0][0]:
        return perfil[0][1]
    if x >= perfil[-1][0]:
        return perfil[-1][1]
    pendientes = [(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(perfil, perfil[1:])]
    tangentes = [pendientes[0]]
    for m0, m1 in zip(pendientes, pendientes[1:]):
        tangentes.append(0.0 if m0 * m1 <= 0 else 2.0 * m0 * m1 / (m0 + m1))
    tangentes.append(pendientes[-1])
    for i, (a, b) in enumerate(zip(perfil, perfil[1:])):
        if a[0] <= x <= b[0]:
            h = b[0] - a[0]
            t = (x - a[0]) / h
            return (
                (2 * t ** 3 - 3 * t * t + 1) * a[1]
                + (t ** 3 - 2 * t * t + t) * h * tangentes[i]
                + (-2 * t ** 3 + 3 * t * t) * b[1]
                + (t ** 3 - t * t) * h * tangentes[i + 1]
            )
    return perfil[-1][1]


def contorno_redondeado(perfil, radio=0.04, pasos=3):
    """Redondea las esquinas de un polígono 2D o 3D con filetes cuadráticos tangentes."""
    salida = []
    n = len(perfil)
    for i, punto in enumerate(perfil):
        b = Vector(punto)
        a = Vector(perfil[i - 1])
        c = Vector(perfil[(i + 1) % n])
        d_ab = (a - b).length
        d_cb = (c - b).length
        if d_ab < 1e-6 or d_cb < 1e-6:
            salida.append(tuple(b))
            continue
        dist = min(radio, d_ab * 0.35, d_cb * 0.35)
        inicio = b + (a - b).normalized() * dist
        final = b + (c - b).normalized() * dist
        for j in range(pasos + 1):
            t = j / pasos
            p = (1 - t) ** 2 * inicio + 2 * t * (1 - t) * b + t * t * final
            salida.append(tuple(p))
    return salida


def crear_vacio(nombre, posicion=(0.0, 0.0, 0.0), padre=None):
    o = bpy.data.objects.new(nombre, None)
    bpy.context.collection.objects.link(o)
    o.location = posicion
    if padre is not None:
        o.parent = padre
    return o


def inicializar_jerarquia(id_vehiculo):
    grupos = {}
    raiz = crear_vacio(id_vehiculo)
    raiz["unidades"] = "metros"
    raiz["frente_blender"] = "+X"
    raiz["origen"] = "suelo, centro longitudinal"
    grupos["raiz"] = raiz
    for sub in ("carroceria", "interior", "cristales", "decoracion"):
        grupos[sub] = crear_vacio(sub, padre=raiz)
    bpy.context.view_layer.update()
    return grupos


def vincular(obj, mat, padre):
    if mat is not None and hasattr(obj.data, "materials"):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    if padre is not None:
        obj.parent = padre
        obj.matrix_parent_inverse = padre.matrix_world.inverted()
    return obj


def crear_malla(nombre, vertices, caras, mat, padre, suavizar=False):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(vertices, [], caras)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    if suavizar:
        for p in me.polygons:
            p.use_smooth = True
    obj = bpy.data.objects.new(nombre, me)
    bpy.context.collection.objects.link(obj)
    return vincular(obj, mat, padre)


def crear_superficie_grid(nombre, filas_puntos, mat, padre, cerrar_u=False, cerrar_v=False, invertir=False):
    """Construye una superficie cuádrica suave a partir de una malla `M x N` de puntos 3D."""
    n_u = len(filas_puntos)
    n_v = len(filas_puntos[0])
    verts = [ tuple(p) for fila in filas_puntos for p in fila ]
    caras = []
    lim_u = n_u if cerrar_u else n_u - 1
    lim_v = n_v if cerrar_v else n_v - 1
    for i in range(lim_u):
        i2 = (i + 1) % n_u
        for j in range(lim_v):
            j2 = (j + 1) % n_v
            a = i * n_v + j
            b = i2 * n_v + j
            c = i2 * n_v + j2
            d = i * n_v + j2
            caras.append((a, d, c, b) if invertir else (a, b, c, d))
    obj = crear_malla(nombre, verts, caras, mat, padre, suavizar=True)
    if cerrar_u or cerrar_v:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
    return obj


def suavizar_subsurf(obj, niveles=2):
    """Aplica subdivisión Catmull-Clark para accesorios orgánicos (espejos, asientos, ópticas)."""
    mod = obj.modifiers.new("OrgSubsurf", "SUBSURF")
    mod.levels = niveles
    mod.render_levels = niveles
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def crear_caja(nombre, centro, medidas, mat, padre, bisel=0.0, segmentos_bisel=2):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centro)
    o = bpy.context.object
    o.name = nombre
    o.dimensions = medidas
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bisel > 0:
        mod = o.modifiers.new("Cantos", "BEVEL")
        mod.width = bisel
        mod.segments = segmentos_bisel
        mod.affect = "EDGES"
        bpy.ops.object.modifier_apply(modifier=mod.name)
        wn = o.modifiers.new("Normales", "WEIGHTED_NORMAL")
        bpy.ops.object.modifier_apply(modifier=wn.name)
    return vincular(o, mat, padre)


def crear_cilindro(nombre, centro, radio, fondo, mat, padre, eje="Y", lados=24):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=lados, radius=radio, depth=fondo, end_fill_type="NGON", location=centro
    )
    o = bpy.context.object
    o.name = nombre
    if eje == "Y":
        o.rotation_euler.x = math.pi / 2
    elif eje == "X":
        o.rotation_euler.y = math.pi / 2
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for p in o.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return vincular(o, mat, padre)


def crear_tubo(nombre, puntos, radio, mat, padre, cerrado=False, resolucion=2):
    cu = bpy.data.curves.new(nombre, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 2
    cu.bevel_depth = radio
    cu.bevel_resolution = resolucion
    sp = cu.splines.new("POLY")
    sp.points.add(len(puntos) - 1)
    for p, co in zip(sp.points, puntos):
        p.co = (*co, 1.0)
    sp.use_cyclic_u = cerrado
    o = bpy.data.objects.new(nombre, cu)
    bpy.context.collection.objects.link(o)
    return vincular(o, mat, padre)


def crear_panel(nombre, contorno, mat, padre, espesor=0.016, suavizar=True):
    """Construye un panel 3D (admite contornos cóncavos como pasos de rueda) con espesor."""
    limpios = []
    for p in contorno:
        v = Vector(p)
        if not limpios or (v - limpios[-1]).length > 1e-5:
            limpios.append(v)
    if len(limpios) > 2 and (limpios[0] - limpios[-1]).length <= 1e-5:
        limpios.pop()
    tris = tessellate_polygon([limpios])
    caras = [list(tri) for tri in tris]
    o = crear_malla(nombre, [tuple(v) for v in limpios], caras, mat, padre, suavizar=suavizar)
    if espesor > 0:
        mod = o.modifiers.new("Espesor", "SOLIDIFY")
        mod.thickness = espesor
        mod.offset = 0.0
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o


def crear_torno(
    nombre,
    perfil_rd,
    xc,
    yc,
    zc,
    signo_y,
    mat,
    padre,
    segmentos=56,
    cerrado=False,
    dibujo_banda=None,
    con_uv=False,
):
    """Revoluciona un perfil `(radio, desp_axial)` alrededor del eje Y local de la rueda."""
    vertices = []
    for r, d in perfil_rd:
        for j in range(segmentos + 1):
            t = math.tau * j / segmentos - math.pi / 2.0
            rr = r
            if dibujo_banda is not None:
                r_min, d_max, prof = dibujo_banda
                if r >= r_min and abs(d) <= d_max and (j + (1 if d < 0 else 0)) % 3 == 0:
                    rr -= prof
            vertices.append((xc + rr * math.cos(t), yc + signo_y * d, zc + rr * math.sin(t)))
    n = segmentos + 1
    caras = []
    anillos = len(perfil_rd) if cerrado else len(perfil_rd) - 1
    for i in range(anillos):
        k = (i + 1) % len(perfil_rd)
        for j in range(segmentos):
            if signo_y > 0:
                caras.append((i * n + j, k * n + j, k * n + j + 1, i * n + j + 1))
            else:
                caras.append((i * n + j, i * n + j + 1, k * n + j + 1, k * n + j))
    o = crear_malla(nombre, vertices, caras, mat, padre, suavizar=True)
    if con_uv:
        uv = o.data.uv_layers.new(name="UVMap")
        for p in o.data.polygons:
            for loop in p.loop_indices:
                i, j = divmod(o.data.loops[loop].vertex_index, n)
                uv.data[loop].uv = (j / segmentos * 8.0, i / max(1, len(perfil_rd) - 1) * 2.0)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(o.data)
    bm.free()
    return o


def construir_ruedas_volumetricas(
    datos,
    materiales,
    grupos,
    perfil_neumatico,
    perfil_llanta,
    segmentos_neumatico=56,
    segmentos_llanta=56,
    dibujo_banda=None,
    n_ventilaciones=8,
    radio_ventilaciones=0.132,
    radio_agujero=0.017,
    desp_agujero=0.062,
    ventanas_aleacion=None,
    n_tuercas=4,
    radio_tuercas=0.056,
    radio_buje=0.038,
    desp_buje=0.072,
):
    """Crea la jerarquía de dirección/rodadura y modela neumáticos y llantas perforadas (acero o aleación)."""
    zc = datos["centro_rueda_z"]
    semivia = datos["semivia_ruedas"]
    for ie, x in enumerate(datos["ejes"]):
        es_delantera = ie == 1
        for signo in (-1, 1):
            lado = "derecha" if signo == -1 else "izquierda"
            etapa = "delantera" if es_delantera else "trasera"
            nombre_rueda = f"rueda_{etapa}_{lado}"
            yc = signo * semivia
            if es_delantera:
                nombre_dir = f"direccion_delantera_{lado}"
                grupos[nombre_dir] = crear_vacio(nombre_dir, (x, yc, zc), grupos["raiz"])
                bpy.context.view_layer.update()
                grupos[nombre_rueda] = crear_vacio(nombre_rueda, (0.0, 0.0, 0.0), grupos[nombre_dir])
            else:
                grupos[nombre_rueda] = crear_vacio(nombre_rueda, (x, yc, zc), grupos["raiz"])
            bpy.context.view_layer.update()
            pivote = grupos[nombre_rueda]

            crear_torno(
                "Neumatico radial",
                perfil_neumatico,
                x,
                yc,
                zc,
                signo,
                materiales["neumatico"],
                pivote,
                segmentos=segmentos_neumatico,
                cerrado=False,
                dibujo_banda=dibujo_banda,
                con_uv=True,
            )
            llanta = crear_torno(
                "Llanta perfilada",
                perfil_llanta,
                x,
                yc,
                zc,
                signo,
                materiales["llanta"],
                pivote,
                segmentos=segmentos_llanta,
                cerrado=True,
                con_uv=False,
            )
            cortadores = []
            if ventanas_aleacion:
                # Ventanas trapezoidales/radiales para llantas de aleación multirradio
                for a0, a1, r_int, r_ext in ventanas_aleacion:
                    pasos_a = max(3, int(abs(a1 - a0) / 0.10))
                    arco_ext = [
                        (x + r_ext * math.cos(a0 + (a1 - a0) * k / pasos_a), zc + r_ext * math.sin(a0 + (a1 - a0) * k / pasos_a))
                        for k in range(pasos_a + 1)
                    ]
                    arco_int = [
                        (x + r_int * math.cos(a1 - (a1 - a0) * k / pasos_a), zc + r_int * math.sin(a1 - (a1 - a0) * k / pasos_a))
                        for k in range(pasos_a + 1)
                    ]
                    poli_2d = contorno_redondeado(arco_ext + arco_int, radio=0.008, pasos=2)
                    c_ven = crear_panel(
                        "Corte ventana aleacion",
                        [(px, yc + signo * desp_agujero, pz) for px, pz in poli_2d],
                        materiales["oscuro"],
                        pivote,
                        espesor=0.18,
                    )
                    cortadores.append(c_ven)
            elif n_ventilaciones > 0:
                for j in range(n_ventilaciones):
                    ang = math.tau * j / n_ventilaciones
                    xx = x + radio_ventilaciones * math.cos(ang)
                    zz = zc + radio_ventilaciones * math.sin(ang)
                    cortadores.append(
                        crear_cilindro(
                            "Corte ventilacion",
                            (xx, yc + signo * desp_agujero, zz),
                            radio_agujero,
                            0.14,
                            materiales["oscuro"],
                            pivote,
                            eje="Y",
                            lados=14,
                        )
                    )
            if cortadores:
                bpy.ops.object.select_all(action="DESELECT")
                for c in cortadores:
                    c.select_set(True)
                bpy.context.view_layer.objects.active = cortadores[0]
                if len(cortadores) > 1:
                    bpy.ops.object.join()
                mod = llanta.modifiers.new("Ventilaciones reales", "BOOLEAN")
                mod.operation = "DIFFERENCE"
                mod.solver = "EXACT"
                mod.object = cortadores[0]
                bpy.context.view_layer.objects.active = llanta
                bpy.ops.object.modifier_apply(modifier=mod.name)
                bpy.data.objects.remove(cortadores[0], do_unlink=True)

            r_freno = (
                max(v[3] for v in ventanas_aleacion) * 0.86
                if ventanas_aleacion
                else radio_ventilaciones + radio_agujero * 1.4
            )
            crear_cilindro(
                "Freno interior",
                (x, yc + signo * (desp_buje - 0.056), zc),
                r_freno,
                0.032,
                materiales["oscuro"],
                pivote,
                eje="Y",
                lados=28,
            )
            crear_cilindro(
                "Copa central buje",
                (x, yc + signo * desp_buje, zc),
                radio_buje,
                0.028,
                materiales["llanta"],
                pivote,
                eje="Y",
                lados=32,
            )
            crear_cilindro(
                "Tapon buje",
                (x, yc + signo * (desp_buje + 0.014), zc),
                radio_buje * 0.56,
                0.008,
                materiales["oscuro"],
                pivote,
                eje="Y",
                lados=24,
            )
            for j in range(n_tuercas):
                ang = math.tau * j / n_tuercas + math.pi / n_tuercas
                xx = x + radio_tuercas * math.cos(ang)
                zz = zc + radio_tuercas * math.sin(ang)
                crear_cilindro(
                    "Alojamiento tuerca",
                    (xx, yc + signo * (desp_buje - 0.004), zz),
                    0.015,
                    0.008,
                    materiales["oscuro"],
                    pivote,
                    eje="Y",
                    lados=12,
                )
                crear_cilindro(
                    "Tuerca rueda",
                    (xx, yc + signo * (desp_buje + 0.006), zz),
                    0.011,
                    0.016,
                    materiales.get("cromo", materiales["llanta"]),
                    pivote,
                    eje="Y",
                    lados=6,
                )


def consolidar_lotes(raiz, nombres_mat_con_uv=(), nombre_mat_llanta=None):
    """Convierte curvas, agrupa por (pivote, material), limpia caras degeneradas y ajusta bordes duros."""
    def pertenece(o):
        p = o
        while p is not None:
            if p == raiz:
                return True
            p = p.parent
        return False

    curvas = [o for o in bpy.context.scene.objects if pertenece(o) and o.type in {"CURVE", "FONT"}]
    bpy.ops.object.select_all(action="DESELECT")
    for o in curvas:
        o.select_set(True)
    if curvas:
        bpy.context.view_layer.objects.active = curvas[0]
        bpy.ops.object.convert(target="MESH")
    bpy.context.view_layer.update()

    lotes = defaultdict(list)
    for o in list(bpy.context.scene.objects):
        if pertenece(o) and o.type == "MESH" and o.parent is not None and len(o.data.materials) > 0:
            # Hornear la transformación local respecto al pivote padre para que todas las mallas
            # queden con matriz identidad limpia bajo su pivote y centradas exactamente en el eje.
            if o.data.users > 1:
                o.data = o.data.copy()
            mat_local_padre = o.parent.matrix_world.inverted() @ o.matrix_world
            o.data.transform(mat_local_padre)
            o.matrix_parent_inverse.identity()
            o.location = (0.0, 0.0, 0.0)
            o.rotation_mode = "XYZ"
            o.rotation_euler = (0.0, 0.0, 0.0)
            o.scale = (1.0, 1.0, 1.0)
            o.data.update()
            lotes[(o.parent.name, o.data.materials[0].name)].append(o)
    bpy.context.view_layer.update()

    for (nombre_padre, nombre_mat), objetos in lotes.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objetos:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objetos[0]
        if len(objetos) > 1:
            bpy.ops.object.join()
        unido = objetos[0]
        unido.name = f"{nombre_padre}__{nombre_mat}"
        unido.data.name = unido.name

        bm = bmesh.new()
        bm.from_mesh(unido.data)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=list(bm.edges))
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        degeneradas = [f for f in bm.faces if f.calc_area() < 1e-11]
        if degeneradas:
            bmesh.ops.delete(bm, geom=degeneradas, context="FACES")
        limite_grados = 78.0 if (nombre_padre.startswith("rueda_") and nombre_mat == nombre_mat_llanta) else 58.0
        umbral_rad = math.radians(limite_grados)
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle() > umbral_rad:
                e.smooth = False
        bm.to_mesh(unido.data)
        bm.free()

        if nombre_mat not in nombres_mat_con_uv:
            for uv in list(unido.data.uv_layers):
                unido.data.uv_layers.remove(uv)


def preparar_rig_y_clips(datos, grupos):
    """Guarda metadatos `movimiento` en la raíz y genera pistas NLA `rodar_adelante` y `rodar_atras`."""
    configuracion = dict(
        datos["movimiento"],
        radio_rueda=datos["radio_rueda"],
        eje_trasero=datos["ejes"][0],
        eje_delantero=datos["ejes"][1],
        semivia=datos["semivia_ruedas"],
    )
    grupos["raiz"]["movimiento"] = configuracion
    grupos["raiz"]["animacion"] = "Rodadura por distancia; dirección Ackermann. Clips: 1 vuelta por segundo."
    escena = bpy.context.scene
    escena.render.fps = 24
    escena.frame_start, escena.frame_end = 1, 25
    for nombre, objeto in grupos.items():
        if not nombre.startswith("rueda_"):
            continue
        objeto.rotation_mode = "XYZ"
        objeto.animation_data_create()
        for clip, signo in (("rodar_adelante", 1.0), ("rodar_atras", -1.0)):
            objeto.animation_data.action = None
            for frame in range(1, 26):
                objeto.rotation_euler.y = signo * math.tau * (frame - 1) / 24.0
                objeto.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)
            accion = objeto.animation_data.action
            accion.name = f"{clip}_{nombre}"
            slot = getattr(objeto.animation_data, "action_slot", None)
            objeto.animation_data.action = None
            pista = objeto.animation_data.nla_tracks.new()
            pista.name = clip
            tira = pista.strips.new(clip, 1, accion)
            if slot is not None and hasattr(tira, "action_slot"):
                tira.action_slot = slot
            tira.extrapolation = "NOTHING"
        objeto.rotation_euler.y = 0.0
    escena.frame_set(1)
    return configuracion


def validar_geometria_vehiculo(raiz, datos, ruta_ficha: Path = None, info_extra=None):
    def pertenece(o):
        p = o
        while p is not None:
            if p == raiz:
                return True
            p = p.parent
        return False

    meshes = [o for o in bpy.context.scene.objects if pertenece(o) and o.type == "MESH"]
    triangulos = 0
    degenerados = 0
    for o in meshes:
        o.data.calc_loop_triangles()
        triangulos += len(o.data.loop_triangles)
        degenerados += sum(t.area < 1e-11 for t in o.data.loop_triangles)

    esquinas = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    minimo = [min(p[i] for p in esquinas) for i in range(3)]
    maximo = [max(p[i] for p in esquinas) for i in range(3)]
    dims = [maximo[i] - minimo[i] for i in range(3)]
    presupuesto = datos.get("acabados", {}).get("presupuesto_triangulos", 75000)

    assert degenerados == 0, f"Triángulos degenerados encontrados: {degenerados}"
    assert -0.015 <= minimo[2] <= 0.020, f"Contacto con suelo inválido min_z={minimo[2]:.4f}"
    assert abs(maximo[2] - datos["alto"]) <= 0.08, f"Altura {maximo[2]:.3f} m difiere de meta {datos['alto']} m"
    assert triangulos < presupuesto, f"Triángulos ({triangulos}) superan presupuesto ({presupuesto})"

    reporte = {
        "id": datos["id"],
        "nombre": datos["nombre"],
        "triangulos": triangulos,
        "mallas": len(meshes),
        "materiales": len({m.name for o in meshes for m in o.data.materials}),
        "triangulos_degenerados": degenerados,
        "limite_min_m": [round(v, 4) for v in minimo],
        "limite_max_m": [round(v, 4) for v in maximo],
        "dimensiones_m": [round(v, 4) for v in dims],
        "pivotes_ruedas": [
            "rueda_trasera_derecha",
            "rueda_trasera_izquierda",
            "rueda_delantera_derecha",
            "rueda_delantera_izquierda",
        ],
        "validacion_urbana": "Vehículo móvil local sin emplazamiento estático en manzanas.",
        "interpretacion": datos.get("interpretacion", []),
    }
    if info_extra:
        reporte.update(info_extra)
    if ruta_ficha is not None:
        ruta_ficha.parent.mkdir(parents=True, exist_ok=True)
        ruta_ficha.write_text(json.dumps(reporte, indent=2, ensure_ascii=False) + "\n")
    return reporte


def seleccionar_jerarquia(raiz):
    bpy.ops.object.select_all(action="DESELECT")
    pila = [raiz]
    while pila:
        actual = pila.pop()
        actual.select_set(True)
        pila.extend(actual.children)
    bpy.context.view_layer.objects.active = raiz


def exportar_glb_vehiculo(raiz, ruta_glb: Path):
    ruta_glb.parent.mkdir(parents=True, exist_ok=True)
    seleccionar_jerarquia(raiz)
    bpy.ops.export_scene.gltf(
        filepath=str(ruta_glb),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_extras=True,
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_force_sampling=True,
        export_frame_range=False,
        export_cameras=False,
        export_lights=False,
        export_texcoords=True,
        export_tangents=True,
    )


def configurar_estudio_y_renderizar(
    raiz,
    datos,
    ruta_blend: Path,
    carpeta_renders: Path = None,
    vistas_pedidas=None,
    ruta_referencia: Path = None,
    sin_render=False,
):
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.samples = 32
    escena.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        hay_cuda = False
        for dev in prefs.devices:
            dev.use = dev.type in {"CUDA", "OPTIX"}
            hay_cuda = hay_cuda or dev.use
        escena.cycles.device = "GPU" if hay_cuda else "CPU"
    except Exception:
        escena.cycles.device = "CPU"

    escena.render.image_settings.file_format = "PNG"
    escena.render.film_transparent = False
    escena.world = bpy.data.worlds.new("Estudio_Vehiculo")
    escena.world.use_nodes = True
    bg = escena.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.50, 0.48, 0.54, 1.0)
    bg.inputs["Strength"].default_value = 0.52
    escena.view_settings.view_transform = "AgX"

    mat_suelo = material_pbr("ESTUDIO_calzada", "#b8aeb6", rugosidad=0.95)
    bpy.ops.mesh.primitive_plane_add(size=160.0, location=(0.0, 0.0, -0.008))
    suelo = bpy.context.object
    suelo.name = "ESTUDIO_suelo_no_exportado"
    suelo.data.materials.append(mat_suelo)

    largo = datos["largo"]
    ancho = datos["ancho"]
    alto = datos["alto"]
    zc = alto * 0.48
    luces = [
        ("ESTUDIO_Principal", (5.5, -5.0, 6.8), 1500, 5.5, (1.0, 0.90, 0.80)),
        ("ESTUDIO_Relleno", (-4.5, -1.5, 4.5), 720, 5.0, (0.82, 0.88, 1.0)),
        ("ESTUDIO_Recorte", (0.8, 5.0, 5.2), 1100, 4.0, (1.0, 0.96, 0.89)),
    ]
    for nombre, pos, energia, tam, col in luces:
        ldata = bpy.data.lights.new(nombre, "AREA")
        ldata.energy, ldata.shape, ldata.size, ldata.color = energia, "DISK", tam, col
        lo = bpy.data.objects.new(nombre, ldata)
        escena.collection.objects.link(lo)
        lo.location = pos
        lo.rotation_euler = (Vector((0.0, 0.0, zc)) - lo.location).to_track_quat("-Z", "Y").to_euler()

    x_del = datos["ejes"][1]
    y_der = -datos["semivia_ruedas"]
    r_rueda = datos["radio_rueda"]
    vistas = [
        ("perspectiva", "PERSP", (largo * 1.42, -largo * 1.65, alto * 1.32), (0.05, 0.0, alto * 0.48), 46.0, 1280, 900),
        ("lateral", "ORTHO", (0.0, -12.0, alto * 0.52), (0.0, 0.0, alto * 0.52), largo * 1.22, 1400, 740),
        ("frente", "ORTHO", (12.0, 0.0, alto * 0.52), (0.0, 0.0, alto * 0.52), ancho * 1.48, 960, 960),
        ("trasera", "ORTHO", (-12.0, 0.0, alto * 0.52), (0.0, 0.0, alto * 0.52), ancho * 1.48, 960, 960),
        ("peaton", "PERSP", (largo * 1.25, -largo * 1.35, 1.60), (0.0, 0.0, alto * 0.52), 42.0, 1280, 850),
        ("rueda", "ORTHO", (x_del + 0.85, y_der - 3.2, r_rueda * 1.35), (x_del, y_der, r_rueda * 1.02), r_rueda * 3.1, 1000, 900),
    ]
    cams = {}
    for nombre, tipo, pos, mira, param, _, _ in vistas:
        cdata = bpy.data.cameras.new(f"ESTUDIO_cam_{nombre}")
        co = bpy.data.objects.new(f"ESTUDIO_cam_{nombre}", cdata)
        escena.collection.objects.link(co)
        co.location = pos
        co.rotation_euler = (Vector(mira) - co.location).to_track_quat("-Z", "Y").to_euler()
        cdata.type = tipo
        if tipo == "ORTHO":
            cdata.ortho_scale = param
        else:
            cdata.lens = param
        cams[nombre] = co
    escena.camera = cams["perspectiva"]

    if ruta_referencia and Path(ruta_referencia).is_file():
        im = bpy.data.images.load(str(ruta_referencia), check_existing=True)
        im.use_fake_user = True
        im.pack()

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = raiz
    ruta_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(ruta_blend))

    if not sin_render and carpeta_renders is not None:
        carpeta_renders.mkdir(parents=True, exist_ok=True)
        for nombre, _, _, _, _, rx, ry in vistas:
            if vistas_pedidas and nombre not in vistas_pedidas:
                continue
            escena.camera = cams[nombre]
            escena.render.resolution_x = rx
            escena.render.resolution_y = ry
            escena.render.resolution_percentage = 100
            escena.render.filepath = str(carpeta_renders / f"{nombre}.png")
            bpy.ops.render.render(write_still=True)
