"""Manzanas sin foto: mínimo colonial compartido, no fidelidad atribuida.
Fuente de huellas recortadas: reparto/manzanas.json. Casas con portón,
ventanas con reja, zócalo, cornisa/alero, balcón y techo de teja.
"""
import os,sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')))
sys.path.insert(0,os.path.dirname(__file__))
from kit import *
from casas_codex import casa_minima

def construir(mid,completar_laterales=False):
    m,col=iniciar('codex',mid);vistos=set()
    for e in m['edificios']:
        if e['id'] in vistos:continue
        vistos.add(e['id']);casa_minima(e,col,completar_laterales=completar_laterales)
    exportar('codex',mid)
    return m
