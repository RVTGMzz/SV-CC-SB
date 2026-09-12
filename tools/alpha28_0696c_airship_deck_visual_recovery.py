#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import math
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
ASSETS = CARDCHA / "assets"
PROP_ROOT = ASSETS / "airship_props/set01_redux"
WINDOW_DIR = PROP_ROOT / "window_runtime"
CONSOLE_DIR = PROP_ROOT / "console_runtime"
SHELL_DIR = ASSETS / "airship_props/room_shell"
MANIFEST_PATH = PROP_ROOT / "airship_ambient_manifest.json"
DECK_MAP = ASSETS / "airship_deck.tmx"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.64"
SHELL_GID = 7200
TILE = 16

SEASONS = ["default", "spring", "summer", "fall", "winter"]
TIMES = ["morning", "noon", "evening", "night"]
WEATHERS = ["clear", "rain", "storm", "snow"]
VIEWPORT = (16, 14, 128, 42)


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def tint_pixel(rgb: tuple[int, int, int], season: str, tod: str, weather: str) -> tuple[int, int, int]:
    r, g, b = rgb
    season_mul = {
        "default": (1.00, 1.00, 1.00),
        "spring": (0.98, 1.05, 1.03),
        "summer": (1.07, 1.04, 0.96),
        "fall": (1.11, 0.96, 0.88),
        "winter": (0.91, 0.99, 1.10),
    }[season]
    time_mul, time_add = {
        "morning": ((1.04, 0.97, 0.91), (14, 8, 2)),
        "noon": ((1.00, 1.00, 1.00), (0, 0, 0)),
        "evening": ((1.05, 0.79, 0.92), (20, 5, 12)),
        "night": ((0.39, 0.50, 0.78), (0, 3, 18)),
    }[tod]
    weather_mul, weather_add = {
        "clear": ((1.00, 1.00, 1.00), (0, 0, 0)),
        "rain": ((0.72, 0.79, 0.88), (-2, 0, 6)),
        "storm": ((0.48, 0.56, 0.72), (-5, -3, 8)),
        "snow": ((0.98, 1.04, 1.12), (14, 16, 20)),
    }[weather]
    vals = []
    for c, sm, tm, wm, add_t, add_w in zip((r, g, b), season_mul, time_mul, weather_mul, time_add, weather_add):
        vals.append(clamp(c * sm * tm * wm + add_t + add_w))
    return tuple(vals)  # type: ignore[return-value]


