#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/Cardcha/assets'
MAP=A/'boss2_hollow_curator_arena.tmx'
SHEET=A/'bosses/milestone/hollow_curator_arena_tiles.png'
C={'bg':(29,24,45,255),'deep':(39,31,58,255),'wood':(67,51,82,255),'wood2':(83,61,96,255),'edge':(112,88,132,255),'blue':(112,132,220,255),'ice':(159,180,239,255),'violet':(153,111,199,255),'pink':(206,111,168,255),'gold':(211,180,92,255),'paper':(210,202,168,255),'ink':(52,38,76,255),'glass':(72,80,125,255),'black':(21,17,31,255)}

def need(x,m):
    if not x: raise SystemExit('0688 ARENA FAIL: '+m)

# 32 dedicated 16px tiles: archive shelves, mirrors, catalog drawers, ink, paper and record seals.
s=Image.new('RGBA',(128,64),(0,0,0,0)); d=ImageDraw.Draw(s)
def box(i,c):
    x=(i%8)*16;y=(i//8)*16;d.rectangle((x,y,x+15,y+15),fill=c);return x,y
x,y=box(0,C['wood']);d.rectangle((x,y,x+15,y+2),fill=C['edge']);d.rectangle((x,y+13,x+15,y+15),fill=C['deep'])
for xx in (2,13):d.rectangle((x+xx,y+3,x+xx+1,y+12),fill=C['deep'])
x,y=box(1,C['wood']);d.rectangle((x,y,x+15,y+2),fill=C['edge']);d.rectangle((x,y+8,x+15,y+9),fill=C['deep'])
for xx,c,h in [(2,C['blue'],5),(5,C['paper'],4),(7,C['violet'],6),(10,C['gold'],5),(13,C['ice'],4)]:d.rectangle((x+xx,y+3,x+xx+1,y+3+h),fill=c)
d.rectangle((x,y+13,x+15,y+15),fill=C['deep'])
x,y=box(2,C['wood2']);d.rectangle((x,y,x+15,y+2),fill=C['edge']);d.rectangle((x,y+8,x+15,y+9),fill=C['deep'])
for xx,c,h in [(1,C['pink'],5),(4,C['violet'],6),(7,C['paper'],4),(10,C['blue'],5),(13,C['pink'],6)]:d.rectangle((x+xx,y+3,x+xx+1,y+3+h),fill=c)
d.rectangle((x+2,y+11,x+13,y+12),fill=C['black']);d.rectangle((x,y+13,x+15,y+15),fill=C['deep'])
x,y=box(3,C['deep']);d.rectangle((x,y+9,x+15,y+15),fill=C['wood']);d.rectangle((x,y+8,x+15,y+9),fill=C['edge'])
for xx in (2,7,12):d.rectangle((x+xx,y+4,x+xx+1,y+7),fill=C['violet']);d.point((x+xx,y+3),fill=C['ice'])
x,y=box(4,C['bg']);d.rectangle((x+8,y,x+15,y+15),fill=C['wood2']);d.rectangle((x+10,y+2,x+12,y+13),fill=C['edge']);d.rectangle((x+7,y,x+15,y+2),fill=C['violet']);d.rectangle((x+7,y+13,x+15,y+15),fill=C['deep'])
x,y=box(5,C['bg']);d.rectangle((x,y,x+7,y+15),fill=C['wood2']);d.rectangle((x+3,y+2,x+5,y+13),fill=C['edge']);d.rectangle((x,y,x+8,y+2),fill=C['violet']);d.rectangle((x,y+13,x+8,y+15),fill=C['deep'])
x,y=box(6,C['deep']);d.line((x+2,y+13,x+13,y+2),fill=C['violet']);d.line((x+5,y+13,x+13,y+5),fill=C['blue']);d.rectangle((x+1,y+1,x+4,y+4),fill=C['wood2']);d.point((x+2,y+2),fill=C['gold'])
x,y=box(7,C['deep']);d.rectangle((x+2,y+2,x+13,y+13),outline=C['violet']);d.rectangle((x+4,y+4,x+11,y+11),outline=C['blue']);d.line((x+8,y+3,x+8,y+12),fill=C['gold']);d.line((x+3,y+8,x+12,y+8),fill=C['gold']);d.point((x+8,y+8),fill=C['paper'])
x,y=box(8,C['deep']);d.rectangle((x+2,y+1,x+13,y+14),fill=C['wood2']);d.rectangle((x+4,y+3,x+11,y+12),fill=C['glass']);d.rectangle((x+3,y+2,x+12,y+13),outline=C['violet']);d.line((x+5,y+4,x+10,y+4),fill=C['ice'])
x,y=box(9,C['deep']);d.rectangle((x+3,y+2,x+12,y+13),fill=C['glass']);d.line((x+5,y+4,x+10,y+9),fill=C['ice']);d.line((x+4,y+10,x+7,y+13),fill=C['blue'])
x,y=box(10,C['deep']);d.rectangle((x+3,y+2,x+12,y+13),fill=C['glass']);d.rectangle((x+2,y+1,x+13,y+14),outline=C['violet']);d.line((x+8,y+3,x+7,y+7,x+10,y+9,x+6,y+13),fill=C['ice'])
x,y=box(11,C['wood'])
for yy in (2,7,12):d.rectangle((x+2,y+yy-1,x+13,y+yy+2),fill=C['wood2']);d.rectangle((x+6,y+yy,x+9,y+yy+1),fill=C['gold'])
x,y=box(12,C['bg']);d.rectangle((x,y+6,x+15,y+10),fill=C['ink']);d.line((x,y+7,x+15,y+7),fill=C['violet'])
for xx in (3,8,13):d.point((x+xx,y+9),fill=C['pink'])
x,y=box(13,C['bg'])
for off,c in [(0,C['paper']),(2,C['ice']),(4,C['paper'])]:d.rectangle((x+3+off//2,y+9-off,x+12+off//2,y+11-off),fill=c);d.line((x+4+off//2,y+10-off,x+10+off//2,y+10-off),fill=C['wood2'])
x,y=box(14,C['bg'])
for k in range(5):
    xx=x+3+k*2;yy=y+2+k*3;d.rectangle((xx,yy,xx+2,yy+3),outline=C['edge'])
box(15,C['black'])
x,y=box(16,C['deep']);d.rectangle((x+1,y+1,x+14,y+14),outline=C['wood2']);d.line((x+8,y+2,x+8,y+13),fill=C['violet']);d.line((x+2,y+8,x+13,y+8),fill=C['violet']);d.point((x+8,y+8),fill=C['gold'])
x,y=box(17,C['deep']);d.line((x+2,y+3,x+7,y+7,x+5,y+11,x+13,y+14),fill=C['edge'])
x,y=box(18,C['deep']);d.rectangle((x+2,y+3,x+7,y+6),fill=C['paper']);d.rectangle((x+9,y+9,x+13,y+12),fill=C['ice']);d.point((x+4,y+5),fill=C['wood2']);d.point((x+11,y+11),fill=C['wood2'])
x,y=box(19,C['deep'])
for yy in (3,7,11):d.line((x+3,y+yy,x+12,y+yy),fill=C['wood2']);d.point((x+5+(yy%4),y+yy),fill=C['gold'])
x,y=box(20,C['deep']);d.rectangle((x+5,y+7,x+10,y+14),fill=C['wood2']);d.rectangle((x+3,y+13,x+12,y+15),fill=C['edge']);d.rectangle((x+6,y+4,x+9,y+7),fill=C['gold'])
x,y=box(21,C['deep']);d.rectangle((x+7,y+7,x+8,y+13),fill=C['paper']);d.point((x+7,y+6),fill=C['gold']);d.point((x+8,y+5),fill=C['pink']);d.rectangle((x+5,y+13,x+10,y+14),fill=C['wood2'])
x,y=box(22,C['bg']);d.arc((x+1,y+1,x+14,y+16),180,360,fill=C['edge'],width=3);d.arc((x+4,y+4,x+11,y+14),180,360,fill=C['violet'])
x,y=box(23,C['bg']);d.rectangle((x+2,y,x+5,y+15),fill=C['wood2']);d.rectangle((x+3,y+2,x+4,y+13),fill=C['edge']);d.point((x+4,y+4),fill=C['violet']);d.point((x+4,y+10),fill=C['violet'])
x,y=box(24,C['deep']);d.rectangle((x+3,y+10,x+12,y+12),fill=C['blue']);d.rectangle((x+5,y+7,x+13,y+9),fill=C['pink']);d.rectangle((x+2,y+4,x+10,y+6),fill=C['paper'])
x,y=box(25,C['deep']);d.rectangle((x+4,y+4,x+11,y+12),fill=C['paper']);d.line((x+5,y+6,x+10,y+6),fill=C['wood2']);d.line((x+5,y+9,x+9,y+9),fill=C['wood2'])
x,y=box(26,C['deep']);d.rectangle((x+4,y+11,x+8,y+14),fill=C['ink']);d.line((x+7,y+11,x+12,y+3),fill=C['paper']);d.point((x+12,y+3),fill=C['ice'])
x,y=box(27,C['deep']);d.polygon([(x+3,y+3),(x+8,y+5),(x+5,y+10)],fill=C['glass']);d.polygon([(x+10,y+7),(x+14,y+10),(x+9,y+14)],fill=C['blue']);d.line((x+3,y+3,x+8,y+5),fill=C['ice'])
x,y=box(28,C['deep']);d.rectangle((x+2,y+5,x+13,y+7),fill=C['pink']);d.rectangle((x+5,y+10,x+14,y+12),fill=C['ink'])
x,y=box(29,C['deep']);d.polygon([(x+2,y+8),(x+8,y+4),(x+14,y+8),(x+8,y+12)],outline=C['violet']);d.rectangle((x+7,y+7,x+9,y+9),fill=C['gold'])
x,y=box(30,C['deep']);d.arc((x+1,y+1,x+21,y+21),180,270,fill=C['violet'],width=2);d.point((x+4,y+11),fill=C['gold'])
x,y=box(31,C['deep']);d.ellipse((x+2,y+2,x+13,y+13),outline=C['violet']);d.rectangle((x+6,y+6,x+9,y+9),outline=C['gold']);d.point((x+8,y+8),fill=C['paper'])
s.save(SHEET,optimize=True)

# Map separation. Re-running on a materialized map is harmless.
t=ET.parse(MAP);r=t.getroot();w=int(r.attrib['width']);h=int(r.attrib['height']);need((w,h)==(28,20),'unexpected map size')
for q in list(r.findall('tileset')):
    if q.attrib.get('name')=='HollowCuratorArchitecture':r.remove(q)
children=list(r);last=max(i for i,c in enumerate(children) if c.tag=='tileset');q=ET.Element('tileset',{'firstgid':'1984','name':'HollowCuratorArchitecture','tilewidth':'16','tileheight':'16','tilecount':'32','columns':'8'});ET.SubElement(q,'image',{'source':'bosses/milestone/hollow_curator_arena_tiles.png','width':'128','height':'64'});r.insert(last+1,q)
def layer(n):
    q=next(x for x in r.findall('layer') if x.attrib.get('name')==n);dta=q.find('data');v=[int(x.strip()) for x in (dta.text or '').split(',') if x.strip()];need(len(v)==w*h,n+' count');return dta,v
g=lambda x:1984+x
bd,b=layer('Buildings');foot=[i for i,v in enumerate(b) if v];nb=[0]*(w*h)
for y in range(h):
    for x in range(w):
        i=y*w+x
        if not b[i]:continue
        if y==0:z=6 if x in (0,w-1) else 3 if x in (1,6,11,16,21,26) else 1 if x%3 else 2
        elif y==h-1:z=6 if x in (0,w-1) else 0 if x%3 else 11
        elif x==0:z=4 if y%5==0 else 23
        elif x==w-1:z=5 if y%5==0 else 23
        elif (x,y)==(5,5):z=8
        elif (x,y)==(22,5):z=10
        elif (x,y)==(5,14):z=11
        elif (x,y)==(22,14):z=7
        else:z=0
        nb[i]=g(z)
need([i for i,v in enumerate(nb) if v]==foot,'collision footprint changed');bd.text='\n'+','.join(map(str,nb))+'\n'
bkd,bk=layer('Back')
for x in range(2,w-2):
    if x%2==0:bk[2*w+x]=g(19 if x%4==0 else 17);bk[17*w+x]=g(18 if x%4==0 else 28)
for y in range(3,h-3):
    if y%3==0:bk[y*w+2]=g(25 if y%2 else 24);bk[y*w+w-3]=g(27 if y%2 else 26)
cx,cy=14,10;pat={(-2,-2):30,(2,-2):30,(-2,2):30,(2,2):30,(0,-2):29,(-2,0):29,(2,0):29,(0,2):29,(-1,-1):16,(0,-1):28,(1,-1):16,(-1,0):28,(0,0):31,(1,0):28,(-1,1):16,(0,1):28,(1,1):16}
for (dx,dy),z in pat.items():bk[(cy+dy)*w+cx+dx]=g(z)
for x,y,z in [(7,6,27),(8,7,18),(20,6,27),(19,7,18),(7,13,25),(8,12,18),(20,13,25),(19,12,18)]:bk[y*w+x]=g(z)
bkd.text='\n'+','.join(map(str,bk))+'\n'
gd,gv=layer('CardchaArenaGround')
for j,(x,y) in enumerate([(11,8),(12,7),(14,7),(16,7),(17,8),(17,11),(16,12),(14,13),(12,12),(11,11)]):gv[y*w+x]=1976+j%8
gd.text='\n'+','.join(map(str,gv))+'\n'
ET.indent(t,space='  ');t.write(MAP,encoding='utf-8',xml_declaration=True,short_empty_elements=True)
print('0688 Boss II arena identity materialized: dedicated Archive architecture, unchanged collision footprint.')
