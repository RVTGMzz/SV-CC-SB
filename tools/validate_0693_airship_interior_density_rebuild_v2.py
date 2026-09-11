#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, struct
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src/Cardcha'
VERSION='0.3.0-alpha.28.0.4.14.4.5.12.60'
BRANCH='cardcha-alpha28-0693-airship-interior-density-rebuild'

def req(c,m):
    if not c: raise SystemExit('0693 validation FAIL: '+m)

def png(path:Path):
    raw=path.read_bytes(); req(raw[:8]==b'\x89PNG\r\n\x1a\n',path.name+' not PNG')
    return (*struct.unpack('>II',raw[16:24]),raw[25])

def layer_vals(root,name):
    layer=next((x for x in root.findall('layer') if x.attrib.get('name')==name),None); req(layer is not None,'missing '+name)
    data=layer.find('data'); req(data is not None and data.attrib.get('encoding')=='csv',name+' not CSV')
    vals=[int(x.strip()) for x in (data.text or '').split(',') if x.strip()]
    req(len(vals)==int(root.attrib['width'])*int(root.attrib['height']),name+' tile count')
    return vals

for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets']:
    req(VERSION in (SRC/rel).read_text(encoding='utf-8'),rel+' version')

for name,size in [('airship_0693_sky_dock_density.png',(480,288)),('airship_0693_deck_density.png',(384,224))]:
    w,h,ct=png(SRC/'assets'/name); req((w,h)==size,f'{name} size'); req(ct==6,f'{name} RGBA color type')

def inspect_map(name,wh,tileset_name,flat_source,density_range,min_density):
    root=ET.parse(SRC/'assets'/name).getroot(); req((int(root.attrib['width']),int(root.attrib['height']))==wh,name+' dims')
    ts=next((t for t in root.findall('tileset') if t.attrib.get('name')==tileset_name),None); req(ts is not None,name+' density tileset')
    image=ts.find('image'); req(image is not None and image.attrib.get('source')==flat_source,name+' flat source')
    req('/' not in image.attrib.get('source','') and '\\' not in image.attrib.get('source',''),name+' density source must be flat')
    vals=layer_vals(root,'BackDecor'); lo,hi=density_range; req(sum(lo<=v<=hi for v in vals)>=min_density,name+' density coverage')
    props={p.attrib.get('name'):p.attrib.get('value') for ps in root.findall('properties') for p in ps.findall('property')}
    req(props.get('CardchaTextureContract')=='0693|flat-rgba-density-and-hero-tmx-textures|png-color-type-6',name+' texture contract')
    return root,vals,layer_vals(root,'Buildings')

dock,dock_back,dock_build=inspect_map('sky_dock_interior.tmx',(30,18),'CardchaSkyDockDensity0693','airship_0693_sky_dock_density.png',(5800,6339),65)
req(not any(5000<=v<=5024 for v in dock_back),'old route-board cluster active')
req(not any(5300<=v<=5308 for v in dock_back),'old crate cluster active')
req(not any(5500<=v<=5799 for v in dock_back),'old sparse Set02 active')
req(any(5100<=v<=5141 for v in dock_back),'boarding gate missing')
req(any(5200<=v<=5205 for v in dock_back),'dock lamp missing')
for y in range(7,18):
    for x in range(14,17): req(dock_build[y*30+x]!=5400,f'dock center blocked {x},{y}')
for x,y in [(7,7),(23,8),(5,11),(15,16),(15,14)]: req(dock_build[y*30+x]!=5400,f'dock anchor blocked {x},{y}')

deck,deck_back,deck_build=inspect_map('airship_deck.tmx',(24,14),'CardchaAirshipDeckDensity0693','airship_0693_deck_density.png',(5800,6135),50)
req(any(5000<=v<=5049 for v in deck_back),'Observation Window missing')
req(any(5100<=v<=5134 for v in deck_back),'Navigation Console missing')
req(sum(5200<=v<=5205 for v in deck_back)>=2,'deck lamps missing')
for x,y in [(4,8),(19,8),(7,11),(16,11),(12,12),(12,6)]: req(deck_build[y*24+x]!=5400,f'deck anchor blocked {x},{y}')

renderer=(SRC/'Services/AirshipInteriorStardewRenderer.cs').read_text(encoding='utf-8')
req('DrawDeckStardewDecor(batch);' not in renderer,'deck physical runtime decor re-enabled')
req('DrawDockStardewDecor(batch);' not in renderer,'dock physical runtime decor re-enabled')
req('Draw0690WindowOverlay(batch);' in renderer and 'Draw0690ConsoleOverlay(batch);' in renderer,'hero VFX lost')

audit=json.loads((ROOT/'render_depth_audit.json').read_text(encoding='utf-8'))
req(audit.get('branch')==BRANCH,'render audit branch')
req('0693 Airship dense physical interior scene->TMX; runtime remains VFX-only' in json.dumps(audit),'depth marker')
latest=(ROOT/'handoff/LATEST_CARDCHA_HANDOFF.md').read_text(encoding='utf-8')
handoff=(ROOT/'handoff/ALPHA28_0693_AIRSHIP_INTERIOR_DENSITY_REBUILD.md').read_text(encoding='utf-8')
req(BRANCH in latest and VERSION in latest,'latest handoff')
req('In-game visual acceptance remains PENDING' in handoff,'acceptance state')
print('0693 Airship interior density validation PASS')
