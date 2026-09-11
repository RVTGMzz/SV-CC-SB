#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/Cardcha/assets'
BLOCKER=5400

def clear_cells(map_name:str,cells:list[tuple[int,int]]) -> None:
    path=ASSETS/map_name
    tree=ET.parse(path); root=tree.getroot()
    w,h=int(root.attrib['width']),int(root.attrib['height'])
    layer=next((x for x in root.findall('layer') if x.attrib.get('name')=='Buildings'),None)
    if layer is None: raise RuntimeError(f'{map_name}: missing Buildings')
    data=layer.find('data')
    if data is None or data.attrib.get('encoding')!='csv': raise RuntimeError(f'{map_name}: Buildings not CSV')
    toks=[x.strip() for x in (data.text or '').split(',')]
    if not toks or any(x=='' for x in toks): raise RuntimeError(f'{map_name}: empty Buildings CSV token')
    vals=[int(x) for x in toks]
    if len(vals)!=w*h: raise RuntimeError(f'{map_name}: wrong Buildings tile count')
    for x,y in cells:
        if 0<=x<w and 0<=y<h and vals[y*w+x]==BLOCKER:
            vals[y*w+x]=0
    data.text='\n'+','.join(str(x) for x in vals)+'\n'
    ET.indent(tree,space=' ')
    tree.write(path,encoding='UTF-8',xml_declaration=True)

# These tiles are gameplay anchors, not decorative collision territory.
dock=[(7,7),(23,8),(5,11),(15,16),(15,14)]
dock += [(x,y) for y in range(7,18) for x in range(14,17)]
deck=[(4,8),(19,8),(7,11),(16,11),(12,12),(12,6)]
clear_cells('sky_dock_interior.tmx',dock)
clear_cells('airship_deck.tmx',deck)
print('0693 protected Airship interaction anchors cleared from decor collision')
