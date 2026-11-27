"""Limpieza de la cuadra institucional por pedido del usuario, 2026-11-13.

130715/724/736/741: ante Catedral y Gobernación no hay viviendas ni
tiendas interpuestas. Se retira la casa genérica E749b6b y se conserva
su área como patio del conjunto, sin atribuirle distribución documental.
El suelo de enlace hasta la acera evita huecos y que BASE vuelva a
clasificar esa franja como terreno libre para casas.
"""
from mathutils import Vector
from kit import *
from piezas_codex import pavimentar
from pavimentos_codex import pavimento_fuera_calles
from casas_codex import cubierta_baja
from piezas_codex import recortar_interior


def patio_institucional(e,col):
    c=Constructor(e['id'])
    pavimentar(c,e['huella'],'adoquin',offset=.14,paso=3,color='#c9c0aa')
    c.objeto(col)


def suelo_frente_institucional(col):
    cat=lados(edificio('M055','E03fe1d')['huella'])[2]
    gob=lados(edificio('M055','E2c6601')['huella'])[0]
    a,b,d=Vector(cat['a']),Vector(cat['b']),Vector(gob['b'])
    na,nb=Vector(cat['normal']),Vector(gob['normal']);nm=(na+nb).normalized()
    h=[tuple(p) for p in (a,b,d,d+nb*14,b+nm*14,a+na*14)]
    c=Constructor('M055_suelo_conjunto_institucional')
    for pieza in pavimento_fuera_calles(h,datos.calles_reales()):
        pavimentar(c,pieza,'adoquin',offset=.14,paso=3,color='#c9c0aa')
    c.objeto(col)


def cubiertas_catedral(col):
    """Faldones de la nave y ala existente; el atrio permanece descubierto.

    La geometría interior no tiene levantamiento: pendiente baja estimada.
    No se añaden casas, lucarnas, torres ni cúpulas sin referencia.
    """
    e=edificio('M055','E03fe1d');h=e['huella']
    z=max(altura_suelo(*p) for p in h)+10.2
    f=Fachada(None,lados(h)[12],0)
    nave=recortar_interior(h,f,-8.75)
    from museo_codex import huellas_ala
    c=Constructor('M055_Catedral_cubiertas')
    for pol in (nave,huellas_ala()[0]):
        cubierta_baja(c,pol,z,'#b06b4e')
    c.objeto(col)
