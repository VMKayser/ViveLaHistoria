"""Revisión de holguras y apoyos con los maestros Blender ya generados."""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

CARPETA = Path(__file__).resolve().parent


def arbol(objetos):
    vertices, caras = [], []
    for o in objetos:
        inicio = len(vertices)
        vertices.extend(o.matrix_world @ v.co for v in o.data.vertices)
        caras.extend(tuple(inicio+i for i in f.vertices) for f in o.data.polygons)
    return BVHTree.FromPolygons(vertices,caras,all_triangles=True)


def holguras():
    eje = bpy.data.objects["tornamesa_delantera"]
    carcasa = arbol([o for n in ("carroceria","interior","decoracion","cristales")
                     for o in bpy.data.objects[n].children if o.type=="MESH"])
    ruedas = [bpy.data.objects[f"rueda_delantera_{lado}"].children for lado in ("izquierda","derecha")]
    maximo = eje.parent["movimiento"]["direccion_maxima"]
    choques = []
    for angulo in np.linspace(-maximo,maximo,41):
        eje.rotation_euler.z = angulo
        bpy.context.view_layer.update()
        for lado,rueda in zip(("izquierda","derecha"),ruedas):
            n = len(carcasa.overlap(arbol(rueda)))
            if n:
                choques.append([lado,round(math.degrees(angulo),2),n])
    eje.rotation_euler.z = 0
    return {"posiciones_comprobadas":41,"intersecciones_rueda_caja":choques}


def cascos():
    datos = json.loads((CARPETA/"caballo.json").read_text())
    escena = bpy.context.scene
    rig = bpy.data.objects["Esqueleto equino"]
    malla = bpy.data.objects["Pelaje modelado del caballo"]
    indices = {}
    for nombre in datos["patas"]:
        id_grupo = malla.vertex_groups[f"{nombre}_casco"].index
        indices[nombre] = [v.index for v in malla.data.vertices
                           if any(g.group==id_grupo and g.weight>.57 for g in v.groups)]
    coords = np.zeros(len(malla.data.vertices)*3,dtype=np.float32)
    informe = {}
    for nombre,ciclo in datos["clips"].items():
        for pista in rig.animation_data.nla_tracks:
            pista.is_solo = pista.name==nombre
        rig.animation_data.nla_tracks[nombre].is_solo = True
        todos, apoyos = [], []
        for frame in range(ciclo["fotogramas"]+1):
            escena.frame_set(frame+1)
            deforme = malla.evaluated_get(bpy.context.evaluated_depsgraph_get())
            deforme.data.vertices.foreach_get("co",coords)
            z = coords.reshape((-1,3))[:,2]
            for pata,ids in indices.items():
                fase = (frame/ciclo["fotogramas"]+datos["patas"][pata][ciclo["desfase"]]) % 1
                minimo = float(z[ids].min())
                todos.append(minimo)
                if fase<ciclo["apoyo"]:
                    apoyos.append(minimo)
        informe[nombre] = {
            "casco_mas_bajo_m": round(min(todos),5),
            "apoyo_mas_alto_m": round(max(apoyos),5),
            "apoyos_muestreados":len(apoyos),
        }
    for pista in rig.animation_data.nla_tracks:
        pista.is_solo = False
    escena.frame_set(1)
    return informe


def revisar(ruta):
    cli = argparse.ArgumentParser()
    cli.add_argument("modelo")
    cli.add_argument("salida",type=Path)
    args = cli.parse_args(ruta)
    es_caballo = args.modelo=="caballo_castano"
    informe = cascos() if es_caballo else holguras()
    args.salida.mkdir(parents=True,exist_ok=True)
    (args.salida/"geometria.json").write_text(json.dumps(informe,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(informe,ensure_ascii=False),flush=True)
    if es_caballo:
        for clip in informe.values():
            assert clip["casco_mas_bajo_m"] >= -.017
            assert clip["apoyo_mas_alto_m"] <= .021
    else:
        assert not informe["intersecciones_rueda_caja"]


if __name__=="__main__":
    revisar(sys.argv[sys.argv.index("--")+1:])
