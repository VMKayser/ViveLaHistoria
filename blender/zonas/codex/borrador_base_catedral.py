"""Copia revisable de BASE con la cuadra institucional sin casas automáticas.

NO escribe en rutas de Claude ni en modelos publicados. Salida ignorada:
revisiones/codex/repaso_20261113/BASE_limpia.glb. El dueño de BASE debe
aplicar/publicar la limpieza y conservarla en su generador; propuesta en
propuesta_base_catedral.patch. Se preservan todos los demás objetos.
"""
import os,sys,json,hashlib
import bpy,bmesh
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from piezas_codex import pavimentar
from pavimentos_codex import pavimento_fuera_calles
H=[(-269.16,-214.06),(-356.26,-317.52),(-257.73,-402.35),(-170.52,-301.44)]
origen=os.path.join(datos.RAIZ,'web/public/models/ciudad/claude/BASE.glb')
carpeta=os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113')
destino=os.path.join(carpeta,'BASE_limpia.glb')
sha=hashlib.sha256(open(origen,'rb').read()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=origen)
ob=bpy.data.objects['BASE_relleno'];bm=bmesh.new();bm.from_mesh(ob.data)
retirar=[]
for f in bm.faces:
    p=ob.matrix_world@f.calc_center_median()
    if datos._dentro(p.x,p.y,H):retirar.append(f)
caras_antes=len(bm.faces);n=len(retirar)
bmesh.ops.delete(bm,geom=retirar,context='FACES')
bm.to_mesh(ob.data);bm.free();ob.data.update()
col=bpy.data.collections.new('borrador_limpieza_institucional');bpy.context.scene.collection.children.link(col)
c=Constructor('BASE_suelo_conjunto_institucional')
for h in pavimento_fuera_calles(H,datos.calles_reales(),hasta_calzada=True):
    pavimentar(c,h,'adoquin',offset=.13,paso=3,color='#c9c0aa')
c.objeto(col)
assert hashlib.sha256(open(origen,'rb').read()).hexdigest()==sha,'BASE cambió durante la lectura; repetir el borrador'
bpy.ops.export_scene.gltf(filepath=destino,export_format='GLB',export_yup=True,
                          export_apply=True,export_normals=True,export_materials='EXPORT')
json.dump({'solo_borrador':True,'origen':origen,'sha256_origen':sha,
           'salida':destino,'poligono':H,'caras_relleno_antes':caras_antes,
           'caras_retiradas':n,'suelo_offset_m':.13,
           'nota':'No publicado; requiere actualización por el dueño de BASE'},
          open(destino+'.json','w'),indent=2,ensure_ascii=False)
print('[BASE borrador]',n,'caras retiradas; publicada intacta →',destino,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
