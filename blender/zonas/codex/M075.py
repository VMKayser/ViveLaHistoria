"""M075: casona del mirador de enfrente en R0095. INVENTARIO_M075.md.
La casona sur de R0096–R0098 es AMP_S de Claude y se conserva aparte.
"""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from esquina_ortiz_dalence import construir_casona
m,col=iniciar('codex','M075')
for e in m['edificios']:construir_casona(e,col)
exportar('codex','M075')
