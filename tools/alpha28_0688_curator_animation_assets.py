#!/usr/bin/env python3
from pathlib import Path
import math
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/Cardcha/assets/bosses/milestone'
OLD=A/'hollow_curator.png'
OUT=A/'hollow_curator'
OUT.mkdir(parents=True,exist_ok=True)
if not OLD.exists():
    required=[OUT/f'{n}.png' for n in ['idle','drift','observe','cast','page_volley','mirror','adapt','hurt','transition','defeat']]
    if all(p.exists() for p in required):
        print('0688 Curator animation assets already materialized.')
        raise SystemExit(0)
    raise SystemExit('0688 ANIM FAIL: legacy source missing and clips incomplete')
src=Image.open(OLD).convert('RGBA')
if src.size!=(864,64): raise SystemExit(f'0688 ANIM FAIL: unexpected source size {src.size}')
F=[src.crop((i*48,0,(i+1)*48,64)) for i in range(18)]
P={'blue':(142,164,255,255),'ice':(190,208,255,255),'violet':(188,140,255,255),'pink':(238,139,219,255),'dark':(34,27,58,255),'paper':(220,213,179,255),'gold':(232,207,106,255),'red':(221,107,145,255),'green':(133,222,177,255),'white':(244,244,255,255),'cyan':(139,229,238,255)}

def tint(im,c,a):
    o=im.copy(); q=o.load(); cr,cg,cb,_=c
    for y in range(o.height):
        for x in range(o.width):
            r,g,b,z=q[x,y]
            if z:q[x,y]=(int(r*(1-a)+cr*a),int(g*(1-a)+cg*a),int(b*(1-a)+cb*a),z)
    return o

