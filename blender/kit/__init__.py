"""Kit compartido de modelado de la ciudad (Claude y Codex). Ver .agents/skills/modelado-ciudad/SKILL.md.

Uso típico en blender/zonas/<agente>/<MANZANA>.py:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    from kit import *
"""

from . import arquitectura, datos, nucleo, paleta, salida  # noqa: F401
from .arquitectura import *  # noqa: F401,F403
from .datos import altura_suelo, edificio, lados, manzana, ruta_foto, ubicaciones  # noqa: F401
from .nucleo import Constructor, Fachada  # noqa: F401
from .paleta import PALETA, material  # noqa: F401
from .salida import camara, camara_desde_foto, contexto, exportar, iniciar, revisar  # noqa: F401

VERSION = "1.0"
