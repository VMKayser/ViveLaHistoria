"""Baranda verde de M075/R0096: rombos, postes y retornos sobre losa."""
from varillas_codex import rama


def balcon_verde(f,s,h,ancho=1.55):
    a,b=s-ancho/2,s+ancho/2;d=.50;color='#507b6c'
    f.caja(a-.06,b+.06,h-.15,h,-.025,d+.06,'piedra','#d4c7ad')
    for ss in (a,b):
        for dd in (0,d*.5,d):
            f.cilindro_vertical(ss,h,h+.95,dd,.018,'hierro',color,lados=6)
    for hh in (h+.08,h+.88,h+.94):
        rama(f.c,f.punto(a,hh,d),f.punto(b,hh,d),.019,.019,'hierro',color)
        for ss in (a,b):rama(f.c,f.punto(ss,hh,0),f.punto(ss,hh,d),.019,.019,'hierro',color)
    for j in range(3):
        ss=a+(j+.5)*ancho/3;w=ancho/6-.035
        pts=[f.punto(ss-w,h+.48,d),f.punto(ss,h+.84,d),f.punto(ss+w,h+.48,d),f.punto(ss,h+.12,d)]
        for p,q in zip(pts,pts[1:]+pts[:1]):rama(f.c,p,q,.013,.013,'hierro',color)
    for ss in (a,b):
        f.c.esfera(*f.punto(ss,h+.97,d),.035,'hierro',color,segmentos=6)