def generate_window_assets() -> dict[str, dict[str, dict[str, str]]]:
    WINDOW_DIR.mkdir(parents=True, exist_ok=True)
    base = Image.open(PROP_ROOT / "observation_window_base.png").convert("RGBA")
    overlay1 = Image.open(PROP_ROOT / "observation_window_overlay_1.png").convert("RGBA")
    if base.size != (160, 80) or overlay1.size != (160, 80):
        raise RuntimeError("Observation Window source dimensions drifted")

    mask_alpha = overlay1.getchannel("A")
    mask = Image.new("RGBA", base.size, (0, 0, 0, 0))
    mp = mask.load()
    ap = mask_alpha.load()
    frame = base.copy()
    fp = frame.load()
    for y in range(base.height):
        for x in range(base.width):
            if ap[x, y] > 0:
                mp[x, y] = (255, 255, 255, 255)
                r, g, b, _ = fp[x, y]
                fp[x, y] = (r, g, b, 0)
    frame.save(WINDOW_DIR / "observation_window_frame.png")
    mask.save(WINDOW_DIR / "observation_window_view_mask.png")

    vx, vy, vw, vh = VIEWPORT
    source_crop = base.crop((vx, vy, vx + vw, vy + vh)).convert("RGBA")
    states: dict[str, dict[str, dict[str, str]]] = {}
    for season in SEASONS:
        states[season] = {}
        for tod in TIMES:
            states[season][tod] = {}
            for weather in WEATHERS:
                scene = source_crop.copy()
                pix = scene.load()
                for y in range(scene.height):
                    # A very small vertical modulation adds depth without repainting source art.
                    horizon = 0.96 + (y / max(1, scene.height - 1)) * 0.08
                    for x in range(scene.width):
                        r, g, b, a = pix[x, y]
                        nr, ng, nb = tint_pixel((r, g, b), season, tod, weather)
                        pix[x, y] = (clamp(nr * horizon), clamp(ng * horizon), clamp(nb * horizon), a)

                draw = ImageDraw.Draw(scene, "RGBA")
                if tod == "night":
                    # Tiny stars only in upper sky. Frame later clips everything to the aperture.
                    for sx, sy in [(9,5),(24,9),(42,4),(63,11),(83,6),(105,9),(119,4)]:
                        draw.point((sx, sy), fill=(235, 240, 255, 180))
                if weather in ("rain", "storm"):
                    draw.rectangle((0, 0, vw, 8), fill=(40, 52, 82, 35 if weather == "rain" else 70))
                elif weather == "snow":
                    draw.rectangle((0, 0, vw, vh), fill=(210, 230, 248, 18))

                name = f"window_scene_{season}_{tod}_{weather}.png"
                scene.save(WINDOW_DIR / name)
                states[season][tod][weather] = f"assets/airship_props/set01_redux/window_runtime/{name}"

    def make_strip(kind: str, frames: int, duration_hint: int) -> None:
        strip = Image.new("RGBA", (vw * frames, vh), (0, 0, 0, 0))
        for i in range(frames):
            fr = Image.new("RGBA", (vw, vh), (0, 0, 0, 0))
            d = ImageDraw.Draw(fr, "RGBA")
            if kind == "clouds":
                for j in range(3):
                    cx = ((i * 9 + j * 47) % (vw + 34)) - 17
                    cy = 5 + j * 8
                    d.rectangle((cx, cy, cx + 18, cy + 3), fill=(244, 247, 255, 28))
                    d.rectangle((cx + 4, cy - 2, cx + 13, cy + 5), fill=(244, 247, 255, 24))
            elif kind == "rain":
                for j in range(26):
                    x = (j * 17 + i * 7) % vw
                    y = (j * 11 + i * 9) % vh
                    d.line((x, y, x - 3, y + 6), fill=(170, 215, 245, 120), width=1)
            elif kind == "snow":
                for j in range(28):
                    x = (j * 29 + i * 5) % vw
                    y = (j * 13 + i * 7) % vh
                    size = 2 if j % 7 == 0 else 1
                    d.rectangle((x, y, x + size - 1, y + size - 1), fill=(245, 250, 255, 185))
            strip.alpha_composite(fr, (i * vw, 0))
        strip.save(WINDOW_DIR / f"window_fx_{kind}_strip.png")

    make_strip("clouds", 6, 140)
    make_strip("rain", 6, 90)
    make_strip("snow", 6, 120)

    for idx, alpha in [(1, 115), (2, 175)]:
        flash = Image.new("RGBA", (160, 80), (0, 0, 0, 0))
        px = flash.load()
        for y in range(80):
            for x in range(160):
                if ap[x, y] > 0:
                    px[x, y] = (220, 235, 255, alpha)
        if idx == 2:
            d = ImageDraw.Draw(flash, "RGBA")
            d.line((80, 18, 73, 30, 79, 30, 70, 48), fill=(255,255,255,230), width=1)
        flash.save(WINDOW_DIR / f"window_fx_lightning_flash_0{idx}.png")

    return states


