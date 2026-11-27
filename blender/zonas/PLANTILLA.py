"""PLANTILLA — copiar a blender/zonas/<agente>/<MANZANA>.py y completar.

Ejecutar (desde la raíz del proyecto):
    ~/apps/blender-5.2.3-linux-x64/blender --background --python blender/zonas/<agente>/<MANZANA>.py
Luego:
    python3 scripts/comparar.py <agente> <MANZANA>     # arma render | foto real

Un script por manzana. Es la fuente de verdad: el GLB se regenera siempre desde aquí.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from kit import *  # noqa: E402,F403

AGENTE = "claude"     # "claude" o "codex": tiene que ser el dueño de la manzana
MANZANA = "M000"      # id de reparto/manzanas.json

m, col = iniciar(AGENTE, MANZANA)

# ---------------------------------------------------------------------------
# Un bloque por edificio. Anota lo que ves en las fotos (#n = número en ficha_fotos.jpg).
#
# E000000 — <nombre o descripción>
#   fotos: #1 #2 ... | pisos: 2 | color muro: #f3e6d3 | zócalo: piedra 1.4 m
#   calle (lado 1): 5 vanos por piso, portón en arco al centro, balcón corrido arriba,
#   remate: alero de tejas con canes | lado 2: medianera (liso)
# ---------------------------------------------------------------------------

for e in m["edificios"]:
    # Punto de partida genérico: REEMPLAZAR por la versión fiel a las fotos de cada edificio.
    ob, lados_e = edificio_colonial(e["id"], e["huella"], pisos=2, coleccion=col)

# Ejemplo de fachada a mano (en vez de edificio_colonial):
#   c = Constructor("E000000")
#   huella = edificio(MANZANA, "E000000")["huella"]
#   ...prisma, techo_plano...
#   l = lados(huella)[1]
#   f = Fachada(c, l, altura_suelo(*(l["a"])))
#   zocalo(f, 1.4); ventana(f, 3.0, 5.2, balcon="hierro"); puerta(f, 6.0, arco=True); alero_tejas(f, 8.6)
#   c.objeto(col)

exportar(AGENTE, MANZANA)
revisar(AGENTE, MANZANA)  # renders desde cada foto -> revisiones/<agente>/<MANZANA>/
