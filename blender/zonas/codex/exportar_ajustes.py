"""Reexporta scripts propios sin render; admite una lista explícita de archivos.

blender ... --python ejecutar.py -- exportar_ajustes.py M055.py M037.py
Sin lista, procesa los cinco conjuntos fotografiados que siguen en revisión.
"""
import os
import runpy
import sys
carpeta=os.path.dirname(os.path.abspath(__file__))
seleccion=[a for a in sys.argv[1:] if a.endswith('.py')]
if not seleccion:seleccion=['M055.py','M037.py','M056.py','M061.py','P01.py']
sys.argv=['exportar_ajustes.py','--sin-render']
for nombre in seleccion:
    ruta=os.path.abspath(os.path.join(carpeta,nombre))
    if os.path.dirname(ruta)!=carpeta:raise ValueError('Solo scripts propios')
    print('[codex] Exportar',nombre,flush=True)
    runpy.run_path(ruta,run_name='__main__')
