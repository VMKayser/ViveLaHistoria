"""Contexto de revisión acotado; nunca escribe modelos de otro agente.

Selecciona por huellas y recorta en memoria las mallas importadas. BASE se
importa una sola vez. No modifica la colección que se está revisando.
"""
import os
import json
import math
import bpy
import numpy as np
from kit import datos, salida, Constructor
from contexto_glb_codex import recortar_glb


def instalar_contexto(puntos, margen=28, base_alternativa=None, solo_terreno=False):
    puntos=list(puntos)
    assert puntos
    limites=(min(p[0] for p in puntos)-margen,min(p[1] for p in puntos)-margen,
             max(p[0] for p in puntos)+margen,max(p[1] for p in puntos)+margen)

    def intersecta(h):
        return bool(h) and not (max(p[0] for p in h)<limites[0] or min(p[0] for p in h)>limites[2]
                               or max(p[1] for p in h)<limites[1] or min(p[1] for p in h)>limites[3])

    def recortar(ob):
        if ob.type!='MESH':return True
        if not intersecta([(ob.matrix_world@__import__('mathutils').Vector(p))[:2] for p in ob.bound_box]):
            me=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
            if not me.users:bpy.data.meshes.remove(me)
            return False
        me=ob.data
        v=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',v);v=v.reshape(-1,3)
        matriz=np.array(ob.matrix_world,dtype=np.float32)
        mundo=v@matriz[:3,:3].T+matriz[:3,3]
        # Los GLB son triangulados; ningún contexto se reexporta.
        assert all(p.loop_total==3 for p in me.polygons)
        indices=np.empty(len(me.loops),dtype=np.int32);me.loops.foreach_get('vertex_index',indices);indices=indices.reshape(-1,3)
        xy=mundo[indices,:2];lo=xy.min(axis=1);hi=xy.max(axis=1)
        usar=(hi[:,0]>=limites[0])&(lo[:,0]<=limites[2])&(hi[:,1]>=limites[1])&(lo[:,1]<=limites[3])
        if usar.all():return True
        if not usar.any():
            bpy.data.objects.remove(ob,do_unlink=True)
            if not me.users:bpy.data.meshes.remove(me)
            return False
        caras=indices[usar];vertices,rev=np.unique(caras,return_inverse=True)
        nuevo=bpy.data.meshes.new(me.name+'_local')
        nuevo.from_pydata(v[vertices].tolist(),[],rev.reshape(-1,3).tolist())
        for m in me.materials:nuevo.materials.append(m)
        materiales=np.empty(len(me.polygons),dtype=np.int32);me.polygons.foreach_get('material_index',materiales)
        nuevo.polygons.foreach_set('material_index',materiales[usar])
        suaves=np.empty(len(me.polygons),dtype=bool);me.polygons.foreach_get('use_smooth',suaves)
        nuevo.polygons.foreach_set('use_smooth',suaves[usar])
        ob.data=nuevo
        if not me.users:bpy.data.meshes.remove(me)
        return True

    def contexto(mid):
        col=bpy.data.collections.new('contexto_local');bpy.context.scene.collection.children.link(col)
        c=Constructor('terreno_contexto_local')
        for x in range(math.floor(limites[0]/5)*5,math.ceil(limites[2]/5)*5,5):
            for y in range(math.floor(limites[1]/5)*5,math.ceil(limites[3]/5)*5,5):
                c.poligono([(a,b,datos.altura_suelo(a,b)-.35) for a,b in ((x,y),(x+5,y),(x+5,y+5),(x,y+5))],'calzada')
        c.objeto(col)
        rutas=[]
        for m in ([] if solo_terreno else datos.reparto()['manzanas']+datos.reparto()['espacios']):
            if m['id']==mid:continue
            if m['id']=='BASE':
                ruta=base_alternativa or os.path.join(salida.dir_modelos(m['dueno']),'BASE.glb')
            else:
                huella=m.get('huella',[]) or m.get('poligono',[])
                if not huella:huella=[p for e in m.get('edificios',[]) for p in e['huella']]
                if not intersecta(huella):continue
                ruta=os.path.join(salida.dir_modelos(m['dueno']),m['id']+'.glb')
            if not os.path.exists(ruta):
                # Durante un traspaso el GLB anterior sigue siendo contexto
                # de lectura hasta que su nuevo dueño publique el sustituto.
                anterior=os.path.join(salida.dir_modelos('codex'),'M055.glb')
                if m['id']=='M055' and os.path.exists(anterior):ruta=anterior
                else:continue
            copia=recortar_glb(ruta,limites,os.path.join(datos.RAIZ,'revisiones/codex/contexto_cache'))
            antes=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=copia)
            for ob in set(bpy.data.objects)-antes:
                if not recortar(ob):continue
                for cc in list(ob.users_collection):cc.objects.unlink(ob)
                col.objects.link(ob)
            rutas.append(ruta)
        col['archivos_glb_json']=json.dumps(rutas)
        print('[contexto local]',limites,'GLB:',','.join(os.path.basename(p) for p in rutas),flush=True)
    salida.contexto=contexto
    return limites
