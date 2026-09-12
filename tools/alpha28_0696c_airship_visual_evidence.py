#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
CARDCHA=ROOT/"src/Cardcha"
PROP=CARDCHA/"assets/airship_props/set01_redux"
manifest=json.loads((PROP/"airship_ambient_manifest.json").read_text(encoding="utf-8"))
states=manifest["observationWindow"]["sceneMatrix"]["states"]
frame=Image.open(PROP/"window_runtime/observation_window_frame.png").convert("RGBA")
vx,vy,vw,vh=16,14,128,42
seasons=["default","spring","summer","fall","winter"]
times=["morning","noon","evening","night"]
weathers=["clear","rain","storm","snow"]
scale=2
cellw=160*scale
cellh=(80+14)*scale
canvas=Image.new("RGBA",(cellw*4,cellh*20),(25,20,28,255))
draw=ImageDraw.Draw(canvas)
row=0
for season in seasons:
    for tod in times:
        for col,weather in enumerate(weathers):
            scene=Image.open(CARDCHA/states[season][tod][weather]).convert("RGBA")
            comp=Image.new("RGBA",(160,80),(0,0,0,0))
            comp.alpha_composite(scene,(vx,vy))
            comp.alpha_composite(frame,(0,0))
            comp=comp.resize((320,160),Image.Resampling.NEAREST)
            x=col*cellw; y=row*cellh
            canvas.alpha_composite(comp,(x,y+28))
            draw.text((x+4,y+4),f"{season} | {tod} | {weather}",fill=(245,235,210,255))
        row+=1
out=ROOT/"handoff/AIRSHIP_0696C_WINDOW_MATRIX_PREVIEW.png"
canvas.convert("RGB").save(out)
print(out)
