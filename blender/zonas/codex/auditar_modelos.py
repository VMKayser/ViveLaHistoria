"""Comprueba cobertura, integridad GLB, roles, nombres y presupuestos de Codex.

Python del sistema. Escribe el informe solo en revisiones/codex/.
"""
import ast
import json
import math
import pathlib
import struct
import sys
RAIZ=pathlib.Path(__file__).resolve().parents[3]
carpeta=RAIZ/'web/public/models/ciudad/codex'
reparto=json.loads((RAIZ/'reparto/manzanas.json').read_text())
esperados={m['id'] for m in reparto['manzanas']+reparto['espacios'] if m['dueno']=='codex'}
man=json.loads((carpeta/'manifiesto.json').read_text())
faltan=esperados-set(man)
assert not set(man)-esperados,('Modelos fuera del reparto',set(man)-esperados)
assert not faltan or '--parcial' in sys.argv,('Cobertura',faltan)
mod=ast.parse((RAIZ/'blender/kit/paleta.py').read_text())
roles=set(next(ast.literal_eval(n.value) for n in mod.body if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=='PALETA' for t in n.targets)))
# Arquitecturas singulares reconstruidas por las correcciones de la plaza:
# Hotel Plaza, edificio USFX y banco de la esquina con cúpula. Presupuesto
# de monumento (60.000), manteniendo 15.000 para las casas corrientes.
monumentos={'E2c6601','E03fe1d','E627dd1','Ee30c62','M059_hotel_plaza','M058_USFX','Ed8b92f','E1aa79c','Eaeb297','M027_templo'}
# La Asamblea es un edificio institucional histórico, con presupuesto de monumento.
monumentos.add('Eae1b1b')
# Universidad: siete pares de aulas en tres niveles, basamento y portón.
monumentos.add('M061_UCB_aulas')
informe={};total=0
for mid,entrada in sorted(man.items()):
    ruta=carpeta/entrada['archivo'];datos=ruta.read_bytes()
    magic,version,longitud=struct.unpack_from('<III',datos)
    assert magic==0x46546c67 and version==2 and longitud==len(datos),mid
    n,t=struct.unpack_from('<II',datos,12);g=json.loads(datos[20:20+n])
    assert t==0x4e4f534a
    nombres=[m['name'] for m in g['meshes']];assert len(nombres)==len(set(nombres)),mid
    asignada=next(m for m in reparto['manzanas']+reparto['espacios'] if m['id']==mid)
    ids_originales={e['id'] for e in asignada.get('edificios',[])}
    assert ids_originales.issubset(nombres),(mid,'Edificios faltantes',ids_originales-set(nombres))
    for mat in g.get('materials',[]):assert mat['name'].split('__')[0] in roles,(mid,mat['name'])
    objetos={}
    for m in g['meshes']:
        tri=0
        for pr in m['primitives']:
            assert pr.get('mode',4)==4,(mid,'Primitiva no triangular')
            a=g['accessors'][pr['indices']];assert a['count']%3==0
            tri+=a['count']//3
            pos=g['accessors'][pr['attributes']['POSITION']]
            assert all(math.isfinite(v) for v in pos['min']+pos['max']),(mid,'Coordenada inválida')
        limite=60000 if m['name'] in monumentos or 'SanMiguel' in m['name'] else 15000
        assert tri<=limite,(mid,m['name'],tri,limite)
        objetos[m['name']]=tri
    tris=sum(objetos.values());assert tris==entrada['triangulos'],(mid,tris,entrada)
    assert len(g['meshes'])==entrada['objetos'],(mid,'Cantidad de objetos')
    assert (RAIZ/'blender/zonas/codex'/f'{mid}.py').exists(),(mid,'Sin fuente')
    informe[mid]={'triangulos':tris,'objetos':objetos};total+=tris
assert total<=1500000,total
salida=RAIZ/'revisiones/codex/auditoria_modelos.json'
salida.write_text(json.dumps({'modelos':len(man),'triangulos':total,'resultado':'correcto','detalle':informe},indent=2))
print(f'{len(man)} modelos; {total:,} triángulos. Integridad, roles, fuentes y presupuestos correctos.')
if faltan:print('Cobertura parcial; faltan por exportar:',', '.join(sorted(faltan)))
