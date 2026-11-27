"""M037: cámaras del usuario y recorridos a 1,6 m con contexto exportado.

No modela ni exporta; incluye S_PLAZA25 como contexto de solo lectura.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy

sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from kit import salida
from frentes_codex import frente_de_calle
from detalles_plaza_codex import punto_encadenado
from contexto_codex import instalar_contexto
from render_codex import configurar

m,col=iniciar('codex','M037')
ruta=Path(datos.RAIZ)/'web/public/models/ciudad/codex/M037.glb'
bpy.ops.import_scene.gltf(filepath=str(ruta))
for ob in list(bpy.context.scene.objects):
    for co in list(ob.users_collection):co.objects.unlink(ob)
    col.objects.link(ob)

camaras=[]
for numero in (105,121):
    d=json.loads((Path(datos.RAIZ)/f'coordinacion/revisiones/R{numero:04}/revision.json').read_text())
    p=d['escena']['camara']['lienzo'];q=d['escena']['centro']
    camaras.append((f'R{numero:04}',tuple(p[k] for k in ('x','y','z')),tuple(q[k] for k in ('x','y','z'))))

for eid,calle,normal,tomas in (
    ('E627dd1','Calle José Álvarez de Arenales',(.63,.78),
     [('teatro_portal_pie',51,7,51,3.8),('teatro_longitud_pie',3,1.4,42,3.0)]),
    ('Eeb6abd','Calle Batalla de Junín',(-.78,.63),
     [('junin_pie',25,2.2,43,3.6)]),
):
    _,g=frente_de_calle(edificio('M037',eid),None,calle,normal,0)
    for nombre,s,dist,mirada,alto in tomas:
        p=punto_encadenado(g,s,0,dist);q=punto_encadenado(g,mirada,0,0)
        camaras.append((nombre,(p.x,p.y,altura_suelo(p.x,p.y)+1.6),
                        (q.x,q.y,altura_suelo(q.x,q.y)+alto)))

instalar_contexto([p for _,ojo,mirada in camaras for p in (ojo,mirada)],margen=18)
salida._luz_y_mundo();salida.contexto('M037')
sc=bpy.context.scene;configurar(sc,hilos=2,muestras=16)
sc.render.resolution_x=960;sc.render.resolution_y=720;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='JPEG'
destino=Path(datos.RAIZ)/'revisiones/codex/M037/frentes_20261114';destino.mkdir(exist_ok=True)
for nombre,p,q in camaras:
    if nombre=='R0121':
        sc.render.resolution_x=1280;sc.render.resolution_y=664
    else:sc.render.resolution_x=960;sc.render.resolution_y=720
    cam=salida.camara(p,q,lente=20)
    sc.render.filepath=str(destino/(nombre+'.jpg'));bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True)
registro={'modelo_sha256':hashlib.sha256(ruta.read_bytes()).hexdigest(),
          'camaras':[{'nombre':n,'ojo':p,'mirada':q} for n,p,q in camaras],
          'contexto':json.loads(bpy.data.collections['contexto_local'].get('archivos_glb_json','[]'))}
(destino/'registro.json').write_text(json.dumps(registro,ensure_ascii=False,indent=2)+'\n')
