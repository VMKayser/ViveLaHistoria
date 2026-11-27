"""Segundo pase de los FLOTA: suelda costuras de normales y mide contacto real.
No modifica GLB. Comprueba vértices y centros de caras contra otras islas,
incluyendo apoyos laterales. El auditor común usa un único rayo vertical y
puede marcar un disco que penetra el fuste o un aplique pegado a un muro.
"""
import os,sys,json,math
from collections import defaultdict
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
from kit import datos
raiz=datos.RAIZ
lineas=open(os.path.join(raiz,'revisiones/codex/auditoria.txt')).read().splitlines()
objetivos=defaultdict(set)
for ln in lineas:
 if 'FLOTA' in ln:
  mid,nombre=ln.split('\t')[:2];objetivos[mid].add(nombre)
informe=[]
for mid,nombres in objetivos.items():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=os.path.join(raiz,'web/public/models/ciudad/codex',mid+'.glb'))
 for ob in bpy.data.objects:
  if ob.type!='MESH' or ob.name not in nombres:continue
  bm=bmesh.new();bm.from_mesh(ob.data);bm.transform(ob.matrix_world)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00003)
  bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
  grupos=[];visto=set();vert_grupo={}
  for v0 in bm.verts:
   if v0.index in visto:continue
   pila=[v0];visto.add(v0.index);vs=[]
   while pila:
    v=pila.pop();vs.append(v)
    for e in v.link_edges:
     w=e.other_vert(v)
     if w.index not in visto:visto.add(w.index);pila.append(w)
   i=len(grupos)
   for v in vs:vert_grupo[v.index]=i
   grupos.append(vs)
  coords=[v.co.copy() for v in bm.verts];polys=[[v.index for v in f.verts] for f in bm.faces]
  gcaras=[vert_grupo[f.verts[0].index] for f in bm.faces]
  arbol=BVHTree.FromPolygons(coords,polys)
  for i,vs in enumerate(grupos):
   cx=sum(v.co.x for v in vs)/len(vs);cy=sum(v.co.y for v in vs)/len(vs)
   zmin=min(v.co.z for v in vs);sobre=zmin-datos.altura_suelo(cx,cy)
   if sobre<2.5:continue
   caras={f for v in vs for f in v.link_faces}
   mats=[ob.data.materials[f.material_index].name.split('__')[0] for f in caras]
   if all(m in ('hierro','follaje','follaje_claro') for m in mats):continue
   muestras=[v.co for v in vs[::max(1,len(vs)//20)]]
   fs=sorted(caras,key=lambda f:f.calc_center_median().z)
   muestras += [f.calc_center_median() for f in fs[::max(1,len(fs)//12)]]
   muestras += [Vector((cx,cy,zmin))]
   mejor=.401;vecino=None
   for p in muestras:
    for q,n,j,dist in arbol.find_nearest_range(p,.4):
     if gcaras[j]!=i and dist<mejor:mejor=dist;vecino=gcaras[j]
   if mejor>.085:
    informe.append({'manzana':mid,'objeto':ob.name,'roles':sorted(set(mats)),
     'centro':[round(cx,3),round(cy,3),round(zmin,3)],'alto_sobre_suelo':round(sobre,3),
     'separacion':round(mejor,3),'vertices':len(vs)})
  bm.free()
 print('[contactos]',mid,flush=True)
ruta=os.path.join(raiz,'revisiones/codex/auditoria_D/contactos.json')
json.dump(informe,open(ruta,'w'),ensure_ascii=False,indent=2)
print('[contactos] Sin contacto a menos de 8,5 cm:',len(informe),'→',ruta,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
