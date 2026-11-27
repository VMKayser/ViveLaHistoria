"""M042 — B2 y B3 (R0002, R0003).
Frente a la Plaza 25 de Mayo: edificios con fachada propia según las fotos de las correcciones (plaza_norte.py);
el resto de la manzana, versión sencilla (generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plaza_norte import script_manzana  # noqa: E402

script_manzana("M042", 80.0, 104.0, ['R0002', 'R0003'])
