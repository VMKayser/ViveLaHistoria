"""M040 — B1 palacio blanco de tres plantas (R0001).
Frente a la Plaza 25 de Mayo: edificios con fachada propia según las fotos de las correcciones (plaza_norte.py);
el resto de la manzana, versión sencilla (generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plaza_norte import script_manzana  # noqa: E402

script_manzana("M040", 104.0, 200.0, ['R0001', 'R0002'])
