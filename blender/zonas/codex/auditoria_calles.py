"""Ejecuta la auditoría común en lectura y cierra Blender sin espera de audio."""
import os,sys,runpy
raiz=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../..'))
codigo=0
try:
 runpy.run_path(os.path.join(raiz,'blender/zonas/claude/auditoria.py'),run_name='__main__')
except BaseException:
 import traceback
 traceback.print_exc();codigo=1
sys.stdout.flush();sys.stderr.flush();os._exit(codigo)
