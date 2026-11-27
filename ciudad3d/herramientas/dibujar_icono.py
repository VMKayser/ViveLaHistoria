from PIL import Image, ImageDraw
import sys
MARFIL=(244,234,214);TEJA=(192,98,63);ORO=(201,164,92);SOMBRA=(214,198,168);V1=(47,74,62);V2=(24,40,33)
def torre(d,cx,base,alto,ancho,con_det=True):
    """Campanario: cuerpo en tres cuerpos, vanos con arco, reloj, chapitel piramidal de teja y aguja."""
    u=alto/100.0
    w=ancho
    y=base
    # basamento
    d.rectangle([cx-w*.62,y-8*u,cx+w*.62,y],fill=MARFIL); y-=8*u
    d.rectangle([cx-w*.56,y-30*u,cx+w*.56,y],fill=MARFIL); c1=y; y-=30*u
    d.rectangle([cx-w*.62,y-3*u,cx+w*.62,y],fill=SOMBRA); y-=3*u
    d.rectangle([cx-w*.50,y-24*u,cx+w*.50,y],fill=MARFIL); c2=y; y-=24*u
    d.rectangle([cx-w*.58,y-3*u,cx+w*.58,y],fill=SOMBRA); y-=3*u
    d.rectangle([cx-w*.46,y-12*u,cx+w*.46,y],fill=MARFIL); c3=y; y-=12*u
    d.rectangle([cx-w*.56,y-2.5*u,cx+w*.56,y],fill=SOMBRA); y-=2.5*u
    # chapitel
    d.polygon([(cx-w*.50,y),(cx+w*.50,y),(cx,y-17*u)],fill=TEJA)
    d.rectangle([cx-.012*alto,y-27*u,cx+.012*alto,y-16*u],fill=ORO)
    d.rectangle([cx-.035*alto,y-22*u,cx+.035*alto,y-21*u],fill=ORO)
    for s in(-1,1): d.polygon([(cx+s*w*.50,y),(cx+s*w*.42,y),(cx+s*w*.46,y-7*u)],fill=TEJA)
    if con_det:
        r=w*.17; cy=c1-15*u
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=V2); d.ellipse([cx-r*.8,cy-r*.8,cx+r*.8,cy+r*.8],fill=MARFIL)
        d.line([cx,cy,cx,cy-r*.6],fill=V2,width=max(2,int(u*.9))); d.line([cx,cy,cx+r*.45,cy],fill=V2,width=max(2,int(u*.9)))
        for yy,hh,ww in ((c2,19*u,w*.2),(c3,9*u,w*.14)):
            for s in(-1,1) if yy==c2 else (0,):
                x=cx+s*w*.22; top=yy-hh
                d.rectangle([x-ww/2,top+ww/2,x+ww/2,yy-2*u],fill=V2)
                d.pieslice([x-ww/2,top,x+ww/2,top+ww],180,360,fill=V2)
def render(S=1024,fondo=True,caja=.60,solo_torre=False,mono=False):
    k=4; N=S*k
    im=Image.new("RGBA",(N,N),(0,0,0,0)); d=ImageDraw.Draw(im)
    if fondo:
        g=Image.new("RGBA",(1,N)); 
        for i in range(N):
            t=i/N; g.putpixel((0,i),tuple(int(V1[j]*(1-t)+V2[j]*t) for j in range(3))+(255,))
        g=g.resize((N,N))
        m=Image.new("L",(N,N),0); ImageDraw.Draw(m).rounded_rectangle([0,0,N-1,N-1],radius=int(N*.22),fill=255)
        im.paste(g,(0,0),m); d=ImageDraw.Draw(im)
        # colina suave y línea dorada
        d.ellipse([-N*.25,N*.80,N*1.25,N*1.9],fill=(18,31,26,255))
        d.arc([-N*.25,N*.80,N*1.25,N*1.9],200,340,fill=ORO+(255,),width=int(N*.006))
    if mono:
        im=Image.new("RGBA",(N,N),(0,0,0,0)); d=ImageDraw.Draw(im)
    alto=N*caja
    base=N*.5+alto/2+(N*.02 if fondo else 0)
    torre(d,N/2,base,alto,N*.17*(caja/.6))
    if mono:
        # monocromo: todo en blanco
        a=im.split()[3]; im=Image.new("RGBA",(N,N),(255,255,255,0)); im.putalpha(a)
    return im.resize((S,S),Image.LANCZOS)
if __name__=="__main__":
    out=sys.argv[1]
    render(1024).save(out+"/icono_1024.png")
    render(432,fondo=False,caja=.46).save(out+"/fg_432.png")
    render(432,fondo=False,caja=.46,mono=True).save(out+"/mono_432.png")
    Image.new("RGBA",(432,432),V1+(255,)).save(out+"/bg_432.png")
