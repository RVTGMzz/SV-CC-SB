#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP = CARDCHA / "assets/airship_props/set01_redux"
WINDOW = PROP / "window_runtime"
BASE = PROP / "observation_window_base.png"
OVERLAYS = [PROP / f"observation_window_overlay_{i}.png" for i in range(1, 5)]
FRAME = WINDOW / "observation_window_frame.png"
MANIFEST = PROP / "airship_ambient_manifest.json"
SOURCE_PACK = ROOT / "handoff/AIRSHIP_SOURCE_PACK_0696.json"
REPORT = ROOT / "handoff/AIRSHIP_0696D1R_WINDOW_BOUNDED_VALIDATION.json"
PREVIEW = ROOT / "handoff/AIRSHIP_0696D1R_WINDOW_FRAMES_PREVIEW.png"
HANDOFF = ROOT / "handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md"
LATEST = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"

BASELINE_COMMIT = "0b13de1ac30dfa019061d3626c478c5460dab89f"
BRANCH = "cardcha-alpha28-0696d1-observation-window-source-cleanup"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.66"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.67"
EXPECTED_SIZE = (160, 80)
MATTE_RGB = {(244, 214, 168), (244, 210, 156), (238, 204, 156)}
MAX_EDGE_BLEED_COMPONENT = 256


def git_show_bytes(rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASELINE_COMMIT}:{rel}"], cwd=ROOT)


def restore_authoritative_sources() -> dict[str, str]:
    hashes = {}
    for path in [BASE, *OVERLAYS]:
        rel = path.relative_to(ROOT).as_posix()
        raw = git_show_bytes(rel)
        path.write_bytes(raw)
        hashes[rel] = hashlib.sha256(raw).hexdigest()
    return hashes


def rgba_sha(im: Image.Image) -> str:
    return hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest()


def border_connected_exact_matte(src: Image.Image) -> set[tuple[int, int]]:
    im = src.convert("RGBA")
    w, h = im.size
    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def candidate(x: int, y: int) -> bool:
        r, g, b, a = im.getpixel((x, y))
        return a == 0 or (r, g, b) in MATTE_RGB

    def offer(x: int, y: int) -> None:
        p = (x, y)
        if p in seen or not candidate(x, y):
            return
        seen.add(p)
        q.append(p)

    for x in range(w):
        offer(x, 0); offer(x, h - 1)
    for y in range(h):
        offer(0, y); offer(w - 1, y)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                offer(nx, ny)
    return seen


def alpha_components(im: Image.Image) -> list[list[tuple[int,int]]]:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    alpha = rgba.getchannel("A")
    seen: set[tuple[int,int]] = set()
    comps: list[list[tuple[int,int]]] = []
    for y in range(h):
        for x in range(w):
            if (x,y) in seen or alpha.getpixel((x,y)) == 0:
                continue
            q = deque([(x,y)])
            seen.add((x,y))
            pts: list[tuple[int,int]] = []
            while q:
                px, py = q.popleft(); pts.append((px,py))
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny = px+dx,py+dy
                    if 0 <= nx < w and 0 <= ny < h and (nx,ny) not in seen and alpha.getpixel((nx,ny)) > 0:
                        seen.add((nx,ny)); q.append((nx,ny))
            comps.append(pts)
    return sorted(comps, key=len, reverse=True)


def bbox(pts: list[tuple[int,int]]) -> list[int]:
    xs=[x for x,_ in pts]; ys=[y for _,y in pts]
    return [min(xs),min(ys),max(xs)+1,max(ys)+1]


def remove_detached_edge_bleed(im: Image.Image) -> tuple[Image.Image, list[dict]]:
    out = im.convert("RGBA").copy()
    w,h = out.size
    comps = alpha_components(out)
    assert comps, "Window became fully transparent"
    main = comps[0]
    removed=[]
    for pts in comps[1:]:
        touches_edge = any(x in (0,w-1) or y in (0,h-1) for x,y in pts)
        if touches_edge and len(pts) <= MAX_EDGE_BLEED_COMPONENT:
            for x,y in pts:
                r,g,b,_ = out.getpixel((x,y))
                out.putpixel((x,y),(r,g,b,0))
            removed.append({"pixels":len(pts),"bbox":bbox(pts)})
    assert all(out.getpixel(p)[3] > 0 for p in main)
    return out, removed


