"""M065 — frente este; inventario y funciones en plaza_este.py / INVENTARIO_PLAZA.md."""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from plaza_este import ala_baja
from detalles_plaza_codex import revisar_correcciones
m,col=iniciar('codex','M065')
frentes=ala_baja(m,col)
revisar_correcciones('M065',[22],frentes)
