"""Inicio de escena, exportación a GLB y renders de revisión (render junto a la foto real)."""

import glob
import json
import math
import os
import time

import bpy
from mathutils import Vector

from . import datos, paleta
from .nucleo import Constructor

RAIZ = datos.RAIZ


def dir_modelos(agente):
    return os.path.join(RAIZ, "web", "public", "models", "ciudad", agente)


def dir_revision(agente, mid):
    return os.path.join(RAIZ, "revisiones", agente, mid)


def iniciar(agente, mid):
    """Verifica que el agente sea dueño de la manzana, limpia la escena y crea la colección de trabajo."""
    m = datos.verificar_dueno(agente, mid)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new(mid)
    bpy.context.scene.collection.children.link(col)
    print(f"[kit] {agente} modela {mid}: {len(m['edificios'])} edificios, {len(m['fotos'])} fotos")
    return m, col


def exportar(agente, mid, col=None):
    """Exporta la colección de la manzana a web/public/models/ciudad/<agente>/<mid>.glb y actualiza el manifiesto del agente."""
    datos.verificar_dueno(agente, mid)
    col = col or bpy.data.collections[mid]
    # control de calidad: cada edificio dentro de su huella (sin invadir al vecino); ver kit/medianeras.py
    from . import medianeras
    n = medianeras.limpiar(col, mid)
    if n:
        print(f"[kit] {n} objetos recortados a sus medianeras")
    os.makedirs(dir_modelos(agente), exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(o.name in col.all_objects)
    ruta = os.path.join(dir_modelos(agente), f"{mid}.glb")
    bpy.ops.export_scene.gltf(filepath=ruta, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_normals=True, export_materials="EXPORT")
    deps = bpy.context.evaluated_depsgraph_get()
    tris = sum(len(o.evaluated_get(deps).data.loop_triangles) for o in col.all_objects if o.type == "MESH")
    man_ruta = os.path.join(dir_modelos(agente), "manifiesto.json")
    man = json.load(open(man_ruta)) if os.path.exists(man_ruta) else {}
    man[mid] = {"archivo": f"{mid}.glb", "triangulos": tris, "objetos": len(col.all_objects),
                "actualizado": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(man_ruta, "w") as fh:
        json.dump(dict(sorted(man.items())), fh, indent=1)
    print(f"[kit] exportado {ruta} ({tris} triángulos)")
    return ruta


# --------------------------------------------------------------------------- revisión visual


def _luz_y_mundo():
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    w = bpy.data.worlds.new("cielo")
    w.use_nodes = True
    fondo = w.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = paleta.hex_a_rgba("#8fc0ea")
    fondo.inputs["Strength"].default_value = 0.9
    sc.world = w
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 3.4
    sol.color = paleta.hex_a_rgba("#fff0d8")[:3]
    sol.angle = math.radians(3)
    ob = bpy.data.objects.new("sol", sol)
    ob.rotation_euler = (math.radians(50), 0, math.radians(-35))  # sol de tarde, desde el NO
    sc.collection.objects.link(ob)


def contexto(mid, radio=140):
    """Agrega alrededor: suelo, volúmenes grises de los edificios vecinos del lienzo y los GLB ya exportados por ambos agentes."""
    m = datos.manzana(mid)
    cx, cy = m["centro"]
    col = bpy.data.collections.new("contexto")
    bpy.context.scene.collection.children.link(col)
    # suelo con la pendiente del terreno
    c = Constructor("suelo")
    paso = 5.0
    for i in range(-int(radio / paso), int(radio / paso)):
        for j in range(-int(radio / paso), int(radio / paso)):
            x0, y0 = cx + i * paso, cy + j * paso
            pts = [(x0, y0), (x0 + paso, y0), (x0 + paso, y0 + paso), (x0, y0 + paso)]
            c.poligono([(x, y, datos.altura_suelo(x, y) - 0.05) for x, y in pts], "calzada")
    c.objeto(col)
    # modelos ya exportados (de los dos agentes), menos esta manzana
    hechos = set()
    rutas = glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "M*.glb"))
    rutas += glob.glob(os.path.join(RAIZ, "web", "public", "models", "ciudad", "*", "BASE*.glb"))
    for ruta in rutas:
        otro = os.path.splitext(os.path.basename(ruta))[0]
        if otro == mid:
            continue
        if otro.startswith("BASE"):
            # calzada, veredas y mobiliario: se cargan siempre (el suelo gris de arriba queda debajo)
            antes = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=ruta)
            for o in set(bpy.data.objects) - antes:
                for cc in o.users_collection:
                    cc.objects.unlink(o)
                col.objects.link(o)
            continue
        try:
            om = datos.manzana(otro)
        except KeyError:
            continue
        if math.hypot(om["centro"][0] - cx, om["centro"][1] - cy) > radio + 60:
            continue
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=ruta)
        for o in set(bpy.data.objects) - antes:
            for cc in o.users_collection:
                cc.objects.unlink(o)
            col.objects.link(o)
        hechos.update(e["id"] for e in om["edificios"])
    # volúmenes del lienzo para lo que nadie modeló todavía
    propios = {e["id"] for e in m["edificios"]}
    todos = {e["id"]: e for mm in datos.reparto()["manzanas"] for e in mm["edificios"]}
    v = Constructor("vecinos_lienzo")
    for eid, e in todos.items():
        if eid in propios or eid in hechos:
            continue
        if math.hypot(e["centro"][0] - cx, e["centro"][1] - cy) > radio:
            continue
        h = datos.recortar_a_calles(e.get("huella_lienzo", e["huella"]))
        if not h:
            continue
        zb = min(datos.altura_suelo(x, y) for x, y in h) - 0.5
        v.prisma(h, zb, zb + 0.5 + min(e["altura_lienzo"], 9), "muro", "#c9c3bb")
    v.objeto(col)


