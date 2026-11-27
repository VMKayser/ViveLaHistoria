"""Planta documentada del pabellón de M060, compartida con su vecino.

R0083/R0084 muestran el pabellón detrás de la reja, junto al Archivo de
M061. La casa aproximada del Archivo debe ceder ese encuentro, no atravesar
el pabellón fotografiado. No cambia el reparto compartido.
"""
import math


def marco_patio_m060():
    return {'a':(-339.36,-323.46),'b':(-329.58,-331.88),'normal':(-.652,-.758)}


def huella_pabellon_m060(margen=0):
    f=marco_patio_m060();a,b=f['a'],f['b'];L=math.dist(a,b)
    u=((b[0]-a[0])/L,(b[1]-a[1])/L);n=f['normal'];r=3.25+margen
    def punto(s,d):return (a[0]+u[0]*s+n[0]*d,a[1]+u[1]*s+n[1]*d)
    return [punto(7.2+r*math.cos(k*math.pi/16),-18+r*math.sin(k*math.pi/16)) for k in range(17)]+[
        punto(7.2-r,-20.1-margen),punto(7.2+r,-20.1-margen)]


def huella_patio_m060():
    return [(-339.36,-323.46),(-329.58,-331.88),(-328.65,-326.55),(-310.2,-319.9),(-320.1,-301.1)]
