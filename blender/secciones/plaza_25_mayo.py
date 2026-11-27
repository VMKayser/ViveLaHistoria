"""SECCIÓN PILOTO — Plaza 25 de Mayo y sus cuatro calles (refactor 2026-11-14, pedido del usuario: "empezar con la
sección piloto, implementación ya").

Qué hace esta sección:
- Suelo propio y continuo (trazado.py + construir.py): calzada de asfalto, veredas de baldosa que llegan hasta las
  fachadas, vereda perimetral de la plaza, bordillos con esquinas redondeadas. Sustituye a la BASE en este polígono
  (la BASE no dibuja nada dentro de secciones/*.json).
- Mobiliario de esta sección colocado sobre el bordillo: faroles ornamentales de brazo en las veredas de las fachadas
  (a 0,45 m del borde, uno cada ~24 m, nunca en la curva de una esquina ni contra un balcón o un árbol).
- Edificios: se salvan los ya modelados (M055 Catedral y Gobernación, M056 atrio, frente norte de plaza_norte,
  M053/M057/M058/M059/M065 del frente SE, P01 la plaza). Sus árboles y faroles de vereda alejados del bordillo se
  corren a él (construir.salvar_mobiliario, reescribe esos GLB).
- Frente NO rehecho sobre la línea real de la calle (plaza_25_mayo_frentes.py): Casa de la Libertad (foto 130638) y
  sus vecinos; en el lienzo la cuadra quedaba 9 m retirada y la fachada vieja (Ee30c62) sin ventanas.
- Fuera: la casita genérica M052 que el lienzo ponía dentro de la plaza.

Revisado en vivo en Blender con el MCP (scripts/abrir_seccion.sh plaza_25_mayo).

Uso: blender -b -P blender/secciones/plaza_25_mayo.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zonas", "claude"))
from kit import Constructor, altura_suelo, exportar, iniciar  # noqa: E402
import construir as K  # noqa: E402
import trazado as T  # noqa: E402
from base_mobiliario import farol_ornamental  # noqa: E402
import plaza_25_mayo_frentes as FR  # noqa: E402

AGENTE, MID = "claude", "S_PLAZA25"
SEC = T.cargar_seccion("plaza_25_mayo")

m, col = iniciar(AGENTE, MID)
g = T.trazar(SEC)
K.suelo(MID, g, col)
cm = Constructor(MID + "_marcas")
print(f"[seccion] {K.cebras(cm, g)} pasos de cebra")
cm.objeto(col)

# --- frente NO (Casa de la Libertad) sobre la línea real de la calle
FR.frente_libertad(col, g["calles"])
# --- esquina N (Arenales × Arce): edificio de esquina redondeada (fotos 130532, 130535); el lote estaba vacío
FR.esquina_alcaldia(col)
# --- Calle España, vereda SE: casona de la esquina con Daniel Calvo (Banco Ecofuturo) y casa gris, rehechas desde
# las fotos del usuario (R0206–R0210): ver zonas/claude/espana_se.py
import espana_se  # noqa: E402
espana_se.construir(col)
# --- esquina O (Estudiantes × Argentina): lote vacío, sin foto propia
FR.esquina_colonial(col, "SP25_esquina_O", "Calle Estudiantes", (-275.0, -210.0), "Calle Argentina",
                    (-275.0, -220.0), (-285.0, -216.0), largo_a=16.0, largo_b=14.0, pisos=(4.4, 4.2),
                    muro="#f6f4ef", remate="alero")
# --- primera cuadra de las calles que salen de la plaza (hileras diseñadas por cuadra)
print(f"[seccion] {FR.primeras_cuadras(col)} casas en las primeras cuadras")

# --- faroles de las veredas de las fachadas
bvh = K.bvh_modelos(g["limite"].bounds)
plaza_ext = g["plaza"].buffer(T.VEREDA_PLAZA + 0.5)
c = Constructor(MID + "_faroles")
puestos = []
for rec in K.linea_de_bordillo(g["vereda"], g["calzada"], 0.45):
    muestras = K.a_lo_largo(rec, 1.0, 0.0)
    for i, ((x, y), (ux, uy)) in enumerate(muestras):
        if i % 24 != 12:
            continue
        if plaza_ext.contains(K.Point(x, y)):          # vereda de la plaza: la amuebla su dueño
            continue
        # no en la curva de una esquina: el rumbo cambia poco 4 m antes y después
        a = muestras[max(0, i - 4)][1]
        b = muestras[min(len(muestras) - 1, i + 4)][1]
        if a[0] * b[0] + a[1] * b[1] < math.cos(math.radians(15)):
            continue
        if not K.libre(bvh, x, y, 0.8) or any(math.hypot(x - p, y - q) < 10 for p, q in puestos):
            continue
        # el brazo mira a la calzada
        nx, ny = uy, -ux
        if not g["calzada"].buffer(0.6).contains(K.Point(x + nx * 0.7, y + ny * 0.7)):
            nx, ny = -nx, -ny
        farol_ornamental(c, x, y, nx, ny)
        puestos.append((x, y))
c.objeto(col)
print(f"[seccion] {len(puestos)} faroles")
exportar(AGENTE, MID)

# --- modelos salvados: su mobiliario de vereda al bordillo (se reescriben sus GLB)
from kit.datos import RAIZ  # noqa: E402
# solo los modelos de claude: los GLB de codex no se reescriben desde aquí (AGENTS.md: cada uno escribe su carpeta)
SALVADOS = [("claude", "M055"), ("claude", "M056"), ("claude", "M040"), ("claude", "M042"), ("claude", "M046"),
            ("claude", "M048")]
K.salvar_mobiliario(g, [os.path.join(RAIZ, "web", "public", "models", "ciudad", a, i + ".glb") for a, i in SALVADOS])
