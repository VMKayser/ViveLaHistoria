"""M019 — sin foto propia: versión sencilla y coherente con la calle (ver generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generica import construir  # noqa: E402

construir("claude", "M019")
