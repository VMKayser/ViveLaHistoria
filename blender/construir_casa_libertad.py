"""Construye la arquitectura de la Casa de la Libertad (patio y Sala Mayor), hornea la
iluminación global con Cycles y exporta una malla optimizada para Godot.

Uso (desde la raíz del repositorio):
    blender -b --factory-startup --python blender/construir_casa_libertad.py

Salidas:
    juego/assets/arquitectura/casa_libertad.glb    malla única, materiales por nombre, colisión (-col)
    juego/assets/arquitectura/luz_horneada.png     luz del cielo, rebotes del sol y velas (UV de la malla)
    blender/casa_libertad.blend                    escena para seguir modelando

El PNG guarda sqrt(luz / RANGO) para conservar precisión en las sombras; el shader de Godot
(juego/shaders/arquitectura_horneada.gdshader) lo decodifica.

Coordenadas: el script recibe posiciones y tamaños como en Godot (Y arriba, -Z hacia el
fondo de la sala) y los convierte a Blender (Z arriba). El exportador glTF los devuelve a Y arriba.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

RAIZ = Path(__file__).resolve().parent.parent
TEXTURAS = RAIZ / "juego" / "assets" / "texturas"
SALIDA = RAIZ / "juego" / "assets" / "arquitectura"
CIELO = RAIZ / "juego" / "assets" / "cielo" / "kloofendal_48d_partly_cloudy_puresky.hdr"

RESOLUCION = 2048
MUESTRAS = 256
RANGO = 4.0

# Energías equivalentes a las de Godot (ver asamblea_1825.tscn).
ENERGIA_CIELO = 0.55                 # ambient_light_energy del entorno
ENERGIA_SOL = 1.7 * math.pi          # Cycles mide el sol en W/m2; Godot ya incluye el 1/pi
DIRECCION_AL_SOL = (0.72, 0.78, 0.42)  # en coordenadas de Godot
VELAS = [(0.0, 5.2, -17.0), (0.0, 5.2, -24.0), (0.0, 5.2, -30.5)]

# Material: (textura de Poly Haven para el color promedio, tinte igual al de Godot)
MATERIALES = {
    "cal": ("white_stucco", (1.0, 0.99, 0.96)),
    "zocalo": ("white_stucco", (0.58, 0.27, 0.17)),
    "empedrado": ("cobblestone_floor_04", (1.0, 1.0, 1.0)),
    "baldosa": ("square_brick_floor", (1.0, 1.0, 1.0)),
    "madera_techo": ("dark_wooden_planks", (0.8, 0.75, 0.7)),
    "viga": ("rough_wood", (0.45, 0.32, 0.22)),
    "madera_mueble": ("wood_table_worn", (0.85, 0.7, 0.6)),
    "piedra": ("large_sandstone_blocks_01", (1.0, 0.97, 0.92)),
    "teja": ("clay_roof_tiles", (1.0, 1.0, 1.0)),
    "terciopelo": (None, (0.3, 0.04, 0.05)),
}


# ------------------------------------------------------------------ utilidades

def a_blender(p):
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    x, y, z = p
    return Vector((x, -z, y))


def tam_a_blender(t):
    x, y, z = t
    return Vector((x, z, y))


def rot_a_blender(rot):
    """rot de Godot ('x'|'y'|'z', grados) -> Euler de Blender."""
    if rot is None:
        return Euler((0, 0, 0))
    eje, grados = rot
    r = math.radians(grados)
    if eje == "x":
        return Euler((r, 0, 0))
    if eje == "y":
        return Euler((0, 0, r))
    return Euler((0, -r, 0))


def limpiar_escena():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def crear_material(nombre, textura, tinte):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    color = Vector((0.6, 0.6, 0.6))
    if textura:
        ruta = TEXTURAS / textura / "albedo.jpg"
        imagen = bpy.data.images.load(str(ruta), check_existing=True)
        imagen.scale(64, 64)
        srgb = np.array(imagen.pixels[:]).reshape(-1, 4)[:, :3]
        lineal = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
        color = Vector(lineal.mean(axis=0).tolist())
        bpy.data.images.remove(imagen)
    color = Vector((color.x * tinte[0], color.y * tinte[1], color.z * tinte[2]))
    if textura is None:
        color = Vector(tinte)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def objeto_desde_bmesh(nombre, bm, material):
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    malla.materials.append(material)
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.collection.objects.link(obj)
    return obj


def caja(nombre, centro, tam, material, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    escala = tam_a_blender(tam)
    for v in bm.verts:
        v.co = Vector((v.co.x * escala.x, v.co.y * escala.y, v.co.z * escala.z))
    obj = objeto_desde_bmesh(nombre, bm, MAT[material])
    obj.location = a_blender(centro)
    obj.rotation_euler = rot_a_blender(rot)
    return obj


def cilindro(nombre, centro, radio, alto, material, lados=40, eje="vertical"):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=radio, radius2=radio, depth=alto)
    obj = objeto_desde_bmesh(nombre, bm, MAT[material])
    obj.location = a_blender(centro)
    if eje == "x":  # eje a lo largo de X de Godot (= X de Blender)
        obj.rotation_euler = Euler((0, math.pi / 2, 0))
    return obj


def restar(base, *cortes):
    """Aplica restas booleanas y borra los objetos de corte."""
    for corte in cortes:
        mod = base.modifiers.new(f"resta_{corte.name}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = corte
        mod.solver = "EXACT"
        corte.hide_render = True
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    evaluado = base.evaluated_get(deps)
    nueva = bpy.data.meshes.new_from_object(evaluado)
    base.modifiers.clear()
    vieja = base.data
    base.data = nueva
    bpy.data.meshes.remove(vieja)
    for corte in cortes:
        bpy.data.objects.remove(corte, do_unlink=True)
    return base


def unir(objetos, nombre):
    """Une todos los objetos en una malla con materiales compartidos."""
    materiales = list(MAT.values())
    indice = {m.name: i for i, m in enumerate(materiales)}
    bpy.context.view_layer.update()
    bm = bmesh.new()
    for obj in objetos:
        malla = obj.data.copy()
        malla.transform(obj.matrix_world)
        for poligono in malla.polygons:
            poligono.material_index = indice[obj.data.materials[poligono.material_index].name]
        bm.from_mesh(malla)
        bpy.data.meshes.remove(malla)
    for obj in objetos:
        bpy.data.objects.remove(obj, do_unlink=True)
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    for m in materiales:
        malla.materials.append(m)
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.collection.objects.link(obj)
    return obj


# ------------------------------------------------------------------ arquitectura

def construir():
    partes = []
    add = partes.append

    # Patio
    add(caja("PisoPatio", (0, -0.1, -0.6), (20.8, 0.2, 22), "empedrado"))
    add(caja("MuroOeste", (-10.6, 2.3, -0.6), (0.4, 4.6, 22), "cal"))
    add(caja("MuroEste", (10.6, 2.3, -0.6), (0.4, 4.6, 22), "cal"))
    add(caja("MuroSur", (0, 2.3, 10.6), (21.6, 4.6, 0.4), "cal"))
    add(caja("MuroNorteOeste", (-8.6, 2.3, -11.8), (4.4, 4.6, 0.4), "cal"))
    add(caja("MuroNorteEste", (8.6, 2.3, -11.8), (4.4, 4.6, 0.4), "cal"))
    add(caja("ZocaloPatioOeste", (-10.38, 0.5, -0.6), (0.04, 1.0, 22), "zocalo"))
    add(caja("ZocaloPatioSur", (0, 0.5, 10.38), (20.8, 1.0, 0.04), "zocalo"))
    add(caja("ZocaloPatioNO", (-5.8, 0.5, -11.58), (9.2, 1.0, 0.04), "zocalo"))
    add(caja("ZocaloPatioNE", (5.8, 0.5, -11.58), (9.2, 1.0, 0.04), "zocalo"))
    add(caja("ZocaloPatioEste", (10.38, 0.5, -0.6), (0.04, 1.0, 22), "zocalo"))

    # Arcada del claustro oeste: 6 arcos de medio punto
    arcada = caja("ArcadaOeste", (-7.6, 2.0, -0.6), (0.6, 4.0, 22), "piedra")
    cortes = []
    for i in range(6):
        z = -11.6 + (22 / 6) * (i + 0.5)
        cortes.append(caja(f"vano{i}", (-7.6, 1.15 - 0.01, z), (0.9, 2.32, 2.5), "piedra"))
        cortes.append(cilindro(f"arco{i}", (-7.6, 2.3, z), 1.25, 0.9, "piedra", lados=32, eje="x"))
    add(restar(arcada, *cortes))
    add(caja("TechoCorredorOeste", (-8.9, 4.1, -0.6), (3.2, 0.2, 22), "madera_techo"))
    add(caja("TejadoOeste", (-8.5, 4.55, -0.6), (4.4, 0.14, 22.4), "teja", rot=("z", -15)))

    # Galería alta este
    add(caja("GaleriaAlta", (8.9, 0.75, -0.6), (3.4, 1.5, 14.8), "piedra"))
    add(caja("PisoGaleria", (8.9, 1.52, -0.6), (3.4, 0.04, 14.8), "madera_mueble"))
    add(caja("Escalon1", (6.0, 0.25, 5.6), (0.8, 0.5, 1.6), "piedra"))
    add(caja("Escalon2", (6.8, 0.5, 5.6), (0.8, 1.0, 1.6), "piedra"))
    for i in range(5):
        add(caja(f"PieDerecho{i}", (7.4, 2.95, -7.6 + 3.5 * i), (0.24, 2.9, 0.24), "viga"))
    add(caja("TechoGaleria", (8.9, 4.45, -0.6), (3.4, 0.15, 15.2), "madera_techo"))
    add(caja("TejadoEste", (8.6, 4.75, -0.6), (4.6, 0.14, 15.6), "teja", rot=("z", 15)))

    # Pileta
    taza = cilindro("Taza", (0, 0.3, 0), 1.5, 0.6, "piedra")
    hueco = cilindro("Hueco", (0, 0.46, 0), 1.32, 0.6, "piedra")
    add(restar(taza, hueco))
    add(cilindro("Pilar", (0, 0.7, 0), 0.18, 1.4, "piedra", lados=20))
    add(cilindro("Copa", (0, 1.4, 0), 0.5, 0.14, "piedra", lados=28))
    add(caja("MesaCredencial", (3, 0.4, 3), (1.0, 0.8, 0.6), "madera_mueble"))

    # Portada de piedra
    add(caja("JambaOeste", (-1.38, 1.7, -11.55), (0.36, 3.4, 0.5), "piedra"))
    add(caja("JambaEste", (1.38, 1.7, -11.55), (0.36, 3.4, 0.5), "piedra"))
    add(caja("DintelPortada", (0, 3.6, -11.55), (3.2, 0.4, 0.5), "piedra"))

    # Sala Mayor
    add(caja("PisoSala", (0, -0.1, -23.9), (12.4, 0.2, 24.6), "baldosa"))
    add(caja("ParedOeste", (-6.2, 3.5, -24), (0.4, 7, 24.4), "cal"))
    pared_este = caja("ParedEste", (6.2, 3.5, -24), (0.4, 7, 24.4), "cal")
    ventanas = [caja(f"ventana{i}", (6.2, 4.3, z), (0.8, 2.4, 1.6), "cal") for i, z in enumerate([-16, -21, -26, -31])]
    add(restar(pared_este, *ventanas))
    add(caja("ParedNorte", (0, 3.5, -36.2), (12.8, 7, 0.4), "cal"))
    add(caja("ParedSurOeste", (-3.8, 3.5, -11.8), (5.2, 7, 0.4), "cal"))
    add(caja("ParedSurEste", (3.8, 3.5, -11.8), (5.2, 7, 0.4), "cal"))
    add(caja("SobrePuerta", (0, 5.2, -11.8), (2.4, 3.6, 0.4), "cal"))
    add(caja("ZocaloSalaOeste", (-5.98, 0.6, -24), (0.04, 1.2, 23.9), "zocalo"))
    add(caja("ZocaloSalaEste", (5.98, 0.6, -24), (0.04, 1.2, 23.9), "zocalo"))
    add(caja("ZocaloSalaNorte", (0, 0.6, -35.98), (11.9, 1.2, 0.04), "zocalo"))
    add(caja("ZocaloSalaSO", (-3.6, 0.6, -12.02), (4.8, 1.2, 0.04), "zocalo"))
    add(caja("ZocaloSalaSE", (3.6, 0.6, -12.02), (4.8, 1.2, 0.04), "zocalo"))
    add(caja("Artesonado", (0, 7.15, -24), (12.8, 0.3, 24.8), "madera_techo"))
    for i in range(24):
        add(caja(f"Viga{i}", (0, 6.86, -12.6 - i), (12.4, 0.28, 0.22), "viga"))
    add(caja("CornisaOeste", (-5.82, 6.8, -24), (0.36, 0.4, 24.4), "viga"))
    add(caja("CornisaEste", (5.82, 6.8, -24), (0.36, 0.4, 24.4), "viga"))
    add(caja("Coro", (0, 3.6, -13.5), (11.98, 0.3, 3), "madera_mueble"))
    add(caja("PilarCoroOeste", (-3, 1.725, -14.85), (0.3, 3.45, 0.3), "viga"))
    add(caja("PilarCoroEste", (3, 1.725, -14.85), (0.3, 3.45, 0.3), "viga"))
    add(caja("MesaPresidencia", (0, 0.425, -32), (4, 0.85, 1.2), "madera_mueble"))
    add(caja("Pano", (0, 0.88, -32), (4.1, 0.06, 1.32), "terciopelo"))
    add(caja("Faldon", (0, 0.52, -31.33), (4.1, 0.72, 0.03), "terciopelo"))
    return partes


# ------------------------------------------------------------------ luces y horneado

def preparar_luces():
    mundo = bpy.data.worlds.new("Cielo")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    nodos = mundo.node_tree.nodes
    entorno = nodos.new("ShaderNodeTexEnvironment")
    entorno.image = bpy.data.images.load(str(CIELO))
    fondo = nodos["Background"]
    fondo.inputs["Strength"].default_value = ENERGIA_CIELO
    mundo.node_tree.links.new(entorno.outputs["Color"], fondo.inputs["Color"])

    sol_datos = bpy.data.lights.new("Sol", "SUN")
    sol_datos.energy = ENERGIA_SOL
    sol_datos.angle = math.radians(0.53)
    sol_datos.color = (1.0, 0.95, 0.86)
    sol = bpy.data.objects.new("Sol", sol_datos)
    bpy.context.collection.objects.link(sol)
    hacia_sol = a_blender(DIRECCION_AL_SOL).normalized()
    sol.rotation_euler = (-hacia_sol).to_track_quat("-Z", "Y").to_euler()

    velas = []
    for i, p in enumerate(VELAS):
        datos = bpy.data.lights.new(f"Velas{i}", "POINT")
        datos.energy = 60.0
        datos.color = (1.0, 0.72, 0.45)
        datos.shadow_soft_size = 0.4
        obj = bpy.data.objects.new(f"Velas{i}", datos)
        obj.location = a_blender(p)
        bpy.context.collection.objects.link(obj)
        velas.append(obj)
    return fondo, sol, velas


def configurar_cycles():
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for tipo in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = tipo
            prefs.refresh_devices()
            if any(d.type == tipo for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == tipo
                escena.cycles.device = "GPU"
                print(f"Horneando con GPU ({tipo})")
                break
        except TypeError:
            continue
    else:
        escena.cycles.device = "CPU"
        print("Horneando con CPU")
    escena.cycles.samples = MUESTRAS
    escena.cycles.max_bounces = 6
    escena.cycles.diffuse_bounces = 4
    escena.render.bake.margin = 8
    escena.render.bake.use_clear = True


def uv_de_luz(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    obj.data.uv_layers.new(name="luz")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=1.0)
    bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def hornear(obj, imagen, filtro):
    for mat in obj.data.materials:
        nodos = mat.node_tree.nodes
        nodo = nodos.get("destino_horneado") or nodos.new("ShaderNodeTexImage")
        nodo.name = "destino_horneado"
        nodo.image = imagen
        nodos.active = nodo
    inicio = time.time()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter=filtro, margin=8, use_clear=True)
    print(f"  horneado {sorted(filtro)} en {time.time() - inicio:.0f} s")
    return np.array(imagen.pixels[:], dtype=np.float32).reshape(RESOLUCION, RESOLUCION, 4)[:, :, :3]


def suavizar(luz, radio=1):
    """Promedio de caja para quitar ruido residual (la luz indirecta es de baja frecuencia)."""
    acumulado = np.zeros_like(luz)
    n = 0
    for dy in range(-radio, radio + 1):
        for dx in range(-radio, radio + 1):
            acumulado += np.roll(np.roll(luz, dy, axis=0), dx, axis=1)
            n += 1
    return acumulado / n


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    limpiar_escena()
    global MAT
    MAT = {nombre: crear_material(nombre, tex, tinte) for nombre, (tex, tinte) in MATERIALES.items()}

    arquitectura = unir(construir(), "CasaLibertad-col")
    print(f"Malla: {len(arquitectura.data.vertices)} vértices, {len(arquitectura.data.polygons)} caras, "
          f"{len(arquitectura.data.materials)} materiales")
    uv_de_luz(arquitectura)

    fondo, sol, velas = preparar_luces()
    configurar_cycles()
    imagen = bpy.data.images.new("horneado", RESOLUCION, RESOLUCION, float_buffer=True)

    # 1) Cielo y velas: luz directa e indirecta (la del cielo no la calcula Godot con oclusión).
    sol.hide_render = True
    cielo_y_velas = hornear(arquitectura, imagen, {"DIRECT", "INDIRECT"})
    # 2) Sol: solo los rebotes; la luz directa y sus sombras las dibuja Godot en tiempo real.
    sol.hide_render = False
    fondo.inputs["Strength"].default_value = 0.0
    for v in velas:
        v.hide_render = True
    rebote_sol = hornear(arquitectura, imagen, {"INDIRECT"})

    luz = suavizar(cielo_y_velas + rebote_sol)
    codificada = np.sqrt(np.clip(luz / RANGO, 0.0, 1.0))
    salida = bpy.data.images.new("luz_horneada", RESOLUCION, RESOLUCION, alpha=False, float_buffer=False)
    salida.colorspace_settings.name = "Non-Color"
    rgba = np.ones((RESOLUCION, RESOLUCION, 4), dtype=np.float32)
    rgba[:, :, :3] = codificada
    salida.pixels = rgba.ravel()
    salida.filepath_raw = str(SALIDA / "luz_horneada.png")
    salida.file_format = "PNG"
    salida.save()
    print(f"Luz horneada: media {luz.mean():.3f}, máxima {luz.max():.3f}")

    for mat in arquitectura.data.materials:
        nodo = mat.node_tree.nodes.get("destino_horneado")
        if nodo:
            mat.node_tree.nodes.remove(nodo)
    bpy.ops.object.select_all(action="DESELECT")
    arquitectura.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(SALIDA / "casa_libertad.glb"),
        use_selection=True,
        export_format="GLB",
        export_materials="EXPORT",
        export_image_format="NONE",
        export_normals=True,
        export_texcoords=True,
        export_apply=True,
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(RAIZ / "blender" / "casa_libertad.blend"))
    print("Listo:", SALIDA / "casa_libertad.glb")


main()
