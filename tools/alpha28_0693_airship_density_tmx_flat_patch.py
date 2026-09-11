#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/Cardcha/assets'
PATCH={
    'sky_dock_interior.tmx':('CardchaSkyDockDensity0693','airship_0693_sky_dock_density.png'),
    'airship_deck.tmx':('CardchaAirshipDeckDensity0693','airship_0693_deck_density.png'),
}
for map_name,(tileset_name,flat_name) in PATCH.items():
    path=ASSETS/map_name
    tree=ET.parse(path); root=tree.getroot()
    found=False
    for ts in root.findall('tileset'):
        if ts.attrib.get('name') != tileset_name:
            continue
        image=ts.find('image')
        if image is None:
            raise RuntimeError(f'{map_name}: {tileset_name} missing image')
        image.set('source',flat_name)
        found=True
    if not found:
        raise RuntimeError(f'{map_name}: missing {tileset_name}')
    props=root.find('properties')
    if props is not None:
        for p in props.findall('property'):
            if p.attrib.get('name')=='CardchaTextureContract':
                p.set('value','0693|flat-rgba-density-and-hero-tmx-textures|png-color-type-6')
    ET.indent(tree,space=' ')
    tree.write(path,encoding='UTF-8',xml_declaration=True)
print('0693 TMX density sources patched to flat RGBA runtime paths')
