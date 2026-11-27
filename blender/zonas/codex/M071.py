"""M071: versión sencilla; edificios sin foto propia en el reparto.

Fuente de las huellas: reparto/manzanas.json, dueño codex.
Detalle de fachadas a calle: generica.py; no atribuir fidelidad fotográfica.
"""
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from generica import construir
construir('M071')
