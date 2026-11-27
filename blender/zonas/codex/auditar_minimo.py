"""Comprueba en los GLB el mínimo geométrico de las casas declaradas sin foto.
Complementa el recorrido: una cuenta de triángulos no demuestra parecido.
No se inventan fachadas en el cuerpo posterior del museo M063.
"""
import json,struct,sys
from pathlib import Path
raiz=Path(__file__).resolve().parents[3]
fuentes=raiz/'blender/zonas/codex';modelos=raiz/'web/public/models/ciudad/codex'
ids=[p.stem for p in fuentes.glob('M*.py') if 'from generica import construir' in p.read_text()]
reparto=json.loads((raiz/'reparto/manzanas.json').read_text())
por_id={m['id']:m for m in reparto['manzanas']}
for mid in ('M037','M061','M058','M059','M064','M065'):ids.append(mid)
solicitadas={a.split('=',1)[1] for a in sys.argv if a.startswith('--mid=')}
if solicitadas:ids=[mid for mid in ids if mid in solicitadas]
resultado=[]
for mid in sorted(ids):
    if por_id[mid]['dueno']!='codex':continue
    data=(modelos/(mid+'.glb')).read_bytes();n=struct.unpack_from('<I',data,12)[0]
    gltf=json.loads(data[20:20+n]);mats=gltf['materials']
    originales={e['id'] for e in por_id[mid]['edificios']}
    # E749b6b: casa genérica retirada por el usuario; ahora patio institucional.
    excepciones={'M064':{'Ed8b92f'},'M055':{'E03fe1d','E2c6601','Eae1b1b','E749b6b'},
                 'M037':{'E627dd1','Ee30c62','Eeb6abd','E1aa79c'},'M061':{'E311863','E02ae75','E00e8b2'}}
    originales-=excepciones.get(mid,set())
    for mesh in gltf['meshes']:
        if mesh['name'] not in originales:continue
        # El cuerpo cerrado y la carpintería siguen siendo un mismo edificio.
        partes=[m for m in gltf['meshes'] if m['name'] in (mesh['name'],mesh['name']+'_detalles')]
        prims=[p for m in partes for p in m['primitives']]
        roles={mats[p['material']]['name'].split('__')[0] for p in prims}
        tris=sum(gltf['accessors'][p['indices']]['count']//3 for p in prims)
        requeridos={'muro','zocalo_piedra','vidrio','marco_ventana','hierro','teja'}
        assert requeridos<=roles,(mid,mesh['name'],'Faltan roles',requeridos-roles)
        assert roles&{'madera','metal'},(mid,mesh['name'],'Sin portón/carpintería')
        assert tris>=250,(mid,mesh['name'],'Detalle insuficiente',tris)
        resultado.append({'manzana':mid,'edificio':mesh['name'],'triangulos':tris,'roles':sorted(roles)})
ruta=raiz/'revisiones/codex/calidad_E/minimo.json'
ruta.write_text(json.dumps({'casas':len(resultado),'manzanas':len(ids),'resultado':'correcto','detalle':resultado},ensure_ascii=False,indent=2))
print(f'{len(resultado)} casas en {len(ids)} manzanas: roles del mínimo y más de 250 triángulos; falta/presencia visual se coteja en el recorrido.')
