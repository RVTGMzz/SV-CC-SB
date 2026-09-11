#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, re, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src/Cardcha'
VERSION='0.3.0-alpha.28.0.4.14.4.5.12.57'
BRANCH='cardcha-alpha28-0690-airship-interior-visual-rebuild'

def need(cond,msg):
    if not cond: raise SystemExit('0690 validation FAIL: '+msg)

def text(p): return p.read_text(encoding='utf-8')

manifest=json.loads(text(SRC/'manifest.json'))
need(manifest.get('Version')==VERSION,'manifest version')
need(VERSION in text(SRC/'Cardcha.csproj'),'csproj version')
need(VERSION in text(SRC/'Directory.Build.targets'),'Directory.Build.targets version')

asset=SRC/'assets/airship_props/set01_redux'
expected={
 'route_notice_board.png':(80,80),
 'boarding_gate_arch.png':(112,96),
 'signal_lamp.png':(32,48),
 'cargo_parcel_crate.png':(48,48),
 'observation_window_base.png':(160,80),
 'navigation_console_base.png':(112,80),
 'collision_blocker.png':(16,16),
}
for i in range(1,5):
 expected[f'observation_window_overlay_{i}.png']=(160,80)
 expected[f'navigation_console_overlay_{i}.png']=(112,80)
for name,size in expected.items():
 p=asset/name
 need(p.exists() and p.stat().st_size>50,f'missing asset {name}')
 need(Image.open(p).size==size,f'{name} size {Image.open(p).size} != {size}')
for name in [f'observation_window_overlay_{i}.png' for i in range(1,5)]:
 im=Image.open(asset/name).convert('RGBA')
 need(im.getchannel('A').getbbox() is not None,f'{name} empty')
for name in [f'navigation_console_overlay_{i}.png' for i in range(1,5)]:
 im=Image.open(asset/name).convert('RGBA')
 need(im.getchannel('A').getbbox() is not None,f'{name} empty')

def map_audit(path, wh, required_tilesets):
 root=ET.parse(path).getroot()
 need((int(root.attrib['width']),int(root.attrib['height']))==wh,f'{path.name} dimensions')
 names={ts.attrib.get('name'):int(ts.attrib['firstgid']) for ts in root.findall('tileset')}
 for name,gid in required_tilesets.items(): need(names.get(name)==gid,f'{path.name} tileset {name}')
 layers={}
 for l in root.findall('layer'):
  d=l.find('data')
  if d is None or d.attrib.get('encoding')!='csv': continue
  toks=[x.strip() for x in (d.text or '').split(',')]
  need(toks and all(toks),f'{path.name}/{l.attrib.get("name")} empty CSV token')
  vals=[int(x) for x in toks]
  need(len(vals)==wh[0]*wh[1],f'{path.name}/{l.attrib.get("name")} tile count')
  layers[l.attrib['name']]=vals
 return layers

dock=map_audit(SRC/'assets/sky_dock_interior.tmx',(30,18),{
 'CardchaRouteNoticeBoard0690':5000,'CardchaBoardingGate0690':5100,
 'CardchaSignalLamp0690':5200,'CardchaCargoCrate0690':5300,'CardchaCollision0690':5400})
need(any(5000<=v<5025 for v in dock['BackDecor']),'dock route board not placed')
need(any(5100<=v<5142 for v in dock['BackDecor']),'dock gate not placed')
need(any(5300<=v<5309 for v in dock['BackDecor']),'dock cargo not placed')
w=30
for x,y in [(7,7),(23,8),(15,16),(15,14)]: need(dock['Buildings'][y*w+x]!=5400,f'dock critical tile blocked {x},{y}')

deck=map_audit(SRC/'assets/airship_deck.tmx',(24,14),{
 'CardchaObservationWindow0690':5000,'CardchaNavigationConsole0690':5100,
 'CardchaSignalLamp0690':5200,'CardchaCollision0690':5400})
need(any(5000<=v<5050 for v in deck['BackDecor']),'deck window not placed')
need(any(5100<=v<5135 for v in deck['BackDecor']),'deck console not placed')
w=24
for x,y in [(12,6),(12,12),(12,10)]: need(deck['Buildings'][y*w+x]!=5400,f'deck critical tile blocked {x},{y}')

service=text(SRC/'Services/AirshipFoundationService.cs')
bridge=re.search(r'private void EnsureDeckVanillaFurniture\(GameLocation deck\)(.*?)private void EnsureSkyDockVanillaFurniture',service,re.S)
dock_fn=re.search(r'private void EnsureSkyDockVanillaFurniture\(GameLocation dock\)(.*?)private static void ClearInteriorDecor',service,re.S)
need(bridge and 'TryAddInteriorFurniture' not in bridge.group(1),'bridge vanilla clutter still active')
need(dock_fn and 'TryAddInteriorFurniture' not in dock_fn.group(1),'dock vanilla clutter still active')
need('-0690-bridge' in bridge.group(1) and '-0690-dock' in dock_fn.group(1),'0690 decor markers')

renderer=text(SRC/'Services/AirshipInteriorStardewRenderer.cs')
for token in ['Draw0690WindowOverlay(batch)','Draw0690ConsoleOverlay(batch)','observation_window_overlay_1.png','navigation_console_overlay_4.png']:
 need(token in renderer,f'renderer missing {token}')
trydeck=renderer[renderer.index('public static bool TryDrawDeck'):renderer.index('public static bool TryDrawSkyDock')]
need('DrawDeckStardewDecor(' not in trydeck,'post-world physical deck decor re-enabled')
trysky=renderer[renderer.index('public static bool TryDrawSkyDock'):renderer.index('private static void DrawDeckStardewDecor')]
need('DrawDockStardewDecor(' not in trysky,'post-world physical dock decor re-enabled')

audit=json.loads(text(ROOT/'render_depth_audit.json'))
need(audit.get('branch')==BRANCH,'render audit branch')
need('0690 Airship Set01 physical props->TMX; window/console motion->VFX-only overlays' in audit.get('completedDepthMigrations',[]),'migration marker')
need(audit['renderedWorldSubscribers']['Airship']['physicalAllowed'] is False,'Airship physicalAllowed must remain false')
need((ROOT/'handoff/ALPHA28_0690_AIRSHIP_INTERIOR_VISUAL_REBUILD.md').exists(),'handoff missing')
need(BRANCH in text(ROOT/'handoff/LATEST_CARDCHA_HANDOFF.md'),'latest handoff branch')
print('0690 validation PASS')
