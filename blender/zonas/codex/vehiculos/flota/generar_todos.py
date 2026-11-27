"""Generación secuencial para respetar el límite de un Blender pesado a la vez."""
import json
import os
from pathlib import Path
import subprocess
import sys

AQUI=Path(__file__).resolve().parent
RAIZ=AQUI.parents[4]
disenos=json.loads((AQUI/'disenos.json').read_text())
elegidos=[a for a in sys.argv[1:] if not a.startswith('--')] or list(disenos)
opciones=[a for a in sys.argv[1:] if a.startswith('--')]
blender=Path.home()/'apps/blender-5.2.3-linux-x64/blender'
entorno=dict(os.environ,__NV_PRIME_RENDER_OFFLOAD='1',__GLX_VENDOR_LIBRARY_NAME='nvidia')
for identificador in elegidos:
    assert identificador in disenos,identificador
    carpeta=RAIZ/'revisiones/codex/flota'/identificador
    carpeta.mkdir(parents=True,exist_ok=True)
    log=carpeta/'construccion.log'
    print('Construyendo',identificador,flush=True)
    with log.open('w') as f:
        resultado=subprocess.run([str(blender),'-b','-t','2','-P',str(AQUI/'construir.py'),'--',identificador,*opciones],env=entorno,stdout=f,stderr=subprocess.STDOUT)
    contenido=log.read_text()
    if resultado.returncode or 'Traceback' in contenido or 'FLOTA_VALIDACION' not in contenido:
        raise SystemExit(contenido[-5000:])
    print('Exportado y revisiones renderizadas:',identificador,flush=True)
