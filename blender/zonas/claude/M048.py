"""M048 — B6, B7 y el banco de la esquina (R0008–R0012).
Frente a la Plaza 25 de Mayo: edificios con fachada propia según las fotos de las correcciones (plaza_norte.py);
el resto de la manzana, versión sencilla (generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plaza_norte import script_manzana  # noqa: E402

# t0 = 0: desde la esquina E de la plaza; con t < 0 los árboles seguían por la Calle Daniel Calvo, que no tiene
# ninguno (R0205: "esta cuadra no tiene arboles, quitarlos todos")
script_manzana("M048", 0.0, 42.0, ['R0008', 'R0009', 'R0010', 'R0011', 'R0012'])
