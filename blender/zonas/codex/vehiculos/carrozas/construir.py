"""Genera maestros y GLB de las carrozas en su espacio independiente."""
import argparse
import importlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[4]
FUENTES = REPO / "autos/carrozas"
PUBLICO = REPO / "web/public/models/ciudad/codex/vehiculos/carrozas"
MODELOS = ("carroza_azul", "carruaje_madera")
sys.path[:0] = [str(AQUI), str(REPO / ".agents/skills/vehiculo-3d-desde-diseno/scripts")]

from kit_vehiculo_bpy import (consolidar_lotes, configurar_estudio_y_renderizar,
    inicializar_jerarquia, preparar_rig_y_clips, seleccionar_jerarquia,
    validar_geometria_vehiculo)
from piezas import materiales, ruedas_y_bastidor


def exportar(raiz, ruta):
    ruta.parent.mkdir(parents=True,exist_ok=True)
    seleccionar_jerarquia(raiz)
    bpy.ops.export_scene.gltf(
        filepath=str(ruta),export_format="GLB",use_selection=True,export_extras=True,
        export_animation_mode="NLA_TRACKS",export_force_sampling=True,export_frame_range=False,
        export_anim_slide_to_zero=True,export_yup=True,export_cameras=False,export_lights=False,
    )


def construir(id_carroza):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    datos = json.loads((AQUI / f"{id_carroza}.json").read_text())
    grupos = inicializar_jerarquia(id_carroza)
    paleta = materiales(datos)
    importlib.import_module(id_carroza).construir(grupos, paleta)
    ruedas_y_bastidor(datos, grupos, paleta)
    raiz = grupos["raiz"]
    conservar_uv = (paleta["roble"].name,) if "roble" in paleta else ()
    consolidar_lotes(raiz, conservar_uv)
    config = preparar_rig_y_clips(datos, grupos)
    config["radios_ruedas"] = datos["radios_ruedas"]
    config["enganche"] = datos["enganche"]
    raiz["movimiento"] = config
    raiz["animacion"] = "Tornamesa delantera y giro por distancia con radios por eje"
    ficha = PUBLICO / f"{id_carroza}.ficha.json"
    extensiones = bpy.data.objects["varas_caballo"].children_recursive
    esquinas = [o.matrix_world @ Vector(c) for o in raiz.children_recursive
                if o.type == "MESH" and o not in extensiones for c in o.bound_box]
    medidas = [round(max(p[j] for p in esquinas)-min(p[j] for p in esquinas),4) for j in range(3)]
    validar_geometria_vehiculo(raiz, datos, ficha, {
        "dimensiones_sin_varas_m": medidas,
        "movimiento": config,
        "clips": ["rodar_adelante", "rodar_atras"],
        "varas": "Ocultar el nodo completo varas_caballo para inspeccionar sin caballo",
    })
    exportar(raiz, PUBLICO / f"{id_carroza}.glb")
    guardar_estudio(raiz,datos,PUBLICO/f"{id_carroza}.blend",FUENTES/datos["referencia"])


def guardar_estudio(raiz,datos,ruta,referencia=None):
    configurar_estudio_y_renderizar(raiz,datos,ruta,ruta_referencia=referencia,sin_render=True)
    alto = datos["alto"]
    for nombre,escala in (("lateral",2.11),("frente",1.23),("trasera",1.23)):
        camara = bpy.data.objects[f"ESTUDIO_cam_{nombre}"].data
        camara.ortho_scale = max(camara.ortho_scale,alto*escala)
    bpy.ops.wm.save_as_mainfile(filepath=str(ruta))


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("modelos", nargs="*", metavar="MODELO")
    args = cli.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    for modelo in args.modelos or MODELOS:
        if modelo not in MODELOS:
            cli.error(f"Modelo desconocido: {modelo}")
        construir(modelo)