def pose(i,dx=0,dy=0,c=None,a=0,opacity=255):
    o=Image.new('RGBA',(48,64),(0,0,0,0)); p=F[i].copy()
    if c is not None and a:p=tint(p,c,a)
    if opacity!=255:p.putalpha(p.getchannel('A').point(lambda v:v*opacity//255))
    o.alpha_composite(p,(dx,dy)); return o

def diamond(d,x,y,c,s=1):
    for yy in range(-s,s+1):
        h=s-abs(yy); d.line((x-h,y+yy,x+h,y+yy),fill=c)

def page(d,x,y,c=None,o=0):
    c=c or P['ice']; edge=(82,93,162,255)
    if o%2==0:
        d.rectangle((x,y,x+3,y+4),fill=edge); d.rectangle((x+1,y+1,x+2,y+3),fill=c)
    else:
        d.rectangle((x,y,x+4,y+3),fill=edge); d.rectangle((x+1,y+1,x+3,y+2),fill=c)

def cross(d,x,y,c):
    d.line((x-2,y,x+2,y),fill=c); d.line((x,y-2,x,y+2),fill=c); d.point((x,y),fill=P['white'])

def idle(i,n):
    f=pose(i%2,dy=[1,0,-1,-2,-1,0,1,0][i]); d=ImageDraw.Draw(f); x,y=[(5,16),(8,11),(12,7),(34,8),(38,12),(40,17),(37,22),(8,22)][i]; page(d,x,y,P['ice'],i)
    if i in (2,3,4):diamond(d,24,5,P['blue'])
    return f

def drift(i,n):
    f=pose(2+i%2,dx=[0,1,2,2,1,0,-1,-1][i],dy=[0,-1,-1,0,1,1,0,-1][i],c=P['blue'],a=.08); d=ImageDraw.Draw(f)
    for k in range(3):page(d,(6+i*4-k*7)%42,14+k*9+((i+k)%3),P['paper'],i+k)
    return f

def observe(i,n):
    f=pose(4+i%2,dy=-1 if i in (3,4,5) else 0,c=P['red'],a=.10); d=ImageDraw.Draw(f)
    if i>=2:w=min(8,i); d.line((24-w,5,24+w,5),fill=P['pink']); d.point((24,5),fill=P['white'])
    if i>=4:d.line((5,43,11,35),fill=P['gold']); d.line((42,43,36,35),fill=P['gold'])
    return f

def cast(i,n):
    f=pose(8+i%2,dy=[1,0,-1,-2,-2,-1,0,1,0,-1][i],c=P['pink'],a=.10); d=ImageDraw.Draw(f); s=min(10,2+i); y=42+i%2
    d.rectangle((max(0,14-s),y,max(0,20-s),y+2),fill=P['red']); d.rectangle((min(47,28+s),y,min(47,34+s),y+2),fill=P['red'])
    if i>=3:cross(d,24,7,P['pink'])
    return f

def volley(i,n):
    f=pose(12+i%2,dy=-1 if i%4 in (1,2) else 0,c=P['ice'],a=.07); d=ImageDraw.Draw(f); t=i/(n-1)
    pts=[(int(18-16*t),int(20-9*t)),(int(30+14*t),int(18-7*t)),(int(16-15*t),int(38+7*t)),(int(32+13*t),int(38+6*t))]
    for k,(x,y) in enumerate(pts):page(d,max(0,min(43,x)),max(0,min(59,y)),P['ice'],i+k)
    if i in (4,5,6):diamond(d,24,10,P['white'])
    return f

def mirror(i,n):
    j=14+i%2; f=Image.new('RGBA',(48,64),(0,0,0,0)); f.alpha_composite(pose(j,dx=5 if i<5 else -5,c=P['violet'],a=.65,opacity=55+10*(i%3))); f.alpha_composite(pose(j,dy=-1 if i in (4,5) else 0)); d=ImageDraw.Draw(f); d.line((24,2,24,12),fill=(152,120,215,180))
    for k,y in enumerate((8,18,30,44)):
        if (i+k)%3==0:diamond(d,5 if k%2==0 else 42,y,P['violet'])
    return f

def adapt(i,n):
    f=pose(10+i%2,dy=[0,-1,-2,-1,0,1,0,-1,-2,-1][i],c=P['green'],a=.12); d=ImageDraw.Draw(f); pts=[(24,5),(34,9),(40,18),(39,30),(9,30),(7,18),(14,9),(24,7)]
    for x,y in pts[:min(len(pts),2+i)]:cross(d,x,y,P['green'] if i%2==0 else P['cyan'])
    return f

def hurt(i,n):
    f=pose(16+i%2,dx=[0,-2,2,-1,1,0][i],c=P['white'] if i in (1,2) else P['red'],a=.38 if i in (1,2) else .12); d=ImageDraw.Draw(f)
    for k in range(4):
        x=(6+i*7+k*9)%44; y=13+k*10; d.line((x,y,x+2,y-2),fill=P['white'] if i<3 else P['red'])
    return f

def transition(i,n):
    fam=[0,0,1,2,3,4,5,6,7,7,7,7][i]; f=pose(fam*2+i%2,dy=-min(3,i//4),c=P['violet'],a=min(.22,i*.018)); d=ImageDraw.Draw(f); r=min(20,4+i*2)
    for a in (0,math.pi/2,math.pi,3*math.pi/2):
        x=int(24+math.cos(a+i*.15)*min(19,r)); y=int(28+math.sin(a+i*.15)*min(19,r)*.75); diamond(d,max(2,min(45,x)),max(3,min(59,y)),P['violet'])
    if i>=7:d.line((8,57,16,49),fill=P['violet']); d.line((40,57,32,49),fill=P['violet'])
    return f

def defeat(i,n):
    f=pose(16+i%2,dy=min(8,i//2),c=P['dark'],a=min(.45,i*.035),opacity=max(55,255-i*17)); d=ImageDraw.Draw(f)
    for k in range(5):
        x=(8+k*8+(i*(k+1))//2)%44; y=max(2,48-k*7-i*3)
        if y<60:
            if k%2:page(d,x,y,P['paper'],i+k)
            else:diamond(d,x,y,P['violet'])
    return f

for name,n,fn in [('idle',8,idle),('drift',8,drift),('observe',10,observe),('cast',10,cast),('page_volley',10,volley),('mirror',10,mirror),('adapt',10,adapt),('hurt',6,hurt),('transition',12,transition),('defeat',12,defeat)]:
    strip=Image.new('RGBA',(48*n,64),(0,0,0,0))
    for i in range(n):strip.alpha_composite(fn(i,n),(i*48,0))
    strip.save(OUT/f'{name}.png',optimize=True)
OLD.unlink()
print('0688 Curator animation library: 10 behavior clips materialized; legacy 2-frame-family strip removed.')