def clean_base(original: Image.Image) -> tuple[Image.Image, dict]:
    src = original.convert("RGBA")
    out = src.copy()
    connected = border_connected_exact_matte(src)
    matte_changed=[]
    for x,y in connected:
        r,g,b,a = src.getpixel((x,y))
        if a > 0 and (r,g,b) in MATTE_RGB:
            out.putpixel((x,y),(r,g,b,0))
            matte_changed.append((x,y))

    after_matte = out.copy()
    out, edge_removed = remove_detached_edge_bleed(out)

    for y in range(src.height):
        for x in range(src.width):
            before=src.getpixel((x,y)); mid=after_matte.getpixel((x,y))
            if before != mid:
                assert before[:3] in MATTE_RGB and before[3] > 0
                assert mid[:3] == before[:3] and mid[3] == 0

    assert src.convert("RGB").tobytes() == out.convert("RGB").tobytes()
    final_components=alpha_components(out)
    touching_detached=[]
    for pts in final_components[1:]:
        if any(x in (0,out.width-1) or y in (0,out.height-1) for x,y in pts):
            touching_detached.append({"pixels":len(pts),"bbox":bbox(pts)})
    assert not touching_detached, touching_detached

    return out, {
        "method":"exact-border-matte + detached-edge-component removal",
        "mattePixelsRemoved":len(matte_changed),
        "detachedEdgeComponentsRemoved":edge_removed,
        "detachedEdgePixelsRemoved":sum(x["pixels"] for x in edge_removed),
        "transparentBefore":sum(a==0 for a in src.getchannel("A").getdata()),
        "transparentAfter":sum(a==0 for a in out.getchannel("A").getdata()),
        "rgbaShaBefore":rgba_sha(src),
        "rgbaShaAfter":rgba_sha(out),
        "mainComponentPixels":len(final_components[0]),
        "mainComponentBBox":bbox(final_components[0]),
        "remainingDetachedEdgeComponents":0,
    }


def sanitize_overlay(original: Image.Image, index: int) -> tuple[Image.Image, dict]:
    src=original.convert("RGBA"); out=src.copy(); removed=0
    for y in range(src.height):
        for x in range(src.width):
            r,g,b,a=src.getpixel((x,y))
            if a>0 and (r,g,b)==(0,0,0):
                out.putpixel((x,y),(0,0,0,0)); removed+=1
    for y in range(src.height):
        for x in range(src.width):
            before=src.getpixel((x,y)); after=out.getpixel((x,y))
            if before[:3] != (0,0,0) or before[3] == 0:
                assert after == before, (index,x,y,before,after)
            else:
                assert after == (0,0,0,0)
    return out, {
        "frame":index,"size":list(src.size),"opaquePureBlackRemoved":removed,
        "remainingOpaquePureBlack":sum(1 for r,g,b,a in out.getdata() if a>0 and (r,g,b)==(0,0,0)),
        "alphaBBoxAfter":list(out.getchannel("A").getbbox() or (0,0,0,0)),
    }


