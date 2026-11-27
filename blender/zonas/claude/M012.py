"""M012 — sin foto propia: versión sencilla y coherente con la calle (ver generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generica import construir  # noqa: E402

# 2026-11-13: el frente a Junín lo construye PEATONAL.py; aquí solo queda lo de atrás de su franja
from peatonal_marco import cortar_franja  # noqa: E402
construir("claude", "M012", forzar={"E744c03": {"tipo": "colonial", "muro": "#f6f4ef", "pisos": 2}},
          filtro_huella=lambda e: cortar_franja(e["huella"], "NO"))
