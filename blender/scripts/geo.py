"""Conversión lat/lon <-> metros del lienzo urban-export (mismas constantes que web/src/mapa/geo.ts).

El nombre del FBX trae el centro redondeado a 4 decimales (±5 m). El desfase real se
midió cruzando las esquinas de edificios OSM con los vértices del FBX (mediana 1.6 m tras corregir).
"""

import math

LAT0 = -19.0460
LON0 = -65.2578
R = 6378137.0
DX = 4.69  # metros al este
DY = 3.09  # metros al norte
_KX = math.pi / 180 * R * math.cos(math.radians(LAT0))
_KY = math.pi / 180 * R


def a_metros(lat, lon):
    return ((lon - LON0) * _KX + DX, (lat - LAT0) * _KY + DY)


def a_latlon(x, y):
    return (LAT0 + (y - DY) / _KY, LON0 + (x - DX) / _KX)
