"""Recorta copias GLB antes de importarlas: el original nunca se modifica.

Los exportados del proyecto tienen vértices absolutos glTF (X, Z, -Y),
sin transformaciones de nodo. Si aparece otro formato, se rechaza esta
optimización y el contexto conserva su importador normal.
"""
import copy
import hashlib
import json
import struct
from pathlib import Path
import numpy as np


def recortar_glb(ruta, limites, carpeta):
    ruta=Path(ruta);datos=ruta.read_bytes()
    sha=hashlib.sha256(datos).hexdigest()
    clave=hashlib.sha256((sha+repr(tuple(limites))).encode()).hexdigest()
    carpeta=Path(carpeta);carpeta.mkdir(parents=True,exist_ok=True)
    dest=carpeta/(clave+'.glb')
    if dest.exists():return str(dest)
    n,t=struct.unpack_from('<II',datos,12)
    assert t==0x4e4f534a
    g=json.loads(datos[20:20+n]);binario=memoryview(datos)[28+n:]
    if any(any(k in node for k in ('matrix','translation','rotation','scale','children','skin')) for node in g['nodes']):
        return str(ruta)
    if g.get('extensionsUsed') or any('sparse' in a for a in g['accessors']):return str(ruta)
    tipos={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    anchos={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def leer(indice):
        a=g['accessors'][indice];v=g['bufferViews'][a['bufferView']]
        dt=np.dtype(tipos[a['componentType']]);ancho=anchos[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],ancho),dt,binario,offset,
                          strides=(v.get('byteStride',dt.itemsize*ancho),dt.itemsize))
    nuevo=copy.deepcopy(g)
    nuevo.update(accessors=[],bufferViews=[],meshes=[],nodes=[],scenes=[{'nodes':[]}],scene=0)
    salida=bytearray()
    def emitir(arr,original=None,indices=False):
        arr=np.ascontiguousarray(arr)
        while len(salida)%4:salida.append(0)
        vista={'buffer':0,'byteOffset':len(salida),'byteLength':arr.nbytes,'target':34963 if indices else 34962}
        salida.extend(arr.tobytes());nuevo['bufferViews'].append(vista)
        a=copy.deepcopy(g['accessors'][original]) if original is not None else {'componentType':5125,'type':'SCALAR'}
        a.pop('byteOffset',None);a.pop('min',None);a.pop('max',None)
        a.update(bufferView=len(nuevo['bufferViews'])-1,count=len(arr))
        if original is not None and 'min' in g['accessors'][original]:
            a.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
        nuevo['accessors'].append(a)
        return len(nuevo['accessors'])-1
    mapeo={}
    for i,m in enumerate(g['meshes']):
        prims=[]
        for pr in m['primitives']:
            assert pr.get('mode',4)==4
            pos=leer(pr['attributes']['POSITION']);idx=leer(pr['indices']).reshape(-1,3)
            # glTF tiene Y arriba: planta del proyecto = (x, -z).
            tri=pos[idx];lo=tri.min(axis=1);hi=tri.max(axis=1)
            usar=(hi[:,0]>=limites[0])&(lo[:,0]<=limites[2])&(-lo[:,2]>=limites[1])&(-hi[:,2]<=limites[3])
            if not usar.any():continue
            vertices,rev=np.unique(idx[usar],return_inverse=True)
            p=copy.deepcopy(pr);p['indices']=emitir(rev.astype('<u4').reshape(-1,1),indices=True)
            p['attributes']={k:emitir(leer(a)[vertices],a) for k,a in pr['attributes'].items()}
            prims.append(p)
        if prims:
            mapeo[i]=len(nuevo['meshes']);nuevo['meshes'].append(dict(m,primitives=prims))
    for node in g['nodes']:
        if node.get('mesh') not in mapeo:continue
        node=dict(node,mesh=mapeo[node['mesh']]);nuevo['scenes'][0]['nodes'].append(len(nuevo['nodes']));nuevo['nodes'].append(node)
    # glTF requiere al menos una primitiva. Si no hay contexto en esta
    # ventana, el importador normal lo descartará por su caja mundial.
    if not nuevo['meshes']:return str(ruta)
    nuevo['buffers']=[{'byteLength':len(salida)}]
    texto=json.dumps(nuevo,separators=(',',':')).encode()
    texto+=b' '*((-len(texto))%4);salida.extend(b'\0'*((-len(salida))%4))
    blob=struct.pack('<III',0x46546c67,2,28+len(texto)+len(salida))+struct.pack('<II',len(texto),0x4e4f534a)+texto+struct.pack('<II',len(salida),0x004e4942)+salida
    temporal=dest.with_suffix('.tmp');temporal.write_bytes(blob);temporal.replace(dest)
    print('[contexto GLB]',ruta.name,len(datos),'→',len(blob),'bytes',flush=True)
    return str(dest)
