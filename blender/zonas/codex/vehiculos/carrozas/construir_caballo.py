"""Caballo de tiro editable y GLB con cuatro acciones de esqueleto."""
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from construir import AQUI, FUENTES, PUBLICO, exportar, guardar_estudio
from caballo_malla import accesorios, acabado, pesos, reconstruir
from caballo_rig import animar, armar, cadenas
from kit_vehiculo_bpy import crear_vacio


def construir():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    datos = json.loads((AQUI/"caballo.json").read_text())
    raiz = crear_vacio(datos["id"])
    raiz["unidades"] = "metros"
    raiz["frente_blender"] = "+X"
    raiz["origen"] = "suelo, centro del caballo"
    raiz["clips"] = datos["clips"]
    malla = reconstruir(FUENTES/datos["fuente"],datos,raiz)
    patas = cadenas(datos)
    acabado(malla,patas)
    puntos = {k:tuple(Vector(p) for p in v) for k,v in datos["articulaciones"].items()}
    rig = armar(raiz,malla,puntos,patas)
    pesos(malla,patas,puntos)
    accesorios(raiz,rig)
    informe = animar(rig,patas,datos["clips"])
    print("Clips y geometría",informe,len(malla.data.vertices),len(malla.data.polygons),flush=True)
    mallas = [o for o in raiz.children_recursive if o.type=="MESH"]
    for pieza in mallas:
        pieza.data.calc_loop_triangles()
    ficha = {
        "id": datos["id"], "nombre": datos["nombre"], "articulaciones": len(rig.data.bones),
        "triangulos": sum(len(o.data.loop_triangles) for o in mallas), "mallas": len(mallas),
        "vertices_pelaje": len(malla.data.vertices), "triangulos_pelaje": len(malla.data.polygons),
        "clips": informe, "textura": "Albedo pictórico lineal por vértice",
        "fuente": "Geometría reparada a partir de autos/carrozas/horse.glb",
        "tiros": ["tiro_caballo_derecha","tiro_caballo_izquierda"],
    }
    (PUBLICO/f"{datos['id']}.ficha.json").write_text(json.dumps(ficha,indent=2,ensure_ascii=False)+"\n")
    glb = PUBLICO/f"{datos['id']}.glb"
    exportar(raiz,glb)
    raiz_de_piel(glb)
    estudio = dict(largo=2.60,ancho=.64,alto=1.83,ejes=(-.52,.52),semivia_ruedas=.22,radio_rueda=.21)
    guardar_estudio(raiz,estudio,PUBLICO/f"{datos['id']}.blend")



def raiz_de_piel(ruta):
    """En glTF la piel comparte raíz de escena con su armadura. Mover la escena completa."""
    contenido = ruta.read_bytes()
    longitud = struct.unpack_from("<I",contenido,12)[0]
    doc = json.loads(contenido[20:20+longitud])
    pieles = [j for j,n in enumerate(doc["nodes"]) if "skin" in n]
    assert len(pieles)==1
    piel = pieles[0]
    escena = doc["scenes"][doc["scene"]]
    for n in doc["nodes"]:
        if piel in n.get("children",[]):
            n["children"].remove(piel)
    escena["nodes"].append(piel)
    bloque = json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
    bloque += b" "*(-len(bloque)%4)
    binario = contenido[20+longitud:]
    cabecera = struct.pack("<4sIIII",b"glTF",2,20+len(bloque)+len(binario),len(bloque),0x4E4F534A)
    ruta.write_bytes(cabecera+bloque+binario)


if __name__=="__main__":
    construir()
