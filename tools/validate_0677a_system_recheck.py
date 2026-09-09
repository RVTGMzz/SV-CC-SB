#!/usr/bin/env python3
from pathlib import Path
import json, re, xml.etree.ElementTree as ET

ROOT=Path('src/Cardcha')
V='0.3.0-alpha.28.0.4.14.4.5.12.45.3.1'

def need(cond,msg):
    if not cond: raise SystemExit('0677A RECHECK FAIL: '+msg)

manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (ROOT/rel).read_text(encoding='utf-8'),f'{rel} version mismatch')

a=(ROOT/'Services/AirshipFoundationService.cs').read_text(encoding='utf-8')
start=a.index('public void OnRenderedWorld')
end=a.index('public void OnButtonPressed',start)
render=a[start:end]
need('EnsureDeckVanillaFurniture' not in render,'RenderedWorld still mutates deck furniture')
need('EnsureSkyDockVanillaFurniture' not in render,'RenderedWorld still mutates dock furniture')
warp=a[a.index('public void OnWarped'):a.index('/// <summary>TEST-only warp',a.index('public void OnWarped'))]
need('EnsureDeckVanillaFurniture(e.NewLocation)' in warp,'deck decor not ensured on warp')
need('EnsureSkyDockVanillaFurniture(e.NewLocation)' in warp,'dock decor not ensured on warp')
for bad in [
    '"(F)1120", 3, 7', '"(F)704", 6, 10',
    '"(F)1132", 18, 7', '"(F)1132", 15, 10']:
    need(bad not in a,'unsafe upgrade-socket-adjacent furniture returned: '+bad)
need('kept Airship furniture' in a and 'skipped held decor' in a,'held-decor nonfatal guard missing')
need('NativeDecor=Bridge:' in a and 'LostFound:' in a,'airship native-decor telemetry missing')

# Interaction anchors must remain exact and open.
for token in ['new Point(4, 8)','new Point(19, 8)','new Point(7, 11)','new Point(16, 11)',
              'ResolveSkyDockInteriorRouteTile','ResolveSkyDockInteriorBayTile','ResolveSkyDockLostFoundTile']:
    need(token in a,'interaction anchor missing: '+token)

# Known runtime Harmony crash regression guards.
vp=(ROOT/'Patches/VerdantGuardianProxyDrawPatch.cs').read_text(encoding='utf-8')
rp=(ROOT/'Patches/RegionExpeditionProxyDrawPatch.cs').read_text(encoding='utf-8')
for text,name in [(vp,'Verdant'),(rp,'Expedition')]:
    need('AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) })' in text,name+' Monster.draw declaration guard missing')
need('typeof(GreenSlime)' not in rp and 'typeof(Bat)' not in rp and 'typeof(Bug)' not in rp,'subclass draw patch regression')

# Test commands and route contracts still exist.
mod=(ROOT/'ModEntry.cs').read_text(encoding='utf-8')
for cmd in ['cardcha_test_airship','cardcha_test_gate','cardcha_test_boss1','cardcha_test_boss2','cardcha_test_boss3','cardcha_test_boss4','cardcha_test_region3','cardcha_test_region4','cardcha_expedition_clear']:
    need(f'"{cmd}"' in mod,'missing test command '+cmd)
mb=(ROOT/'Services/MilestoneBossService.cs').read_text(encoding='utf-8')
for token in ['MirrorArchiveBossCardId = "mirror_archive"','TricolorBossCardId = "tricolor_resonance"','MimiBossCardId = "mimis_resonance"','RouteConfirmWindowMs = 5000L']:
    need(token in mb,'milestone route/reward contract missing: '+token)
need(all(x in mb for x in ['40','60','80']),'40/60/80 milestone tokens missing')
rexp=(ROOT/'Services/RegionExpeditionService.cs').read_text(encoding='utf-8')
for token in ['private const int WaveCount = 3','ExtractConfirmWindowMs = 5000L','Region3LocationName','Region4LocationName']:
    need(token in rexp,'expedition contract missing: '+token)

# Strict TMX CSV integrity for the four currently touched/critical route maps.
for name in ['airship_deck.tmx','sky_dock_interior.tmx','region3_mirrorwild.tmx','region4_resonance_verge.tmx']:
    p=ROOT/'assets'/name
    tree=ET.parse(p); m=tree.getroot(); w=int(m.attrib['width']); h=int(m.attrib['height'])
    for layer in m.findall('layer'):
        d=layer.find('data')
        if d is None or d.attrib.get('encoding')!='csv': continue
        vals=[x.strip() for x in (d.text or '').replace('\n','').split(',') if x.strip()]
        need(len(vals)==w*h,f'{name}:{layer.attrib.get("name")} has {len(vals)} cells, expected {w*h}')

# Frozen save/card contracts. cards.json uses PascalCase model property names.
save=(ROOT/'Services/SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((ROOT/'assets/cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,f'cards.json expected 80 entries, got {len(cards)}')
legacy={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
ids={str(c.get('Id','')) for c in cards}
need('' not in ids,'cards.json contains entry without Id')
need(len(ids)==80,f'cards.json expected 80 unique Id values, got {len(ids)}')
need(legacy.issubset(ids),'legacy mythic IDs missing')
need(len(ids-legacy)==76,f'expected 76 normal card IDs, got {len(ids-legacy)}')

print('0677A system recheck PASS: lifecycle, depth, Harmony, route, expedition, TMX, schema and card contracts intact.')