def generate_console_assets() -> None:
    CONSOLE_DIR.mkdir(parents=True, exist_ok=True)
    base = Image.open(PROP_ROOT / "navigation_console_base.png").convert("RGBA")
    if base.size != (112, 80):
        raise RuntimeError("Navigation Console source dimensions drifted")
    x, y, w, h = 18, 8, 48, 32
    radar_bg = base.crop((x, y, x+w, y+h)).convert("RGBA")
    radar_bg.save(CONSOLE_DIR / "radar_bg.png")

    frame = base.copy()
    fp = frame.load()
    for yy in range(y, y+h):
        for xx in range(x, x+w):
            r,g,b,_ = fp[xx,yy]
            fp[xx,yy] = (r,g,b,0)
    frame.save(CONSOLE_DIR / "navigation_console_frame.png")

    cx, cy = w // 2, h // 2
    sweep_frames = 8
    sweep = Image.new("RGBA", (w*sweep_frames, h), (0,0,0,0))
    for i in range(sweep_frames):
        fr = Image.new("RGBA", (w,h), (0,0,0,0))
        d = ImageDraw.Draw(fr, "RGBA")
        angle = -math.pi/2 + i * math.tau/sweep_frames
        ex = int(round(cx + math.cos(angle) * 18))
        ey = int(round(cy + math.sin(angle) * 12))
        d.line((cx,cy,ex,ey), fill=(120,245,225,190), width=2)
        d.rectangle((cx-1,cy-1,cx+1,cy+1), fill=(205,255,245,210))
        sweep.alpha_composite(fr, (i*w,0))
    sweep.save(CONSOLE_DIR / "radar_sweep_strip.png")

    pings = Image.new("RGBA", (w*4,h), (0,0,0,0))
    points = [(14,10),(34,8),(31,22),(18,24)]
    for i in range(4):
        fr=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(fr,"RGBA")
        for j,(px,py) in enumerate(points):
            if (i+j)%3 != 0:
                a=220 if (i+j)%2==0 else 125
                d.rectangle((px,py,px+1,py+1),fill=(230,255,190,a))
        pings.alpha_composite(fr,(i*w,0))
    pings.save(CONSOLE_DIR / "radar_pings_strip.png")

    glow = Image.new("RGBA", (w*4,h), (0,0,0,0))
    for i,a in enumerate((18,32,45,28)):
        fr=Image.new("RGBA",(w,h),(65,235,220,a))
        glow.alpha_composite(fr,(i*w,0))
    glow.save(CONSOLE_DIR / "radar_glow_strip.png")


def generate_room_shell_asset() -> Path:
    SHELL_DIR.mkdir(parents=True, exist_ok=True)
    out = SHELL_DIR / "airship_deck_border_0696c.png"
    sheet = Image.new("RGBA", (160, 16), (0,0,0,0))
    dark=(45,24,34,255); deep=(75,39,39,255); wood=(126,72,48,255); warm=(164,91,50,255); brass=(210,143,65,255); floor=(151,83,50,255)

    def tile_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        im=Image.new("RGBA",(16,16),floor); return im,ImageDraw.Draw(im)

    tiles=[]
    # left vertical
    im,d=tile_canvas(); d.rectangle((0,0,3,15),fill=dark); d.rectangle((4,0,6,15),fill=deep); d.line((7,0,7,15),fill=brass); tiles.append(im)
    # right vertical
    im,d=tile_canvas(); d.rectangle((12,0,15,15),fill=dark); d.rectangle((9,0,11,15),fill=deep); d.line((8,0,8,15),fill=brass); tiles.append(im)
    # bottom horizontal
    im,d=tile_canvas(); d.rectangle((0,11,15,15),fill=dark); d.rectangle((0,8,15,10),fill=deep); d.line((0,7,15,7),fill=brass); tiles.append(im)
    # top horizontal
    im,d=tile_canvas(); d.rectangle((0,0,15,4),fill=dark); d.rectangle((0,5,15,7),fill=deep); d.line((0,8,15,8),fill=brass); d.rectangle((1,10,14,15),fill=wood); tiles.append(im)
    # bottom-left
    im,d=tile_canvas(); d.rectangle((0,0,3,15),fill=dark); d.rectangle((0,11,15,15),fill=dark); d.line((4,7,15,7),fill=brass); d.line((7,0,7,10),fill=brass); tiles.append(im)
    # bottom-right
    im,d=tile_canvas(); d.rectangle((12,0,15,15),fill=dark); d.rectangle((0,11,15,15),fill=dark); d.line((0,7,11,7),fill=brass); d.line((8,0,8,10),fill=brass); tiles.append(im)
    # top-left
    im,d=tile_canvas(); d.rectangle((0,0,3,15),fill=dark); d.rectangle((0,0,15,4),fill=dark); d.line((4,8,15,8),fill=brass); d.line((7,5,7,15),fill=brass); tiles.append(im)
    # top-right
    im,d=tile_canvas(); d.rectangle((12,0,15,15),fill=dark); d.rectangle((0,0,15,4),fill=dark); d.line((0,8,11,8),fill=brass); d.line((8,5,8,15),fill=brass); tiles.append(im)
    # doorway left jamb / threshold edge
    im,d=tile_canvas(); d.rectangle((0,10,15,15),fill=dark); d.rectangle((10,0,15,15),fill=deep); d.line((9,0,9,15),fill=brass); d.line((0,8,9,8),fill=brass); tiles.append(im)
    # doorway right jamb / threshold edge
    im,d=tile_canvas(); d.rectangle((0,10,15,15),fill=dark); d.rectangle((0,0,5,15),fill=deep); d.line((6,0,6,15),fill=brass); d.line((6,8,15,8),fill=brass); tiles.append(im)

    for i,t in enumerate(tiles): sheet.alpha_composite(t,(i*16,0))
    sheet.save(out)
    return out


