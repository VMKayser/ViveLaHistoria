"""BASE (claude). Sin relleno de cuadras (pedido del usuario 2026-11-14: nada genérico detrás de las fachadas).
Calzadas, veredas y bordillos de TODA la zona con el ancho real de las calles
(reparto/calles_reales.json), más el mobiliario de vereda frente a las manzanas de claude y en los espacios sin
dueño (postes con cables, faroles, semáforos) y la Plaza San Francisco.

Uso: blender --background --python blender/zonas/claude/BASE.py [-- --sin-render]
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import altura_suelo, exportar, iniciar, revisar  # noqa: E402
from kit.salida import camara  # noqa: E402

from base_mobiliario import construir_mobiliario  # noqa: E402
from base_suelo import _zona, construir_suelo  # noqa: E402
from base_plazas import plaza_san_francisco  # noqa: E402

AGENTE, MID = "claude", "BASE"


def normales_arriba(ob):
    """Las superficies sueltas (calzada, marcas) deben mirar hacia arriba: el visor no dibuja la cara de atrás."""
    me = ob.data
    abajo = sum(1 for p in me.polygons if p.normal.z < -0.5)
    arriba = sum(1 for p in me.polygons if p.normal.z > 0.5)
    if abajo > arriba:
        for p in me.polygons:
            p.flip()
        me.update()


def tesela(caja, nombre):
    """Construye una tesela de la BASE (suelo, plaza, relleno y mobiliario cuyo arranque cae en `caja`) y la exporta a
    web/public/models/ciudad/claude/base_teselas/<nombre>.glb (fuera del manifiesto: el visor carga el BASE.glb
    ensamblado)."""
    import bpy
    from kit import datos
    m, col = iniciar(AGENTE, MID)
    z = _zona()
    from base_suelo import en_seccion
    dentro = lambda x, y: (z[0] < x < z[2] and z[1] < y < z[3] and caja[0] <= x < caja[2] and caja[1] <= y < caja[3]
                           and not en_seccion(x, y))
    cs, obs = construir_suelo(col, caja=caja)
    from base_plazas import PLAZA_SF
    cx = sum(p[0] for p in PLAZA_SF) / len(PLAZA_SF)
    cy = sum(p[1] for p in PLAZA_SF) / len(PLAZA_SF)
    if dentro(cx, cy):
        obs += plaza_san_francisco(col, cs)
    # el mobiliario va al final: sus cables se comprueban contra todo lo modelado cercano (base_mobiliario._libre)
    from base_mobiliario import fijar_obstaculos  # noqa: E402
    from base_relleno import _bvh_modelos  # noqa: E402
    fijar_obstaculos(_bvh_modelos(extra=[o for o in obs if o.name.startswith(("BASE_relleno", "BASE_plaza"))], caja=caja))
    obs += construir_mobiliario(col, cs, AGENTE, dentro)
    for ob in obs:
        if ob.name.startswith(("BASE_calzada", "BASE_marcas", "BASE_veredas", "BASE_plaza", "BASE_piso")):
            normales_arriba(ob)
    carpeta = os.path.join(datos.RAIZ, "web", "public", "models", "ciudad", "claude", "base_teselas")
    os.makedirs(carpeta, exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(o.name in col.all_objects)
    bpy.ops.export_scene.gltf(filepath=os.path.join(carpeta, nombre + ".glb"), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True, export_normals=True, export_materials="EXPORT")
    print(f"[BASE] tesela {nombre} lista")


def ensamblar():
    """Une todas las teselas en BASE.glb (lo que cargan el visor y las herramientas de los dos agentes)."""
    import bpy
    import glob
    from kit import datos
    m, col = iniciar(AGENTE, MID)
    carpeta = os.path.join(datos.RAIZ, "web", "public", "models", "ciudad", "claude", "base_teselas")
    for ruta in sorted(glob.glob(os.path.join(carpeta, "*.glb"))):
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=ruta)
        for o in set(bpy.data.objects) - antes:
            for c_ in list(o.users_collection):
                c_.objects.unlink(o)
            col.objects.link(o)
    exportar(AGENTE, MID, col)


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--tesela" in args:
    k = args.index("--tesela")
    tesela(tuple(float(v) for v in args[k + 1:k + 5]), args[k + 5])
    sys.exit(0)
if "--ensamblar" in args:
    ensamblar()
    sys.exit(0)

# modo completo (como antes): toda la zona en un solo proceso — lento; usar scripts/base.py (incremental)
m, col = iniciar(AGENTE, MID)
z = _zona()
from base_suelo import en_seccion  # noqa: E402
dentro = lambda x, y: z[0] < x < z[2] and z[1] < y < z[3] and not en_seccion(x, y)
cs, obs = construir_suelo(col)
obs += plaza_san_francisco(col, cs)
from base_mobiliario import fijar_obstaculos  # noqa: E402
from base_relleno import _bvh_modelos  # noqa: E402
fijar_obstaculos(_bvh_modelos(extra=[o for o in obs if o.name.startswith(("BASE_relleno", "BASE_plaza"))]))
obs += construir_mobiliario(col, cs, AGENTE, dentro)
for ob in obs:
    if ob.name.startswith(("BASE_calzada", "BASE_marcas", "BASE_veredas", "BASE_plaza", "BASE_piso")):
        normales_arriba(ob)
exportar(AGENTE, MID, col)

if "--sin-render" not in sys.argv:
    def vista(x, y, rumbo_grados, nombre, alto=1.6, mirar_alto=3.0, dist=30):
        r = math.radians(rumbo_grados)
        z0 = altura_suelo(x, y)
        return (nombre, (x, y, z0 + alto), (x + math.sin(r) * dist, y + math.cos(r) * dist, z0 + mirar_alto))
    revisar(AGENTE, MID, fotos=[], camaras_extra=[
        vista(-150, 14, 315, "ravelo_noroeste"),
        vista(-215, 66, 135, "ravelo_sureste"),
        vista(-250, 20, 40, "junin"),
        vista(-140, -50, 140, "arce"),
        ("aerea", (-120, -60, 140), (-190, 30, 55)),
    ])
