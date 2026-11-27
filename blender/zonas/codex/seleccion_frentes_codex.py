"""Selección geométrica de fachadas; independiente de Blender para auditarla.

Los índices cambian al recortar calles. La calle, la normal exterior y la
continuidad física definen el frente; una medianera nunca es un retorno.
"""
import math


def lados_de_calle(lados, calle, normal, largo_min=.3):
    modulo = math.hypot(*normal)
    if modulo == 0:
        raise ValueError('Normal nula para ' + calle)
    candidatos = [l for l in lados if l['a_calle'] and l['calle'] == calle
                  and l['largo'] >= largo_min
                  and sum(a*b for a, b in zip(l['normal'], normal))/modulo > .90]
    if not candidatos:
        raise ValueError('No hay fachada visible hacia ' + calle + ' / ' + str(normal))
    return encadenar(candidatos)


def encadenar(lados, tolerancia=.025):
    """Devuelve una cadena a→b; rechaza frentes separados por patios o vacíos."""
    pendientes = list(lados)
    if not pendientes:
        raise ValueError('Frente vacío')
    inicios = [l for l in pendientes if not any(
        otro is not l and math.dist(otro['b'], l['a']) < tolerancia
        for otro in pendientes)]
    if len(inicios) != 1:
        raise ValueError('El frente no es una única cadena abierta')
    cadena = [inicios[0]]
    pendientes.remove(cadena[0])
    while pendientes:
        siguientes = [l for l in pendientes if math.dist(cadena[-1]['b'], l['a']) < tolerancia]
        if len(siguientes) != 1:
            raise ValueError('Lados de fachada desconectados o bifurcados')
        cadena.append(siguientes[0])
        pendientes.remove(cadena[-1])
    return cadena