def checker(size: tuple[int,int], cell:int=8) -> Image.Image:
    out=Image.new("RGBA",size,(38,38,50,255)); d=ImageDraw.Draw(out)
    for y in range(0,size[1],cell):
        for x in range(0,size[0],cell):
            c=(67,67,86,255) if ((x//cell)+(y//cell))%2==0 else (38,38,50,255)
            d.rectangle((x,y,min(x+cell-1,size[0]-1),min(y+cell-1,size[1]-1)),fill=c)
    return out


def composite(base:Image.Image, overlay:Image.Image)->Image.Image:
    out=checker(base.size); out.alpha_composite(base); out.alpha_composite(overlay); return out


def render_preview(orig_base,orig_overlays,fixed_base,fixed_overlays,base_stats):
    scale=3; cw,ch=160*scale,80*scale; margin,top,gap=18,46,52
    canvas=Image.new("RGBA",(margin*5+cw*4,top+ch*2+gap+54),(16,17,24,255)); d=ImageDraw.Draw(canvas)
    d.text((margin,14),"0696D1R FINAL | TOP=.64 source | BOTTOM=bounded fix | 4 independent 160x80 overlays",fill=(238,240,246,255))
    for i in range(4):
        x=margin+i*(cw+margin)
        before=composite(orig_base,orig_overlays[i]).resize((cw,ch),Image.Resampling.NEAREST)
        after=composite(fixed_base,fixed_overlays[i]).resize((cw,ch),Image.Resampling.NEAREST)
        canvas.alpha_composite(before,(x,top)); canvas.alpha_composite(after,(x,top+ch+gap))
        d.text((x,top-20),f"SOURCE frame {i+1}",fill=(225,198,150,255))
        d.text((x,top+ch+gap-20),f"FIXED frame {i+1}",fill=(155,230,190,255))
    d.text((margin,canvas.height-34),f"No crop/shift/packing/hollow. Removed detached edge bleed: {base_stats['detachedEdgePixelsRemoved']} px in {len(base_stats['detachedEdgeComponentsRemoved'])} components.",fill=(205,214,230,255))
    PREVIEW.parent.mkdir(parents=True,exist_ok=True); canvas.save(PREVIEW)


def update_versions():
    for rel in ["manifest.json","Cardcha.csproj","Directory.Build.targets","ModEntry.cs"]:
        p=CARDCHA/rel
        if p.exists():
            s=p.read_text(encoding="utf-8").replace(OLD_VERSION,NEW_VERSION)
            s=s.replace("0696D1R WINDOW BOUNDED CLEANUP TEST","0696D1R WINDOW BOUNDED CLEANUP FINAL TEST")
            p.write_text(s,encoding="utf-8")


def update_manifest():
    data=json.loads(MANIFEST.read_text(encoding="utf-8")); data["version"]=NEW_VERSION; data["workstream"]="0696D1R-window-bounded-cleanup-final"
    ow=data["observationWindow"]
    ow["productionStatus"]="D1R_FINAL_BOUNDED_CLEAN_4_OVERLAYS_ACTIVE_D2_PENDING"
    ow["sourceCleanup"]={
        "mode":"exact-border-matte-plus-detached-edge-component-plus-pure-black-overlay-alpha-repair",
        "baselineCommit":BASELINE_COMMIT,"crop":"forbidden","shift":"forbidden","framePacking":"forbidden","apertureCutout":"forbidden",
        "detachedEdgeRule":f"non-main alpha components touching canvas edge and <= {MAX_EDGE_BLEED_COMPONENT} pixels",
        "overlayFiles":[f"assets/airship_props/set01_redux/observation_window_overlay_{i}.png" for i in range(1,5)],
        "acceptance":"PENDING-RON-VISUAL"
    }
    MANIFEST.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")


def update_source_pack():
    if not SOURCE_PACK.exists(): return
    data=json.loads(SOURCE_PACK.read_text(encoding="utf-8")); targets={p.relative_to(ROOT).as_posix():p for p in [BASE,*OVERLAYS]}
    for rec in data.get("assets",[]):
        rel=rec.get("path")
        if rel not in targets: continue
        p=targets[rel]; im=Image.open(p).convert("RGBA")
        rec.update({"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"dimensions":list(im.size),"mode":"RGBA","alpha_bbox":list(im.getchannel('A').getbbox() or (0,0,0,0)),"nontransparent_pixels":sum(a>0 for a in im.getchannel('A').getdata()),"status":"source-faithful-bounded-cleanup-0696D1R-final"})
    data["source_policy"]="D1R final restores verified .64 source first; base cleanup is exact matte plus detached edge-only bleed removal; each 160x80 overlay repairs pure-black export masks only. No crop, shift, packing, redraw, or aperture cutout."
    SOURCE_PACK.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def write_docs(report):
    edge=report['base']['detachedEdgeComponentsRemoved']; removed=[x['opaquePureBlackRemoved'] for x in report['overlays']]
    HANDOFF.write_text(f'''# Alpha 28 / 0696D1R — Observation Window Bounded Cleanup FINAL\n\n## Status\n- Branch: `{BRANCH}`\n- Build: `{NEW_VERSION}`\n- Baseline restored every run: `{BASELINE_COMMIT}` (.64)\n- Visual acceptance: **PENDING-RON-VISUAL**\n\n## Rejections incorporated\n- `.65` rejected: fuzzy matte cleanup clipped real sprite and hollowed the window.\n- internal `.66` was not promoted after self-review found detached edge fragments still visible on the checkerboard preview.\n\n## Final D1R contract\n- full Window remains exactly 160x80; no crop or shift;\n- exact outer matte removal only;\n- detached alpha components touching the canvas edge are removed only when they are separate from the main Window component and <= {MAX_EDGE_BLEED_COMPONENT} pixels;\n- main Window component is never modified by edge-bleed cleanup;\n- 4 animation overlays remain 4 independent 160x80 files;\n- pure-black overlay export masks become alpha=0 only;\n- no hollow aperture and no sprite-strip packing.\n\n## Evidence\n- matte pixels removed: **{report['base']['mattePixelsRemoved']}**\n- detached edge bleed removed: **{report['base']['detachedEdgePixelsRemoved']} px** in `{edge}`\n- overlay black-mask pixels removed: **{removed}**\n- remaining detached edge components: **0**\n\nD2/D3 remain frozen. Technical PASS does not equal visual PASS.\n''',encoding="utf-8")
    LATEST.write_text(f'''# LATEST CARDCHA HANDOFF\n\nUpdated: 2026-09-12\n\n## Current workstream\n`{BRANCH}`\n\nCurrent build candidate:\n`{NEW_VERSION}`\n\nCurrent handoff:\n`handoff/ALPHA28_0696D1R_WINDOW_BOUNDED_CLEANUP.md`\n\n## Status\n- 0696D1 `.65`: **VISUAL REJECTED by Ron** for clipping/hollowing/bleed.\n- D1R internal `.66`: technically passed, but self-review caught detached edge fragments before release.\n- D1R `.67`: final bounded source pass, including detached-edge-component cleanup without touching the main connected Window body.\n- 4 approved animation overlays remain independent 160x80 files.\n- no crop, shift, strip packing, or aperture cutout.\n- Navigation Console is D3; season/time/weather matrix is D2.\n- Visual acceptance: **PENDING-RON-VISUAL**.\n\n## Continuation order\n1. 0696D1R Window bounded source/overlay cleanup — current acceptance gate\n2. 0696D2 Window Environment Matrix Rebuild\n3. 0696D3 Navigation Console Source Cleanup\n4. 0696D4 Deck Integration & Acceptance\n\nDo not proceed to D2 until Ron accepts the Window source geometry/alpha behavior.\n''',encoding="utf-8")


def main():
    baseline_hashes=restore_authoritative_sources()
    orig_base=Image.open(BASE).convert("RGBA"); orig_overlays=[Image.open(p).convert("RGBA") for p in OVERLAYS]
    assert orig_base.size==EXPECTED_SIZE and all(im.size==EXPECTED_SIZE for im in orig_overlays)
    fixed_base,base_stats=clean_base(orig_base); fixed_overlays=[]; overlay_stats=[]
    for i,src in enumerate(orig_overlays,1):
        fixed,stats=sanitize_overlay(src,i); fixed.save(OVERLAYS[i-1]); fixed_overlays.append(fixed); overlay_stats.append(stats)
    fixed_base.save(BASE); WINDOW.mkdir(parents=True,exist_ok=True); fixed_base.save(FRAME)
    update_versions(); update_manifest(); update_source_pack()
    report={"phase":"0696D1R-window-bounded-cleanup-final","branch":BRANCH,"version":NEW_VERSION,"baselineCommit":BASELINE_COMMIT,"technicalValidation":"MATERIALIZED_PENDING_VALIDATOR","visualAcceptance":"PENDING-RON-VISUAL","baselineSourceSha256":baseline_hashes,"base":base_stats,"overlays":overlay_stats,"contracts":{"dimensions":[160,80],"overlayFileCount":4,"cropAllowed":False,"shiftAllowed":False,"stripPackingAllowed":False,"apertureCutoutAllowed":False,"consoleTouched":False,"environmentMatrixTouched":False}}
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); render_preview(orig_base,orig_overlays,fixed_base,fixed_overlays,base_stats); write_docs(report)
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