def _punto_calle_real(x, y, radio=16.0):
    """((x, y) del eje más cercano, medio ancho, distancia) de la calle real más próxima, o None."""
    mejor = None
    for c in datos.calles_reales():
        for a, b in zip(c["eje"], c["eje"][1:]):
            d, q = datos._dist_seg(x, y, a, b)
            if d < radio and (mejor is None or d < mejor[2]):
                mejor = (q, c["ancho"] / 2, d)
    return mejor


def camara_desde_foto(archivo, lente=24, altura_ojo=1.6, mirar_altura=4.5, distancia=22.0):
    """Cámara aproximada de frente a lo fotografiado, para comparar con la foto.

    El punto de la foto (ubicaciones.json) marca DÓNDE ESTÁ LO FOTOGRAFIADO. La cámara sale desde ese
    punto hacia la calle más cercana (perpendicular a la fachada) y retrocede hasta 'distancia' metros
    o hasta toparse con otro edificio. No usa el GPS del EXIF (tiene 5–20 m de error).
    Si el encuadre no se parece a la foto, pon la cámara a mano con camara(pos, mirar).
    """
    u = datos.ubicaciones()[archivo]
    base = Vector((u["x"], u["y"], 0))
    obj = Vector((u["x"], u["y"], datos.altura_suelo(u["x"], u["y"]) + mirar_altura))
    # con calles de ancho real: la cámara va en la vereda de ENFRENTE, mirando al objeto (como se sacan las fotos)
    real = _punto_calle_real(u["x"], u["y"])
    if real is not None:
        (qx, qy), w, d = real
        direc = Vector((qx - u["x"], qy - u["y"], 0))
        if direc.length < 0.3:
            direc = Vector((0, -1, 0))
        direc.normalize()
        pos = Vector((qx, qy, 0)) + direc * max(0.0, w - 1.2)
        if datos.dentro_de_edificio(pos.x, pos.y):
            pos = Vector((qx, qy, 0))
        pos.z = datos.altura_suelo(pos.x, pos.y) + altura_ojo
        return camara(pos, obj, min(lente, 16))
    _, q, _ = datos.calle_cercana(u["x"], u["y"])
    direc = Vector((q[0], q[1], 0)) - base
    if direc.length < 0.5:
        direc = Vector((0, -1, 0))
    direc.normalize()
    pos = Vector((q[0], q[1], 0))
    paso = 1.0
    while (pos - base).length < distancia:
        sig = pos + direc * paso
        if datos.dentro_de_edificio(sig.x, sig.y):
            break
        pos = sig
    pos -= direc * 0.5 if (pos - base).length > 4 else Vector()
    pos.z = datos.altura_suelo(pos.x, pos.y) + altura_ojo
    return camara(pos, obj, lente)


def camara(pos, mirar, lente=24):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lente
    cam.sensor_width = 36
    cam.clip_end = 3000
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(pos)
    ob.rotation_euler = (Vector(mirar) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


def revisar(agente, mid, fotos=None, ancho=1200, alto=900, camaras_extra=()):
    """Renderiza la manzana con contexto desde cada foto y arma comparaciones render | foto real.

    fotos: lista de archivos (por defecto todas las fotos de la manzana).
    camaras_extra: [(nombre, (x,y,z) posición, (x,y,z) mirar)] para vistas libres (p. ej. vista aérea).
    Salida: revisiones/<agente>/<mid>/render_<foto>.jpg y vista_<nombre>.jpg.
    Luego, fuera de Blender: python3 scripts/comparar.py <agente> <mid>  -> comparacion_<foto>.jpg (render | foto)
    """
    datos.verificar_dueno(agente, mid)
    import sys
    if "--sin-render" in sys.argv:
        print("[kit] --sin-render: no se renderiza")
        return []
    m = datos.manzana(mid)
    _luz_y_mundo()
    contexto(mid)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = ancho, alto
    sc.render.image_settings.file_format = "JPEG"
    salida = dir_revision(agente, mid)
    os.makedirs(salida, exist_ok=True)
    hechas = []
    for archivo in (fotos if fotos is not None else m["fotos"]):
        camara_desde_foto(archivo)
        ruta = os.path.join(salida, f"render_{os.path.splitext(archivo)[0]}.jpg")
        sc.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        hechas.append((ruta, datos.ruta_foto(archivo)))
    for nombre, pos, mirar in camaras_extra:
        camara(pos, mirar)
        ruta = os.path.join(salida, f"vista_{nombre}.jpg")
        sc.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
    print(f"[kit] renders en {salida}")
    return hechas
