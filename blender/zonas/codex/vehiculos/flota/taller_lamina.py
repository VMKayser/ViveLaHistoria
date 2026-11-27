"""Operaciones de taller para modelos propios de la flota, en metros."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils.bvhtree import BVHTree

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[4]
sys.path.insert(0, str(RAIZ / ".agents/skills/vehiculo-3d-desde-diseno/scripts"))
from kit_vehiculo_bpy import (
    configurar_estudio_y_renderizar, consolidar_lotes, contorno_redondeado,
    crear_caja, crear_cilindro, crear_malla, crear_superficie_grid, crear_tubo,
    exportar_glb_vehiculo, inicializar_jerarquia, material_pbr, preparar_rig_y_clips,
    validar_geometria_vehiculo,
)


def interpolar(a, b, t):
    return a + (b - a) * t


def intervalo(a, b, segmentos):
    return [interpolar(a, b, i / segmentos) for i in range(segmentos + 1)]


def entre(a, b, t):
    return tuple(interpolar(x, y, t) for x, y in zip(a, b))


def contorno(puntos, radio, entre_esquinas=4):
    esquinas = contorno_redondeado(puntos, radio, 4)
    return [entre(p, esquinas[(i+1) % len(esquinas)], t)
            for i,p in enumerate(esquinas)
            for t in intervalo(0,1,entre_esquinas if i % 5 == 4 else 1)[:-1]]


def rectangulo(u, v, ancho, alto):
    a, b = ancho/2, alto/2
    return [(u-a,v-b),(u+a,v-b),(u+a,v+b),(u-a,v+b)]


class TallerLamina:
    def __init__(self, datos):
        self.d = datos
        self.g = inicializar_jerarquia(datos["id"])
        self.m = {nombre: material_pbr(nombre, *valores)
                  for nombre,valores in datos["paleta"].items()}

    def piel(self, nombre, filas, mat, grupo="carroceria", **opciones):
        return crear_superficie_grid(nombre, filas, self.m[mat], self.g[grupo], **opciones)

    def tubo(self, nombre, puntos, radio, mat, grupo="decoracion", cerrado=False):
        return crear_tubo(nombre, puntos, radio, self.m[mat], self.g[grupo], cerrado, resolucion=0)

    def bloque(self, nombre, posicion, medidas, mat, bisel, grupo="carroceria"):
        return crear_caja(nombre, posicion, medidas, self.m[mat], self.g[grupo], bisel)

    def cilindro(self, nombre, posicion, radio, fondo, mat, eje="Y", grupo="decoracion", lados=24):
        return crear_cilindro(nombre, posicion, radio, fondo, self.m[mat], self.g[grupo], eje=eje, lados=lados)

    def tapa(self, nombre, puntos, mat, grupo, invertido=False):
        indices = tuple(range(len(puntos)))
        return crear_malla(nombre, puntos, [indices[::-1] if invertido else indices],
                           self.m[mat], self.g[grupo])

    def relieve(self, nombre, borde, mapa, mat, fondo, corona=.012, grupo="decoracion", invertido=False):
        centro = [sum(p[i] for p in borde)/len(borde) for i in (0,1)]
        perfil = ((1,fondo-.008),(1,fondo),(.937,fondo+corona*.72),(.73,fondo+corona))
        filas = [[mapa(entre(centro,p,t),d) for t,d in perfil] for p in borde]
        self.piel(nombre, filas, mat, grupo, cerrar_u=True, invertir=invertido)
        self.tapa(nombre + " cara", [f[-1] for f in filas], mat, grupo, invertido)

    def ventana(self, nombre, exterior, hueco, mapa, pintura, marco, invertida=False):
        self.piel("Chapa alrededor de " + nombre,
                  [[mapa(entre(a,b,t),0) for t in intervalo(0,1,5)] for a,b in zip(exterior,hueco)],
                  pintura, cerrar_u=True, invertir=invertida)
        self.tubo("Burlete de " + nombre, [mapa(p,.001) for p in hueco], .011, marco, cerrado=True)
        centro = [sum(p[i] for p in hueco)/len(hueco) for i in (0,1)]
        filas = [[mapa(entre(centro,p,t),-.0045) for t in (.16,.45,.74,1)] for p in hueco]
        self.piel("Hoja de " + nombre, filas, "vidrio", "cristales", cerrar_u=True, invertir=invertida)
        self.tapa("Centro de " + nombre, [f[0] for f in filas], "vidrio", "cristales", invertida)


def verificar_holgura(taller, obstaculos):
    """Comprueba la banda exterior del neumático frente a la piel y sus accesorios."""
    def geometria(objeto):
        evaluado = objeto.evaluated_get(bpy.context.evaluated_depsgraph_get())
        malla = evaluado.to_mesh()
        vertices = [evaluado.matrix_world @ v.co for v in malla.vertices]
        caras = [tuple(p.vertices) for p in malla.polygons]
        arbol = BVHTree.FromPolygons(vertices, caras)
        evaluado.to_mesh_clear()
        return arbol

    barreras = [(obj.name, geometria(obj)) for obj in obstaculos]
    batalla = taller.d["ejes"][1]-taller.d["ejes"][0]
    semivia = taller.d["semivia_ruedas"]
    limite = taller.d["movimiento"]["direccion_maxima"]
    tornamesa = taller.g.get("tornamesa_delantera")
    for delta in intervalo(-limite,limite,40):
        if tornamesa:
            tornamesa.rotation_euler.z = delta
        curvatura = math.tan(delta)/batalla
        for lado,signo in (("izquierda",-1),("derecha",1)):
            direccion = taller.g["direccion_delantera_" + lado]
            if not tornamesa:
                direccion.rotation_euler.z = math.atan2(curvatura*batalla,1+curvatura*semivia*signo)
            bpy.context.view_layer.update()
            rueda = taller.g["rueda_delantera_" + lado]
            neumatico = next(o for o in rueda.children if o.name.startswith("Neumatico radial"))
            arbol = geometria(neumatico)
            roces = [nombre for nombre, malla in barreras if arbol.overlap(malla)]
            if roces:
                raise ValueError(f"Dirección {delta:.3f} rad, rueda {lado}, roces {roces}")
    if tornamesa:
        tornamesa.rotation_euler.z = 0
    for lado in ("izquierda","derecha"):
        taller.g["direccion_delantera_" + lado].rotation_euler.z = 0
    bpy.context.view_layer.update()
    return 41


def ejecutar_modelo(archivo, constructor, args):
    datos = json.loads(archivo.read_text())
    identificador = datos["id"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    escena.unit_settings.system = "METRIC"
    escena.view_settings.view_transform = "AgX"
    escena.view_settings.look = "AgX - Medium High Contrast"
    taller = constructor(datos)
    resultado = taller.construir()
    raiz = taller.g["raiz"]
    movimiento = preparar_rig_y_clips(datos, taller.g)
    bpy.context.view_layer.update()

    revision = RAIZ / "revisiones/codex/flota" / identificador
    publico = RAIZ / "web/public/models/ciudad/codex/vehiculos/flota"
    destino = publico if "--publicar" in args else revision
    revision.mkdir(parents=True, exist_ok=True)
    for pantalla in bpy.data.screens:
        for area in pantalla.areas:
            if area.type == "VIEW_3D":
                vista = area.spaces.active
                vista.region_3d.view_perspective = "CAMERA"
                vista.overlay.show_overlays = False
                vista.shading.color_type = "MATERIAL"

    lamina = RAIZ / "autos" / datos.get("archivo_lamina", f"generadas/{datos['referencia']}_diseno_miciudad.png")
    maestro = destino / (identificador + ".blend")
    configurar_estudio_y_renderizar(raiz,datos,maestro,ruta_referencia=lamina,sin_render=True)
    consolidar_lotes(raiz,("neumatico",),"llanta")
    for obj in escena.objects:
        if obj.parent and obj.type == "MESH":
            obj.data.validate()
    ficha = validar_geometria_vehiculo(raiz,datos,destino / (identificador + ".ficha.json"), {
        "movimiento": movimiento, "referencia": datos["referencia"],
        "normal_goma": {"fuente": "ambientCG Rubber004", "licencia": "CC0 1.0"},
        "clips": ["rodar_adelante","rodar_atras"], **resultado,
    })
    print("FLOTA_VALIDACION", json.dumps(ficha, ensure_ascii=False), flush=True)
    exportar_glb_vehiculo(raiz,destino / (identificador + ".glb"))

    if "--sin-render" in args:
        return
    bpy.ops.wm.open_mainfile(filepath=str(maestro))
    escena = bpy.context.scene
    escena.cycles.samples = 18
    bpy.data.objects["ESTUDIO_suelo_no_exportado"].scale = (7,7,7)
    resoluciones = {"perspectiva":(1100,760),"frente":(810,800),"lateral":(1280,590),
                    "trasera":(810,800),"peaton":(1100,760),"rueda":(850,760)}
    vistas = next((arg.split("=",1)[1].split(",") for arg in args if arg.startswith("--vistas=")), list(resoluciones))
    for vista in vistas:
        escena.camera = bpy.data.objects["ESTUDIO_cam_" + vista]
        escena.camera.data.clip_end = 1350
        escena.render.resolution_x, escena.render.resolution_y = resoluciones[vista]
        escena.render.filepath = str(revision / (vista + ".png"))
        bpy.ops.render.render(write_still=True)