def csv_values(layer: ET.Element) -> list[int]:
    data=layer.find("data")
    if data is None or data.attrib.get("encoding") != "csv": raise RuntimeError(f"layer {layer.attrib.get('name')} not csv")
    vals=[int(x.strip()) for x in (data.text or "").split(",") if x.strip()]
    if len(vals) != int(layer.attrib["width"])*int(layer.attrib["height"]): raise RuntimeError("layer cell count drift")
    return vals


def set_csv(layer: ET.Element, vals: list[int]) -> None:
    data=layer.find("data"); assert data is not None
    data.text="\n"+",".join(map(str,vals))+"\n"


def layer(root: ET.Element, name: str) -> ET.Element:
    found=next((x for x in root.findall("layer") if x.attrib.get("name")==name),None)
    if found is None: raise RuntimeError(f"missing layer {name}")
    return found


def set_map_property(root: ET.Element, name: str, value: str) -> None:
    props=root.find("properties")
    if props is None:
        props=ET.Element("properties"); root.insert(0,props)
    p=next((x for x in props.findall("property") if x.attrib.get("name")==name),None)
    if p is None: p=ET.SubElement(props,"property",{"name":name})
    p.set("value",value)


def materialize_deck_shell() -> None:
    shell=generate_room_shell_asset()
    tree=ET.parse(DECK_MAP); root=tree.getroot(); w=int(root.attrib["width"]); h=int(root.attrib["height"])
    if (w,h)!=(24,14): raise RuntimeError(f"Airship Deck dimensions drifted: {w}x{h}")
    for old in list(root.findall("tileset")):
        if old.attrib.get("name")=="CardchaAirshipDeckRoomShell0696C": root.remove(old)
    ts=ET.Element("tileset",{"firstgid":str(SHELL_GID),"name":"CardchaAirshipDeckRoomShell0696C","tilewidth":"16","tileheight":"16","tilecount":"10","columns":"10"})
    ET.SubElement(ts,"image",{"source":"airship_props/room_shell/airship_deck_border_0696c.png","width":"160","height":"16"})
    children=list(root); first_layer=next((i for i,c in enumerate(children) if c.tag=="layer"),len(children)); root.insert(first_layer,ts)

    b2=layer(root,"Buildings2"); f2=layer(root,"Front2")
    bvals=csv_values(b2); fvals=csv_values(f2)
    for vals in (bvals,fvals):
        for i,v in enumerate(vals):
            if SHELL_GID <= v < SHELL_GID+10: vals[i]=0
    # visible shell: top + sides are behind player; lower rail is foreground.
    bvals[0*w+0]=SHELL_GID+6; bvals[0*w+23]=SHELL_GID+7
    for x in range(1,23): bvals[x]=SHELL_GID+3
    for y in range(1,13):
        bvals[y*w+0]=SHELL_GID+0; bvals[y*w+23]=SHELL_GID+1
    fvals[13*w+0]=SHELL_GID+4; fvals[13*w+23]=SHELL_GID+5
    for x in range(1,11): fvals[13*w+x]=SHELL_GID+2
    for x in range(13,23): fvals[13*w+x]=SHELL_GID+2
    fvals[13*w+10]=SHELL_GID+8; fvals[13*w+13]=SHELL_GID+9
    # doorway x11..12 is deliberately open and visibly framed by x10/x13 jambs.
    fvals[13*w+11]=0; fvals[13*w+12]=0
    set_csv(b2,bvals); set_csv(f2,fvals)
    set_map_property(root,"CardchaAirshipVersion",NEW_VERSION)
    set_map_property(root,"CardchaVisualAcceptance","PENDING-RON-IN-GAME")
    set_map_property(root,"CardchaRoomShellContract","0696C|visible-shell|doorway-x11-12|runtime-void-guard")
    set_map_property(root,"CardchaAmbientContract","0696C|season-time-weather-matrix")
    ET.indent(tree,space=" "); tree.write(DECK_MAP,encoding="UTF-8",xml_declaration=True)


