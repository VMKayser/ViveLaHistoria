"""Grafo de contacto del ramaje: cada rama debe llegar a una raíz apoyada.

Solo lectura. Suelda costuras del GLB y comprueba intersecciones entre
superficies leñosas. Complementa calidad.py; no sustituye su control.
"""
import json,os,sys
from pathlib import Path
import bpy,bmesh
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from kit import datos


def auditar(mid):
    raiz=Path(datos.RAIZ);bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(raiz/'web/public/models/ciudad/codex'/(mid+'.glb')))
    resultado=[]
    for ob in bpy.data.objects:
        if ob.type!='MESH' or 'arbol' not in ob.name.lower():continue
        bm=bmesh.new();bm.from_mesh(ob.data);bm.transform(ob.matrix_world)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00003)
        bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
        madera={i for i,m in enumerate(ob.data.materials) if m and m.name.split('__')[0]=='tronco'}
        pendientes={f for f in bm.faces if f.material_index in madera};grupos=[]
        while pendientes:
            pila=[pendientes.pop()];caras=[]
            while pila:
                f=pila.pop();caras.append(f)
                for v in f.verts:
                    for otro in v.link_faces:
                        if otro in pendientes:pendientes.remove(otro);pila.append(otro)
            vs=list({v for f in caras for v in f.verts});indices={v:i for i,v in enumerate(vs)}
            coords=[v.co.copy() for v in vs]
            arbol=BVHTree.FromPolygons(coords,[[indices[v] for v in f.verts] for f in caras],epsilon=.00001)
            apoyo=any(v.z-datos.altura_suelo(v.x,v.y)<=.3 for v in coords)
            grupos.append((coords,arbol,apoyo))
        grafo=[set() for g in grupos]
        for i,(vs,a,_) in enumerate(grupos):
            for j in range(i):
                ws,b,_=grupos[j]
                contacto=bool(a.overlap(b))
                if not contacto:
                    contacto=any((r:=b.find_nearest(p,.003))[0] is not None for p in vs)
                if contacto:grafo[i].add(j);grafo[j].add(i)
        vistos={i for i,g in enumerate(grupos) if g[2]};pila=list(vistos)
        while pila:
            for vecino in grafo[pila.pop()]-vistos:vistos.add(vecino);pila.append(vecino)
        sin_raiz=[]
        for i,(vs,_,_) in enumerate(grupos):
            if i in vistos:continue
            p=sum(vs,vs[0]*0)/len(vs);sin_raiz.append([round(v,4) for v in p])
        resultado.append({'objeto':ob.name,'componentes_lenosos':len(grupos),'conectados_a_raiz':len(vistos),'sin_raiz':sin_raiz})
        bm.free()
    dest=raiz/'revisiones/codex/limpieza_20261113'/(mid+'_ramaje.json')
    dest.write_text(json.dumps(resultado,ensure_ascii=False,indent=2))
    print('[ramaje]',len(resultado),'árboles;',sum(len(r['sin_raiz']) for r in resultado),'ramas sin conexión al suelo',flush=True)
    return resultado


if __name__=='__main__':
    mid=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--mid=')),'M061')
    auditar(mid)
