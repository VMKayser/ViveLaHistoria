"""M027 — Junín y templo de Arenales, R0034–R0037. Inventario en INVENTARIO_JUNIN.md."""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from junin_arenales import casona_junin,templo_arenales
from detalles_plaza_codex import revisar_correcciones
m,col=iniciar('codex','M027')
frentes=[casona_junin(m['edificios'][0],col)]+templo_arenales(col)
from mobiliario_junin_oeste import construir_mobiliario
construir_mobiliario('M027',col)
exportar('codex','M027')
revisar_correcciones('M027',[34,35,36,37],frentes)