def patch_runtime_sources() -> None:
    renderer=CARDCHA/"Services/AirshipInteriorStardewRenderer.cs"
    text=renderer.read_text(encoding="utf-8")
    needle="        DrawAmbientLamps(batch, phase);\n        DrawHelmMagic(batch, phase);"
    replacement="        DrawAmbientLamps(batch, phase);\n        // 0696C: restore the four level-aware Engine/Navigation/Hull/Reactor stations.\n        DrawUpgradeStations(batch, save, phase);\n        DrawHelmMagic(batch, phase);"
    if "DrawUpgradeStations(batch, save, phase);" not in text:
        if needle not in text: raise RuntimeError("Could not locate Airship Deck station draw insertion point")
        text=text.replace(needle,replacement,1)
    renderer.write_text(text,encoding="utf-8")

    foundation=CARDCHA/"Services/AirshipFoundationService.cs"
    text=foundation.read_text(encoding="utf-8")
    call_needle="        if (this.PendingDepartureUntilMs > 0 && now > this.PendingDepartureUntilMs)\n            this.PendingDepartureUntilMs = 0;\n"
    if "this.TryRecoverDeckBoundary()" not in text:
        if call_needle not in text: raise RuntimeError("Could not locate deck boundary update insertion point")
        text=text.replace(call_needle,call_needle+"\n        // 0696C room law: no player may remain in the black void outside the bridge shell.\n        if (this.TryRecoverDeckBoundary())\n            return;\n",1)
    method_marker="    private void MigrateUnlockFromExistingStory()\n"
    if "private bool TryRecoverDeckBoundary()" not in text:
        method='''    private bool TryRecoverDeckBoundary()\n    {\n        GameLocation? location = Game1.currentLocation;\n        if (location is null || !location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n            return false;\n\n        int tileX = (int)Math.Floor(Game1.player.Position.X / 64f);\n        int tileY = (int)Math.Floor(Game1.player.Position.Y / 64f);\n\n        // The only legal lower-shell opening is the two-tile doorway. Crossing it returns\n        // immediately to the Arcane Dock instead of leaving the farmer standing in void.\n        if (tileY >= 13 && tileX is 11 or 12)\n        {\n            this.WarpToSkyDockInterior();\n            return true;\n        }\n\n        bool outsideSide = tileX <= 0 || tileX >= 23;\n        bool outsideBottom = tileY >= 13;\n        if (!outsideSide && !outsideBottom)\n            return false;\n\n        int safeX = Math.Clamp(tileX, 1, 22);\n        int safeY = Math.Clamp(tileY, 5, 12);\n        Game1.player.Position = new Vector2(safeX * 64f, safeY * 64f);\n        Game1.player.Halt();\n        return true;\n    }\n\n'''
        if method_marker not in text: raise RuntimeError("Could not locate deck boundary method insertion marker")
        text=text.replace(method_marker,method+method_marker,1)
    foundation.write_text(text,encoding="utf-8")


