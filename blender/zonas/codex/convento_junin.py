"""Convento Eeb6abd/M037 frente a Junín, repaso #22.

130357/130401: dos accesos y tres vanos rectos altos bajo medallón solar
en el tramo próximo al templo; dos arcos en el quiebre; prolongación con
rejas y vanos rectos. No corresponden balcones residenciales en ese muro.
La cota de fachada se mide en Junín (55,5 m), no detrás del lote (58,1 m).
"""
from kit import *
from piezas_codex import prisma_seguro,trasladar,ventana_arco_reja
from casas_codex import cubierta_baja
from junin_arenales import solar
from seleccion_frentes_codex import lados_de_calle
BLANCO='#eeeae7'


def construir_convento(e,col):
    h=e['huella'];frentes=lados_de_calle(lados(h),'Calle Batalla de Junín',(-.78,.63))
    z=max(altura_suelo(*p) for l in frentes for p in (l['a'],l['b']))
    zb=min(altura_suelo(*p) for p in h)-.5;c=Constructor(e['id'])
    prisma_seguro(c,h,zb,z+8.8,'muro',BLANCO)
    primero=True
    for lado in frentes:
        f=Fachada(c,lado,z)
        puertas=(4.2,12.5) if primero else ()
        limites=[0]+[a for s in puertas for a in (s-.95,s+.95)]+[f.largo]
        for a,b in zip(limites[::2],limites[1::2]):
            if b>a:zocalo(f,.9,s0=a,s1=b,desde=zb-z,color='#b49977',sillares=False)
        for ss in puertas:
            p=f.punto(ss,0);ff=trasladar(f,h=altura_suelo(p.x,p.y)+.12-z,d=.025)
            puerta(ff,ss,ancho=1.5,alto=2.9,color='#67452f',color_moldura=BLANCO)
        if primero:
            for ss in (3.0,9.1,15.2):
                ventana(f,ss,4.7,ancho=.95,alto=1.7,reja=True,color_moldura=BLANCO)
            solar(f,9.1,7.1)
        else:
            # El ensanche dejó dos tramos de Junín; los arcos del quiebre
            # y la prolongación pertenecen al mismo segundo tramo.
            for ss in (1.9,4.8):ventana_arco_reja(f,ss,4.7,ancho=1.0,alto=2.6,color_moldura=BLANCO)
            for ss in (9,14,19,24,29,33):
                ventana(trasladar(f,d=.02),ss,1.3,ancho=.9,alto=1.7,reja=True,color_moldura=BLANCO)
                ventana(f,ss,4.8,ancho=.9,alto=1.7,reja=True,color_moldura=BLANCO)
        cornisa(f,8.6,alto=.15,vuelo=.15,color=BLANCO)
        alero_tejas(f,8.8,fondo=1.1,vuelo=.3)
        primero=False
    cubierta_baja(c,h,z+8.8,'#b36b4e')
    c.objeto(col)
