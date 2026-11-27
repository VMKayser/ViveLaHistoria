"""M058 — frente este; inventario y funciones en plaza_este.py / INVENTARIO_PLAZA.md."""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from plaza_este import usfx
from detalles_plaza_codex import revisar_correcciones
m,col=iniciar('codex','M058')
frentes=usfx(m,col)
revisar_correcciones('M058',[20, 21],frentes)
