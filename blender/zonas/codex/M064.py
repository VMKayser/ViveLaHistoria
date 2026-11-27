"""M064 — esquina con cúpula según R0023/24; inventario en INVENTARIO_PLAZA.md."""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from esquina_audiencia import esquina_con_cupula
from detalles_plaza_codex import revisar_correcciones
m,col=iniciar('codex','M064')
frentes=esquina_con_cupula(m,col)
revisar_correcciones('M064',[23,24],frentes)