def write_manifest(states: dict[str,dict[str,dict[str,str]]]) -> None:
    data=json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    data["schemaVersion"]=2
    data["workstream"]="0696C-airship-deck-shell-layer-environment-recovery"
    data["version"]=NEW_VERSION
    data["visualAcceptance"]="PENDING-RON-IN-GAME"
    ow=data["observationWindow"]
    ow["productionStatus"]="GENERATED_ENVIRONMENT_MATRIX_TECHNICAL_TEST"
    ow["sceneMatrix"]={"fallbackSeason":"default","fallbackTime":"noon","fallbackWeather":"clear","states":states}
    # Old time-only map remains only as schema-1 compatibility data; no production selection uses it.
    ow["legacyFallback"]={"enabled":False,"frameDurationMs":900,"paths":[]}
    nc=data["navigationConsole"]
    nc["productionStatus"]="GENERATED_RADAR_8FRAME_TECHNICAL_TEST"
    MANIFEST_PATH.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def bump_versions() -> None:
    pattern=re.compile(r"0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.\d+")
    for rel in ["manifest.json","Cardcha.csproj","Directory.Build.targets","ModEntry.cs"]:
        p=CARDCHA/rel
        if p.exists():
            text=p.read_text(encoding="utf-8")
            text=pattern.sub(NEW_VERSION,text)
            text=text.replace("0696B AIRSHIP AMBIENT RUNTIME FOUNDATION TEST","0696C AIRSHIP DECK VISUAL RECOVERY TEST")
            p.write_text(text,encoding="utf-8")


def write_handoff() -> None:
    handoff=ROOT/"handoff/ALPHA28_0696C_AIRSHIP_DECK_VISUAL_RECOVERY.md"
    handoff.write_text(f'''# Alpha 28 / 0696C — Airship Deck Visual Recovery\n\n## Build\n`{NEW_VERSION}`\n\n## Ron in-game rejection carried forward\n`.63` is **VISUAL REJECTED** for the Airship Deck screenshot pass. Technical foundation success did not equal visual acceptance.\n\nObserved blockers from Ron:\n- opaque black window wipe frames;\n- four upgrade stations missing;\n- room shell/border visually absent;\n- lower doorway allowed the farmer to remain in black void;\n- environment selection did not match the promised time/weather list.\n\n## 0696C corrections\n- Observation Window now resolves an explicit **season × time × weather** scene matrix.\n- Matrix contains 5 season keys (`default`, spring, summer, fall, winter) × 4 time buckets × 4 weather states = **80 authored/generated scene entries**.\n- Time buckets: morning, noon, evening, night.\n- Weather: clear, rain, storm, snow.\n- Moving cloud/rain/snow FX remain separate animation layers; lightning remains an event overlay.\n- Old window overlay frames 2–4 are forbidden as fallback because they contain opaque black wipe pixels. If new ambient assets fail, the clean TMX base remains instead.\n- Navigation Console receives an 8-frame radar sweep plus ping/glow layers.\n- Engine / Navigation / Hull / Reactor upgrade stations are restored through the existing `DrawUpgradeStations` production method.\n- Airship Deck receives a visible Cardcha wood/brass shell on top, sides and lower boundary while base `Buildings` still owns collision.\n- Bottom doorway remains exactly two tiles wide at x=11..12 and crossing it immediately returns to the Arcane Dock. Any illegal side/bottom escape is recovered back inside the room.\n\n## Acceptance\nTechnical validation may PASS in CI, but visual status remains **PENDING-RON-IN-GAME** until Ron tests `.64`.\n''',encoding="utf-8")
    latest=ROOT/"handoff/LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(f'''# LATEST CARDCHA HANDOFF\n\nUpdated: 2026-09-12\n\n## Current workstream\n`cardcha-alpha28-0696-airship-concept-faithful-visible-integration`\n\nCurrent build candidate:\n`{NEW_VERSION}`\n\nCurrent handoff:\n`handoff/ALPHA28_0696C_AIRSHIP_DECK_VISUAL_RECOVERY.md`\n\n## Status\n- 0696A architecture: technical baseline.\n- 0696B `.63`: **VISUAL REJECTED by Ron** from in-game screenshots.\n- 0696C: repairs window matrix, black overlay frames, four upgrade stations, room shell and void escape.\n- Visual acceptance: **PENDING-RON-IN-GAME**.\n\n## Non-negotiable rule\nTechnical PASS never equals visual PASS. Preserve exact hero prop footprints and base `Buildings` collision ownership. Never reintroduce `BackDecor`.\n''',encoding="utf-8")


def main() -> None:
    states=generate_window_assets()
    generate_console_assets()
    write_manifest(states)
    materialize_deck_shell()
    patch_runtime_sources()
    bump_versions()
    write_handoff()
    print(f"0696C materialized: {NEW_VERSION}; window scenes={sum(len(w) for s in states.values() for w in s.values())}")

if __name__=="__main__":
    main()
