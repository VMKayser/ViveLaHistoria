"""Ejecuta en lectura la auditoría común sobre Codex y conserva cierre limpio.
Uso con ejecutar.py: auditoria_lectura.py -- codex M061
No modifica fuentes ni modelos de Claude.
"""
import os,sys,runpy
args=sys.argv[sys.argv.index('--')+1:]
assert args and args[0]=='codex','Este puente solo audita mi zona'
script=os.path.abspath(os.path.join(os.path.dirname(__file__),'../claude/auditoria.py'))
sys.argv=[script,'--']+args
runpy.run_path(script,run_name='__main__')
