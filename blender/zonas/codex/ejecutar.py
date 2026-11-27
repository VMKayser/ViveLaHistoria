"""Ejecuta un script propio y sale tras vaciar los logs; evita el bloqueo de PulseAudio al cerrar Blender.

Uso: blender --background --python blender/zonas/codex/ejecutar.py -- M055.py --sin-render
"""
import os
import runpy
import sys
import traceback

argumentos=sys.argv[sys.argv.index('--')+1:]
carpeta=os.path.dirname(os.path.abspath(__file__))
script=os.path.abspath(os.path.join(carpeta,argumentos[0]))
if os.path.dirname(script)!=carpeta:
    print('[codex] Error: solo scripts propios de Codex',file=sys.stderr,flush=True)
    os._exit(1)
sys.argv=[script]+argumentos[1:]
print("[codex] Ejecutando",script,flush=True)
codigo=0
try:
    runpy.run_path(script,run_name='__main__')
except BaseException:
    traceback.print_exc()
    codigo=1
sys.stdout.flush()
sys.stderr.flush()
os._exit(codigo)
