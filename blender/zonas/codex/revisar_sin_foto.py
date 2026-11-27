"""Una vista de cada manzana sin foto; modelos vecinos y BASE como contexto."""
import os
import sys
import math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
import bpy
from kit import *
from kit import salida
m,col=iniciar('codex','M074')
antes=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(salida.dir_modelos('codex'),'M074.glb'))
for ob in set(bpy.data.objects)-antes:
    for cc in list(ob.users_collection):cc.objects.unlink(ob)
    col.objects.link(ob)
salida._luz_y_mundo()
salida.contexto('M074',radio=650)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU'
sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.threads_mode='FIXED';sc.render.threads=8
sc.render.resolution_x=640;sc.render.resolution_y=480;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='JPEG'
EXCLUIDAS={'M055','M037','M061','M056','M027','M063'}
for dato in datos.reparto()['manzanas']:
    mid=dato['id']
    if dato['dueno']!='codex' or mid in EXCLUIDAS:continue
    if '--corregir-camaras' in sys.argv and mid not in ('M049','M050','M060'):continue
    datos.verificar_dueno('codex',mid)
    mm=datos.manzana(mid);cx,cy=mm['centro'];z=altura_suelo(cx,cy)+3
    pts=[p for e in mm['edificios'] for p in e['huella']]
    frente=None
    if '--frentes' in sys.argv:
        candidatos=[l for e in mm['edificios'] for l in lados(e['huella']) if l['a_calle'] and l['largo']>=2]
        if not candidatos:continue
        frente=max(candidatos,key=lambda l:l['largo'])
    radio=max([math.hypot(x-cx,y-cy) for x,y in pts]+[9])
    distancia=max(22,radio*1.8)
    if frente:
        x,y=(frente['a'][0]+frente['b'][0])/2,(frente['a'][1]+frente['b'][1])/2
        nx,ny=frente['normal'];zz=altura_suelo(x,y)
        distancia=next((dd for dd in (16,12,10,8,6,4,2)
                        if not datos.dentro_de_edificio(x+nx*dd,y+ny*dd)),8)
        ob=camara((x+nx*distancia,y+ny*distancia,zz+7),(x,y,zz+3.5),lente=24)
    else:ob=camara((cx+distancia*.65,cy-distancia*.75,z+distancia*.8),(cx,cy,z),lente=38)
    carpeta=salida.dir_revision('codex',mid);os.makedirs(carpeta,exist_ok=True)
    sc.render.filepath=os.path.join(carpeta,'vista_frente.jpg' if frente else 'vista_general.jpg')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ob,do_unlink=True)
    print('[codex] revisada',mid,flush=True)
