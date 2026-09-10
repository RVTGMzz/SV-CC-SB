#!/usr/bin/env python3
from pathlib import Path
import json, re, xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'
V='0.3.0-alpha.28.0.4.14.4.5.12.46'

def need(cond,msg):
    if not cond: raise SystemExit('0678 VALIDATION FAIL: '+msg)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'),rel+' version mismatch')

mod=(SRC/'ModEntry.cs').read_text(encoding='utf-8')
need('MilestoneBossActorDrawPatch.Apply(harmony, this.MilestoneBosses, this.Monitor);' in mod,'Milestone boss actor patch not wired')
for cmd in ['cardcha_test_boss2','cardcha_test_boss3','cardcha_test_boss4','cardcha_boss_milestone_status']:
    need(f'"{cmd}"' in mod,'missing test command '+cmd)

patch=(SRC/'Patches'/'MilestoneBossActorDrawPatch.cs').read_text(encoding='utf-8')
need('AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) })' in patch,'declared Monster.draw guard missing')
need('priority = Priority.First' in patch,'boss draw patch priority guard missing')
need('MilestoneBossService.BossMarkerKey' in patch and 'DrawActorAtMonsterDepth' in patch,'boss actor routing missing')

verdant=(SRC/'Patches'/'VerdantGuardianProxyDrawPatch.cs').read_text(encoding='utf-8')
need('MilestoneBossService.BossMarkerKey' not in verdant,'Verdant patch still swallows milestone actors')

svc=(SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
rw=svc[svc.index('public void OnRenderedWorld'):svc.index('public void OnRenderedHud')]
need('DrawActor(' not in rw and 'DrawActorAtMonsterDepth' not in rw,'boss physical body still drawn from RenderedWorld')
need('DrawArenaIdentity' not in rw,'arena physical props still drawn from RenderedWorld')
need('DrawBossAuraVfx' in rw and 'DrawAttackTelegraph' in rw,'VFX-only RenderedWorld path missing')
need('private void DrawArenaIdentity' not in svc,'legacy post-world arena renderer still exists')
actor=svc[svc.index('internal void DrawActorAtMonsterDepth'):svc.index('private void DrawBossAuraVfx')]
need('actor.getStandingY() / 10000f' in actor,'actor standing-Y depth missing')
need('0.99f' not in actor and '0.985f' not in actor,'fixed top-layer depth returned')
for scale in ['scale = 1.95f','scale = 1.85f','scale = 1.80f']:
    need(scale in actor,'expected native-ish boss scale missing: '+scale)

# Gameplay identity and balance remain frozen.
for token in [
    'HollowCuratorMaxHealth = 2200','TricolorGuardianMaxHealth = 780','TricolorUnifiedMaxHealth = 1650','MimiMaxHealth = 3600',
    'MirrorArchiveBossCardId = "mirror_archive"','TricolorBossCardId = "tricolor_resonance"','MimiBossCardId = "mimis_resonance"',
    'RouteConfirmWindowMs = 5000L']:
    need(token in svc,'gameplay contract changed: '+token)
need(all(x in svc for x in ['40','60','80']),'40/60/80 milestone route tokens missing')

bossdir=SRC/'assets'/'bosses'/'milestone'
expected={
    'hollow_curator.png':(192,64),
    'tricolor_guardians.png':(288,48),
    'tricolor_unified.png':(256,64),
    'mimi_resonance_master.png':(256,64),
    'hollow_curator_ground_tiles.png':(128,16),
    'tricolor_ground_tiles.png':(128,16),
    'mimi_ground_tiles.png':(128,16),
}
for name,size in expected.items():
    p=bossdir/name
    need(p.exists(),name+' missing')
    with Image.open(p) as im: need(im.size==size,f'{name} size {im.size} != {size}')

maps={
    'boss2_hollow_curator_arena.tmx':'bosses/milestone/hollow_curator_ground_tiles.png',
    'boss3_tricolor_resonance_arena.tmx':'bosses/milestone/tricolor_ground_tiles.png',
    'boss4_mimi_resonance_arena.tmx':'bosses/milestone/mimi_ground_tiles.png',
}
for name,source in maps.items():
    p=SRC/'assets'/name; tree=ET.parse(p); root=tree.getroot(); w=int(root.attrib['width']); h=int(root.attrib['height'])
    sheets=[ts.find('image').attrib.get('source') for ts in root.findall('tileset') if ts.find('image') is not None]
    need(source in sheets,f'{name}: authored ground tileset missing')
    ground=next((l for l in root.findall('layer') if l.attrib.get('name')=='CardchaArenaGround'),None)
    need(ground is not None,f'{name}: CardchaArenaGround missing')
    data=ground.find('data'); vals=[x.strip() for x in (data.text or '').replace('\n','').split(',') if x.strip()]
    need(len(vals)==w*h,f'{name}: ground CSV {len(vals)} != {w*h}')
    need(sum(1 for x in vals if int(x)>0)>=10,f'{name}: authored ground identity too sparse')
    # strict CSV for every layer in each boss arena
    for layer in root.findall('layer'):
        d=layer.find('data')
        if d is None or d.attrib.get('encoding')!='csv': continue
        lv=[x.strip() for x in (d.text or '').replace('\n','').split(',') if x.strip()]
        need(len(lv)==w*h,f'{name}:{layer.attrib.get("name")} CSV {len(lv)} != {w*h}')

save=(SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,f'cards.json expected 80 entries, got {len(cards)}')
ids={str(c.get('Id','')) for c in cards}
legacy={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
need(len(ids)==80,'card IDs are not unique')
need(legacy.issubset(ids),'legacy mythic IDs missing')
need(len(ids-legacy)==76,'active-normal card contract not 76')

print('0678 validation PASS: Boss II-IV actor-depth visuals, arena TMX identity, gameplay and save/card contracts intact.')
