"""Iteración del Teatro conservando convento, nave y mobiliario de M037."""
import os,sys,hashlib
import bpy
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from teatro_codex import construir_teatro
solo_apoyos='--solo-apoyos' in sys.argv
if solo_apoyos:
    esperado=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--origen-sha='))
    ruta=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex/M037.glb')
    assert hashlib.sha256(open(ruta,'rb').read()).hexdigest()==esperado,'Revisión de origen distinta; no aplicar dos veces'
m,col=iniciar('codex','M037')
bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex/M037.glb'))
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH':continue
    if ob.name=='E627dd1' and not solo_apoyos:
        me=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
        if me.users==0:bpy.data.meshes.remove(me)
    else:
        for cc in list(ob.users_collection):cc.objects.unlink(ob)
        col.objects.link(ob)
if solo_apoyos:
    from mathutils import Vector
    from frentes_codex import frente_de_calle
    f,guia=frente_de_calle(edificio('M037','E627dd1'),None,'Calle José Álvarez de Arenales',(.63,.78),0)
    ob=bpy.data.objects['E627dd1'];l={'a':guia['lados'][0]['a'],'b':guia['lados'][-1]['b'],'normal':tuple(f.n[:2])}
    a=Vector((*l['a'],0));u=(Vector((*l['b'],0))-a).normalized();L=(Vector((*l['b'],0))-a).length
    za,zb=altura_suelo(*l['a']),altura_suelo(*l['b']);normal=Vector((*l['normal'],0))
    letras={i for f in ob.data.polygons if ob.data.materials[f.material_index].name.split('__')[0]=='letrero' for i in f.vertices}
    inversa=ob.matrix_world.inverted()
    for v in ob.data.vertices:
        p=ob.matrix_world@v.co;ss=max(0,min(L,(p-a).dot(u)));q=a+u*ss
        p.z+=za+(zb-za)*ss/L-altura_suelo(q.x,q.y)
        if v.index in letras:p-=normal*.03
        v.co=inversa@p
    ob.data.update()
else:construir_teatro(edificio('M037','E627dd1'),col)
exportar('codex','M037')
