"""M028 — sin foto propia: versión sencilla y coherente con la calle (ver generica.py).
Las fotos 130440…130448 asociadas por cercanía muestran el conjunto de San Miguel, al otro lado de
Arenales (mitad de codex): no se usan aquí.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generica import construir  # noqa: E402

construir("claude", "M028")
