"""M057 — frente este; inventario y funciones en plaza_este.py / INVENTARIO_PLAZA.md."""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from plaza_este import arco_vidrio
from detalles_plaza_codex import revisar_correcciones
m,col=iniciar('codex','M057')
frentes=arco_vidrio(m,col)
revisar_correcciones('M057',[19, 20],frentes)
