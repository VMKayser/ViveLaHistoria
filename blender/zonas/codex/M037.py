"""M037 — frentes históricos y San Miguel revisados con fotos.

Fotos: hoja completa (16); detalles 130452, 130521, 130638, 130440.
E627dd1 frente a Arenales, seleccionado por calle y normal, fotos 130452–130532: dos plantas, blanco
#eeeae7 y recuadros grises #81898b, zócalo de piedra gris 1.1 m.
Vanos bajos de medio punto con reja y puertas de madera; altos rectos,
antepechos de balaustres, frontones triangulares y pilastras pareadas.
Esquina hacia plaza: retorno del mismo tratamiento. Se omite el texto
comercial; placa histórica sin texto. Distribución longitudinal provisional.
Ee30c62 orientación SE, 130638 (frente ahora en S_PLAZA25): frente de Casa de la Libertad y vecinos que el
lienzo une: cal blanca, marcos de piedra, zócalo 1.3 m, balcón de madera
corrido con alero. No duplicar el id repetido en reparto/manzanas.json.
Eeb6abd, 130427–130440: muro blanco largo con alero, ventana alta aislada;
la torre y atrio de San Miguel se documentan pero se implantan por separado.
E469654, E97ee92, Efc5742, E1aa79c: sin foto propia suficiente; versión sencilla.
"""
import os
import sys
import math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import trasladar, prisma_seguro, ventana_arco_reja, farol_pie, arbol_podado, ventana_rebajada
from casas_codex import casa_minima
AGENTE='codex'
MANZANA='M037'
BLANCO='#eeeae7'
GRIS='#81898b'
m,col=iniciar(AGENTE,MANZANA)
frentes_revision=[]


def cuerpo(e,alto,color=BLANCO):
    c=Constructor(e['id'])
    ls=lados(e['huella'])
    z=max(altura_suelo(*p) for p in e['huella'])
    zb=min(altura_suelo(*p) for p in e['huella'])-.5
    prisma_seguro(c,e['huella'],zb,z+alto,'muro',color)
    return c,ls,z,zb


vistos=set()
for e in m['edificios']:
    if e['id'] in vistos:continue
    vistos.add(e['id'])
    if e['id']=='E627dd1':
        from teatro_codex import construir_teatro
        construir_teatro(e,col)
    elif e['id']=='Ee30c62':
        c,ls,z,zb=cuerpo(e,8.3)
        # S_PLAZA25 posee el frente reconstruido sobre la línea de calle.
        # La cara antigua está 9 m detrás: solo queda el cuerpo de apoyo,
        # sin segunda fachada, balcón, alero ni vegetación escondidos.
        c.objeto(col)
    elif e['id']=='Eeb6abd':
        from convento_junin import construir_convento
        construir_convento(e,col)
    elif e['id']=='E1aa79c':
        from rectorado_codex import construir_rectorado
        frentes_revision+=construir_rectorado(e,col)
    else:
        casa_minima(e,col)
# Faroles de pie del frente del Teatro, visibles en 130452 y 130521.
from frentes_codex import frente_de_calle
from detalles_plaza_codex import punto_encadenado
e=edificio(MANZANA,'E627dd1');f,guia_teatro=frente_de_calle(e,None,'Calle José Álvarez de Arenales',(.63,.78),0)
# (claude, R0122 2026-11-14: "postes muy al medio, más al borde de la acera") junto al bordillo
import sys as _s, os as _o
_s.path.insert(1,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..','claude'))
from piezas_claude import junto_al_bordillo
for k,ss in enumerate((6,19,33,46)):
    p=punto_encadenado(guia_teatro,ss,0,0)
    x,y=junto_al_bordillo(p.x,p.y,f.n.x,f.n.y,retiro=.4)
    farol_pie(f'M037_farol_teatro_{k}',x,y,col,alto=3.4)
# Árboles de vereda hacia plaza, 130638. Distribución pendiente de levantar completa.
e=edificio(MANZANA,'Ee30c62')
# Referencia geométrica del frente antiguo, solo para proyectar los árboles
# de la foto al bordillo de la plaza; no se decora esta cara interior.
lado_plaza=max((l for l in lados(e['huella']) if l['normal'][0]>.7 and l['normal'][1]<-.5),key=lambda l:l['largo'])
f=Fachada(None,lado_plaza,0)
for k,ss in enumerate((5,12,19,26,33,40)):
    p=f.punto(ss,0,0)
    x,y=junto_al_bordillo(p.x,p.y,f.n.x,f.n.y,retiro=.7)
    arbol_podado(f'M037_arbol_plaza_{k}',x,y,col,radio=1.4,direccion=tuple(f.n[:2]))

# (claude, 2026-11-24, R0219 — pedido del usuario "hazlo tu, cambio de dueno"): la nave de San Miguel sobre
# Arenales, su portada, torre y atrio pasan al espacio SAN_MIGUEL de claude (blender/zonas/claude/SAN_MIGUEL.py).
from mobiliario_junin_oeste import construir_mobiliario
construir_mobiliario(MANZANA,col)

# El templo de las correcciones R0036/37 se reconstruye en M027,
# al oeste de Junín; se retira la implantación aproximada que lo duplicaba.
exportar(AGENTE,MANZANA)
if '--sin-render' not in sys.argv:
    from detalles_plaza_codex import revisar_correcciones
    revisar_correcciones(MANZANA,[25],frentes_revision)
