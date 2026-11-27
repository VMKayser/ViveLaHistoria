"""Exporta únicamente las manzanas sin foto de Codex, una por una."""
import os
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from generica import construir,datos
CON_FOTO={'M055','M037','M061','M056','M027','M063'}
for m in datos.reparto()['manzanas']:
    if m['dueno']=='codex' and m['id'] not in CON_FOTO:
        if any(e.get('fotos') for e in m['edificios']):
            raise ValueError('La manzana tiene fotos: '+m['id'])
        construir(m['id'])
