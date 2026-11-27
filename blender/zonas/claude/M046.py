"""M046 — B4 y B5 de sillería (R0004, R0005, R0007).
Frente a la Plaza 25 de Mayo: edificios con fachada propia según las fotos de las correcciones (plaza_norte.py);
el resto de la manzana, versión sencilla (generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plaza_norte import script_manzana  # noqa: E402

script_manzana("M046", 42.0, 80.0, ['R0004', 'R0005', 'R0007', 'R0006'], vecinas=("M047",))
