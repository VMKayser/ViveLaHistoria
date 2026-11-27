"""M060: patio abierto de Dalence, R0083/R0084; inventario en INVENTARIO_DALENCE.md."""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from dalence_codex import patio_dalence
m,col=iniciar('codex','M060')
frentes=patio_dalence(m['edificios'][0],col)
exportar('codex','M060')
if '--sin-render' not in sys.argv:
 from detalles_plaza_codex import revisar_correcciones
 revisar_correcciones('M060',[83,84],frentes)
