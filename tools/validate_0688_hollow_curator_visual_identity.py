#!/usr/bin/env python3
from pathlib import Path
import json,re,struct,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src/Cardcha'; A=SRC/'assets'; B=SRC/'Services/MilestoneBossService.cs'
VER='0.3.0-alpha.28.0.4.14.4.5.12.56'; BR='cardcha-alpha28-0688-hollow-curator-visual-identity-rebuild'
CLIPS={'idle':8,'drift':8,'observe':10,'cast':10,'page_volley':10,'mirror':10,'adapt':10,'hurt':6,'transition':12,'defeat':12}
def need(x,m):
    if not x:raise SystemExit('0688 VALIDATION FAIL: '+m)
def png_size(p):
    raw=p.read_bytes();need(raw[:8]==b'\x89PNG\r\n\x1a\n',p.name+' invalid PNG');return struct.unpack('>II',raw[16:24])
def csv_layers(p):
    r=ET.parse(p).getroot();mw=int(r.attrib.get('width','0'));mh=int(r.attrib.get('height','0'));out={}
    for l in r.findall('layer'):
        d=l.find('data')
        if d is None or d.attrib.get('encoding')!='csv':continue
        tokens=[x.strip() for x in (d.text or '').split(',')]
        need(tokens and all(tokens),f'empty CSV token {p.name}/{l.attrib.get("name")}')
        need(all(re.fullmatch(r'\d+',x) for x in tokens),f'non-uint CSV {p.name}/{l.attrib.get("name")}')
        w=int(l.attrib.get('width',mw));h=int(l.attrib.get('height',mh));need(len(tokens)==w*h,f'tile count {p.name}/{l.attrib.get("name")}')
        out[l.attrib.get('name','?')]=[int(x) for x in tokens]
    return r,out

m=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'));need(m.get('Version')==VER,'manifest version')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:need(VER in (SRC/rel).read_text(encoding='utf-8'),rel+' version')
anim=A/'bosses/milestone/hollow_curator';need(anim.is_dir(),'clip directory missing')
for name,n in CLIPS.items():
    p=anim/f'{name}.png';need(p.exists(),name+' clip missing');need(png_size(p)==(48*n,64),f'{name} dimensions {png_size(p)} != {(48*n,64)}')
need(not (A/'bosses/milestone/hollow_curator.png').exists(),'legacy 2-frame-family runtime strip still packaged')
need(png_size(A/'bosses/milestone/hollow_curator_arena_tiles.png')==(128,64),'archive architecture sheet dimensions')

src=B.read_text(encoding='utf-8')
for name in CLIPS:need(f'hollow_curator/{name}.png' in src,name+' path not wired')
need('CuratorAnimationClip(long now)' in src,'behavior animation selector missing')
need('UpdateCuratorVisualDamageState(now)' in src and 'CuratorHurtUntilMs = now + 360L' in src,'hurt feedback missing')
need('CuratorAnimationFamily' not in src and 'HollowCuratorTexturePath' not in src,'legacy two-frame selector remains')
need('CuratorVisual=' in src,'visual diagnostic missing')

b2r,b2=csv_layers(A/'boss2_hollow_curator_arena.tmx');b3r,b3=csv_layers(A/'boss3_tricolor_resonance_arena.tmx');b4r,b4=csv_layers(A/'boss4_mimi_resonance_arena.tmx')
need((int(b2r.attrib['width']),int(b2r.attrib['height']))==(28,20),'Boss II dimensions')
ts=next((x for x in b2r.findall('tileset') if x.attrib.get('name')=='HollowCuratorArchitecture'),None);need(ts is not None,'dedicated architecture tileset missing');need(ts.attrib.get('firstgid')=='1984','architecture firstgid')
for name in ['Buildings','Back','CardchaArenaGround']:need(name in b2,name+' layer missing')
fp2=[i for i,v in enumerate(b2['Buildings']) if v];fp3=[i for i,v in enumerate(b3['Buildings']) if v];fp4=[i for i,v in enumerate(b4['Buildings']) if v]
need(len(fp2)==94,'Boss II collision footprint count changed');need(fp2==fp3==fp4,'Boss II collision coordinates changed')
need(b2['Buildings']!=b3['Buildings'] and b2['Buildings']!=b4['Buildings'],'Boss II still shares Boss III/IV Buildings art')
need(all(v>=1984 for v in b2['Buildings'] if v),'Boss II Buildings still contains shared generic art GIDs')
need(sum(v>=1984 for v in b2['Back'])>=40,'Boss II Back lacks Archive-specific floor identity')
need(b3['Buildings']==b4['Buildings'],'Boss III/IV baseline unexpectedly diverged inside 0688')

# Runtime-safe CSV regression lock repository-wide.
checked=0
for p in A.rglob('*.tmx'):
    csv_layers(p);checked+=1
need(checked>=19,'expected authored TMX coverage')

# Frozen gameplay/design contracts.
need('private const int HollowCuratorMaxHealth = 2200;' in src,'2200 HP changed')
need('1 => new[] { 0, 0, 1 }' in src,'Curator phase 1 changed')
for key in ['loose_folios','iron_bindings','mirror_draft','redacted_ledger']:need(key in src,key+' Archive Rule missing')
r2=(SRC/'Services/Region2RoguelikeRunService.cs').read_text(encoding='utf-8');need('TargetNodes = 6 +' in r2,'6-9 node contract');need('mirror_trace' in r2 and 'ink_sweep' in r2 and 'warden_seal' in r2,'0684 mechanics')
need('BindCuratorArchiveRuleSink' in r2 and 'CuratorArchiveRuleSink?.Invoke' in r2,'0686 rule transfer')
latest=(ROOT/'handoff/LATEST_CARDCHA_HANDOFF.md').read_text(encoding='utf-8');need(BR in latest and VER in latest,'latest handoff')
need((ROOT/'handoff/ALPHA28_0688_HOLLOW_CURATOR_VISUAL_IDENTITY_REBUILD.md').exists(),'0688 handoff missing')
audit=(ROOT/'render_depth_audit.json').read_text(encoding='utf-8');need(BR in audit,'render audit marker');need('"physicalAllowed": false' in audit,'render physical lock')
print(f'0688 VALIDATION PASS: {len(CLIPS)} Curator clips, dedicated Boss II Archive arena, 94 collision cells preserved, {checked} TMX runtime-safe.')
