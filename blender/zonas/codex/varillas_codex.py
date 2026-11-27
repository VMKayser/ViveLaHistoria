"""Varillas de baja carga para letras, radios y ramas de detalle."""
from mathutils import Vector


def rama(c,a,b,r0=.07,r1=.035,rol='tronco',color=None):
    """Varilla de cuatro caras, sin un operador BMesh por cada letra/radio."""
    a,b=Vector(a),Vector(b);t=b-a
    if t.length<.001:return
    t.normalize();u=t.cross(Vector((0,0,1)))
    if u.length<.01:u=t.cross(Vector((0,1,0)))
    u.normalize();v=t.cross(u);radios=(u,v,-u,-v)
    aa=[a+q*r0 for q in radios];bb=[b+q*r1 for q in radios]
    for j in range(4):c.poligono([aa[j],aa[(j+1)%4],bb[(j+1)%4],bb[j]],rol,color)
    c.poligono(list(reversed(aa)),rol,color);c.poligono(bb,rol,color)

