#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import base64, json, zlib

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'tools/0690_assets'
OUT=ROOT/'src/Cardcha/assets/airship_props/set01_redux'
OUT.mkdir(parents=True,exist_ok=True)
for src in SRC.glob('*.b85'):
    raw=zlib.decompress(base64.b85decode(src.read_text(encoding='ascii').strip().encode('ascii')))
    (OUT/(src.stem+'.png')).write_bytes(raw)
Image.new('RGBA',(16,16),(0,0,0,0)).save(OUT/'collision_blocker.png',optimize=True)

base_window=Image.open(OUT/'observation_window_base.png').convert('RGBA')
panes=[(28,20,52,48),(59,20,101,48),(108,20,134,48)]
for frame,shift in enumerate((0,3,6,9),1):
    overlay=Image.new('RGBA',base_window.size,(0,0,0,0))
    for box in panes:
        crop=base_window.crop(box); w,h=crop.size
        shifted=Image.new('RGBA',(w,h),(0,0,0,255))
        shifted.alpha_composite(crop,(-shift%w,0)); shifted.alpha_composite(crop,((w-shift)%w,0))
        overlay.alpha_composite(shifted,(box[0],box[1]))
    overlay.quantize(colors=128,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).save(OUT/f'observation_window_overlay_{frame}.png',optimize=True)

base_console=Image.open(OUT/'navigation_console_base.png').convert('RGBA')
box=(40,15,74,37); x0,y0,x1,y1=box; sw,sh=x1-x0,y1-y0
teal_dark=(6,69,69,255); teal=(24,183,166,255); hi=(115,246,220,255); amber=(244,192,74,255); red=(232,76,67,255)
for frame in range(4):
    overlay=Image.new('RGBA',base_console.size,(0,0,0,0)); d=ImageDraw.Draw(overlay)
    d.rectangle((x0,y0,x1-1,y1-1),fill=teal_dark); d.rectangle((x0,y0,x1-1,y0+1),fill=(19,120,112,255))
    if frame==0:
        pts=[(x0+4,y0+15),(x0+10,y0+7),(x0+17,y0+13),(x0+24,y0+6),(x0+30,y0+10)]; d.line(pts,fill=amber,width=1)
        for x,y in pts:d.rectangle((x-1,y-1,x+1,y+1),fill=hi)
    elif frame==1:
        cx,cy=x0+sw//2,y0+sh//2
        for r in (4,8,11):d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(17,137,128,255))
        d.line((cx,cy,cx+10,cy-6),fill=hi,width=1); d.rectangle((cx-1,cy-1,cx+1,cy+1),fill=amber)
    elif frame==2:
        d.rectangle((x0+6,y0+9,x0+22,y0+12),fill=teal); d.rectangle((x0+9,y0+7,x0+19,y0+14),outline=hi)
        d.polygon([(x0+27,y0+15),(x0+31,y0+7),(x0+33,y0+15)],fill=red); d.rectangle((x0+30,y0+10,x0+30,y0+12),fill='white')
    else:
        pts=[(x0+5,y0+15),(x0+11,y0+8),(x0+19,y0+13),(x0+27,y0+6)]; d.line(pts,fill=amber,width=1)
        tx,ty=x0+27,y0+6; d.ellipse((tx-4,ty-4,tx+4,ty+4),outline=red,width=1); d.rectangle((tx-1,ty-1,tx+1,ty+1),fill=hi)
    overlay.quantize(colors=64,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).save(OUT/f'navigation_console_overlay_{frame+1}.png',optimize=True)

manifest={'version':'0690-set01-redux','staticPhysicalOwner':'TMX map layers','runtimeOverlays':['observation_window_overlay_1..4','navigation_console_overlay_1..4'],'props':{'route_notice_board':[80,80],'boarding_gate_arch':[112,96],'signal_lamp':[32,48],'cargo_parcel_crate':[48,48],'observation_window_base':[160,80],'navigation_console_base':[112,80]}}
(OUT/'set01_redux_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('0690 Set01 Redux assets materialized:',OUT)
