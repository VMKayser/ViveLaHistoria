"""Siluetas escultóricas simplificadas para los monumentos ubicados por OSM.

No son retratos reconstruidos: las fotos periféricas no muestran el detalle
central. Se resuelve la figura de pie a escala, diferenciada de su pedestal.
"""
from piezas_codex import rama


def figura_monumento(c,x,y,z,escala=1.0,color='#6a7066'):
    # Botas y piernas separadas; abrigo, hombros, cuello y cabeza.
    s=escala
    for dx in (-.115,.115):
        c.caja(x+(dx-.075)*s,y-.18*s,z,x+(dx+.075)*s,y+.11*s,z+.08*s,'metal',color)
        c.cilindro(x+dx*s,y,z+.08*s,z+.80*s,.075*s,'metal',color,lados=8,radio_arriba=.095*s)
    c.cilindro(x,y,z+.72*s,z+1.4*s,.20*s,'metal',color,lados=10,radio_arriba=.25*s)
    c.caja(x-.26*s,y-.12*s,z+1.24*s,x+.26*s,y+.12*s,z+1.43*s,'metal',color)
    c.cilindro(x,y,z+1.42*s,z+1.54*s,.075*s,'metal',color,lados=8)
    c.esfera(x,y,z+1.67*s,.15*s,'metal',color,segmentos=12)
    for signo in (-1,1):
        a=(x+signo*.24*s,y,z+1.34*s)
        b=(x+signo*.38*s,y-.04*s,z+1.08*s)
        d=(x+signo*.26*s,y-.17*s,z+.94*s)
        rama(c,a,b,.065*s,.055*s,rol='metal',color=color)
        rama(c,b,d,.055*s,.04*s,rol='metal',color=color)
