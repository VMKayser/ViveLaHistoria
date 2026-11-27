"""Luminarias fotografiadas: cápsula de calle y globos dobles de la plaza."""
from kit import Constructor,altura_suelo
from piezas_codex import cable_curvo


def farol_curvo(nombre,x,y,col,direccion=(1,0),alto=4.6):
    c=Constructor(nombre);z=altura_suelo(x,y);dx,dy=direccion
    c.cilindro(x,y,z,z+alto,.045,'hierro',lados=8)
    q=(x+dx*.8,y+dy*.8,z+alto-.2)
    cable_curvo(c,(x,y,z+alto-.15),q,flecha=-.32,radio=.025,segmentos=10)
    c.cilindro(q[0],q[1],q[2]-.18,q[2]-.04,.28,'hierro',lados=12,radio_arriba=.07)
    c.esfera(q[0],q[1],q[2]-.23,.18,'vidrio','#cbc6b5',segmentos=12)
    return c.objeto(col)


def farol_globos(nombre,x,y,col,alto=5.8):
    c=Constructor(nombre);z=altura_suelo(x,y)
    c.cilindro(x,y,z,z+.15,.17,'hierro','#435048',lados=8)
    c.cilindro(x,y,z+.15,z+alto,.045,'hierro','#435048',lados=8)
    c.esfera(x,y,z+alto,.065,'hierro','#435048',segmentos=8)
    for signo,h in ((1,alto-.4),(-1,alto-1.2)):
        q=(x+signo*.55,y,z+h)
        cable_curvo(c,(x,y,z+h),q,flecha=-.2,radio=.022,segmentos=8)
        c.cilindro(q[0],q[1],q[2]-.08,q[2]+.04,.24,'hierro','#435048',lados=10,radio_arriba=.06)
        c.esfera(q[0],q[1],q[2]-.21,.23,'vidrio','#d4d1c0',segmentos=12)
    return c.objeto(col)
