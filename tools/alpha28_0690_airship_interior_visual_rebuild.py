#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.56"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.57"
BRANCH = "cardcha-alpha28-0690-airship-interior-visual-rebuild"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    if not p.exists():
        continue
    s = read(p).replace(OLD_VERSION, NEW_VERSION)
    if rel == "ModEntry.cs":
        s = s.replace("0688 HOLLOW CURATOR VISUAL IDENTITY REBUILD TEST", "0690 AIRSHIP INTERIOR VISUAL REBUILD TEST")
    write(p, s)

def csv_values(layer: ET.Element) -> list[int]:
    data = layer.find("data")
    if data is None or data.attrib.get("encoding") != "csv":
        raise RuntimeError(f"layer {layer.attrib.get('name')} is not CSV")
    toks = [x.strip() for x in (data.text or "").split(",")]
    if not toks or any(x == "" for x in toks):
        raise RuntimeError(f"empty CSV token in layer {layer.attrib.get('name')}")
    return [int(x) for x in toks]

def set_csv(layer: ET.Element, vals: list[int]) -> None:
    data = layer.find("data")
    assert data is not None
    data.text = "\n" + ",".join(str(x) for x in vals) + "\n"

def get_layer(root: ET.Element, name: str) -> ET.Element:
    for layer in root.findall("layer"):
        if layer.attrib.get("name") == name:
            return layer
    raise RuntimeError(f"missing layer {name}")

def remove_tileset(root: ET.Element, name: str) -> None:
    for ts in list(root.findall("tileset")):
        if ts.attrib.get("name") == name:
            root.remove(ts)

def add_tileset(root: ET.Element, firstgid: int, name: str, source: str, width: int, height: int, blocker: bool=False) -> None:
    remove_tileset(root, name)
    ts = ET.Element("tileset", {
        "firstgid": str(firstgid),
        "name": name,
        "tilewidth": "16",
        "tileheight": "16",
        "tilecount": str((width // 16) * (height // 16)),
        "columns": str(width // 16),
    })
    ET.SubElement(ts, "image", {"source": source, "width": str(width), "height": str(height)})
    if blocker:
        tile = ET.SubElement(ts, "tile", {"id": "0"})
        props = ET.SubElement(tile, "properties")
        ET.SubElement(props, "property", {"name": "Passable", "value": "F"})
    children = list(root)
    layer_index = next((i for i,c in enumerate(children) if c.tag == "layer"), len(children))
    root.insert(layer_index, ts)

def blit_asset(root: ET.Element, layer_name: str, firstgid: int, asset: Path, x: int, y: int) -> None:
    from PIL import Image
    im = Image.open(asset).convert("RGBA")
    cols, rows = im.width // 16, im.height // 16
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    layer = get_layer(root, layer_name)
    vals = csv_values(layer)
    if len(vals) != w*h:
        raise RuntimeError(f"{layer_name} expected {w*h} tiles, got {len(vals)}")
    for ty in range(rows):
        for tx in range(cols):
            tile = im.crop((tx*16, ty*16, tx*16+16, ty*16+16))
            if tile.getchannel("A").getbbox() is None:
                continue
            mx, my = x+tx, y+ty
            if not (0 <= mx < w and 0 <= my < h):
                raise RuntimeError(f"{asset.name} placement outside map at {mx},{my}")
            vals[my*w+mx] = firstgid + ty*cols + tx
    set_csv(layer, vals)

def add_blockers(root: ET.Element, blocker_gid: int, cells: list[tuple[int,int]]) -> None:
    w, h = int(root.attrib["width"]), int(root.attrib["height"])
    layer = get_layer(root, "Buildings")
    vals = csv_values(layer)
    for x,y in cells:
        if not (0 <= x < w and 0 <= y < h):
            raise RuntimeError(f"blocker outside map {x},{y}")
        idx = y*w+x
        if vals[idx] == 0:
            vals[idx] = blocker_gid
    set_csv(layer, vals)

ASSET = SRC / "assets/airship_props/set01_redux"

dock_path = SRC / "assets/sky_dock_interior.tmx"
dock = ET.parse(dock_path)
r = dock.getroot()
add_tileset(r, 5000, "CardchaRouteNoticeBoard0690", "airship_props/set01_redux/route_notice_board.png", 80, 80)
add_tileset(r, 5100, "CardchaBoardingGate0690", "airship_props/set01_redux/boarding_gate_arch.png", 112, 96)
add_tileset(r, 5200, "CardchaSignalLamp0690", "airship_props/set01_redux/signal_lamp.png", 32, 48)
add_tileset(r, 5300, "CardchaCargoCrate0690", "airship_props/set01_redux/cargo_parcel_crate.png", 48, 48)
add_tileset(r, 5400, "CardchaCollision0690", "airship_props/set01_redux/collision_blocker.png", 16, 16, blocker=True)
blit_asset(r, "BackDecor", 5000, ASSET/"route_notice_board.png", 2, 3)
blit_asset(r, "BackDecor", 5100, ASSET/"boarding_gate_arch.png", 20, 3)
blit_asset(r, "BackDecor", 5200, ASSET/"signal_lamp.png", 17, 4)
blit_asset(r, "BackDecor", 5300, ASSET/"cargo_parcel_crate.png", 26, 10)
dock_blockers = []
dock_blockers += [(x,y) for y in (6,7) for x in range(2,7)]
dock_blockers += [(20,y) for y in range(5,9)] + [(26,y) for y in range(5,9)]
dock_blockers += [(x,y) for y in range(11,13) for x in range(26,29)]
add_blockers(r, 5400, dock_blockers)
ET.indent(dock, space=" ")
dock.write(dock_path, encoding="UTF-8", xml_declaration=True)

deck_path = SRC / "assets/airship_deck.tmx"
deck = ET.parse(deck_path)
r = deck.getroot()
add_tileset(r, 5000, "CardchaObservationWindow0690", "airship_props/set01_redux/observation_window_base.png", 160, 80)
add_tileset(r, 5100, "CardchaNavigationConsole0690", "airship_props/set01_redux/navigation_console_base.png", 112, 80)
add_tileset(r, 5200, "CardchaSignalLamp0690", "airship_props/set01_redux/signal_lamp.png", 32, 48)
add_tileset(r, 5400, "CardchaCollision0690", "airship_props/set01_redux/collision_blocker.png", 16, 16, blocker=True)
blit_asset(r, "BackDecor", 5000, ASSET/"observation_window_base.png", 7, 1)
blit_asset(r, "BackDecor", 5100, ASSET/"navigation_console_base.png", 9, 5)
blit_asset(r, "BackDecor", 5200, ASSET/"signal_lamp.png", 4, 4)
blit_asset(r, "BackDecor", 5200, ASSET/"signal_lamp.png", 18, 4)
add_blockers(r, 5400, [(x,y) for y in (8,9) for x in range(9,16)])
ET.indent(deck, space=" ")
deck.write(deck_path, encoding="UTF-8", xml_declaration=True)

service = SRC / "Services/AirshipFoundationService.cs"
s = read(service)
deck_re = re.compile(r"private void EnsureDeckVanillaFurniture\(GameLocation deck\)\s*\{.*?\n\}\n\nprivate void EnsureSkyDockVanillaFurniture", re.S)
deck_repl = '''private void EnsureDeckVanillaFurniture(GameLocation deck)
{
    if (ReferenceEquals(this.DeckDecorAppliedLocation, deck)
        && deck.modData.TryGetValue(InteriorDecorMarkerKey, out string? version)
        && string.Equals(version, InteriorDecorVersion + "-0690-bridge", StringComparison.Ordinal))
        return;

    this.DeckDecorAppliedLocation = deck;
    ClearInteriorDecor(deck);
    // 0690: physical bridge furnishings are authored into airship_deck.tmx.
    deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0690-bridge";
}

private void EnsureSkyDockVanillaFurniture'''
s, count = deck_re.subn(deck_repl, s, count=1)
if count != 1:
    raise RuntimeError("could not replace EnsureDeckVanillaFurniture")
dock_re = re.compile(r"private void EnsureSkyDockVanillaFurniture\(GameLocation dock\)\s*\{.*?\n\}\n\nprivate static void ClearInteriorDecor", re.S)
dock_repl = '''private void EnsureSkyDockVanillaFurniture(GameLocation dock)
{
    if (ReferenceEquals(this.SkyDockDecorAppliedLocation, dock)
        && dock.modData.TryGetValue(InteriorDecorMarkerKey, out string? version)
        && string.Equals(version, InteriorDecorVersion + "-0690-dock", StringComparison.Ordinal))
        return;

    this.SkyDockDecorAppliedLocation = dock;
    ClearInteriorDecor(dock);
    // 0690: physical dock furnishings are authored into sky_dock_interior.tmx.
    dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0690-dock";
}

private static void ClearInteriorDecor'''
s, count = dock_re.subn(dock_repl, s, count=1)
if count != 1:
    raise RuntimeError("could not replace EnsureSkyDockVanillaFurniture")
write(service, s)

renderer = SRC / "Services/AirshipInteriorStardewRenderer.cs"
s = read(renderer)
needle = 'private const string HubDecorAtlasPath = "assets/airship_hub_decor.png";'
insert = '''private const string HubDecorAtlasPath = "assets/airship_hub_decor.png";
    private const string PropRoot0690 = "assets/airship_props/set01_redux";
    private static readonly string[] WindowOverlayPaths0690 =
    {
        PropRoot0690 + "/observation_window_overlay_1.png",
        PropRoot0690 + "/observation_window_overlay_2.png",
        PropRoot0690 + "/observation_window_overlay_3.png",
        PropRoot0690 + "/observation_window_overlay_4.png",
    };
    private static readonly string[] ConsoleOverlayPaths0690 =
    {
        PropRoot0690 + "/navigation_console_overlay_1.png",
        PropRoot0690 + "/navigation_console_overlay_2.png",
        PropRoot0690 + "/navigation_console_overlay_3.png",
        PropRoot0690 + "/navigation_console_overlay_4.png",
    };
    private static readonly Texture2D?[] WindowOverlays0690 = new Texture2D?[4];
    private static readonly Texture2D?[] ConsoleOverlays0690 = new Texture2D?[4];'''
if needle not in s:
    raise RuntimeError("renderer constant anchor missing")
s = s.replace(needle, insert, 1)
deck_anchor = '''        float phase = (float)(Environment.TickCount64 / 1000.0);
        DrawWindowMagic(batch, phase);'''
deck_insert = '''        float phase = (float)(Environment.TickCount64 / 1000.0);
        Draw0690WindowOverlay(batch);
        Draw0690ConsoleOverlay(batch);
        DrawWindowMagic(batch, phase);'''
if deck_anchor not in s:
    raise RuntimeError("TryDrawDeck anchor missing")
s = s.replace(deck_anchor, deck_insert, 1)
method_anchor = '    private static void DrawWindowMagic(SpriteBatch batch, float phase)\n'
new_methods = '''    private static Texture2D? Get0690Overlay(Texture2D?[] cache, string[] paths, int index)
    {
        if (index < 0 || index >= cache.Length || ModEntry.StaticHelper is null)
            return null;
        Texture2D? current = cache[index];
        if (current is not null && !current.IsDisposed)
            return current;
        try
        {
            cache[index] = ModEntry.StaticHelper.ModContent.Load<Texture2D>(paths[index]);
            return cache[index];
        }
        catch
        {
            return null;
        }
    }

    private static void Draw0690WindowOverlay(SpriteBatch batch)
    {
        int frame = (int)((Environment.TickCount64 / 900L) % 4L);
        Texture2D? texture = Get0690Overlay(WindowOverlays0690, WindowOverlayPaths0690, frame);
        if (texture is null)
            return;
        Vector2 topLeft = WorldToScreen(7f * 64f, 1f * 64f);
        batch.Draw(texture,
            new Rectangle((int)topLeft.X, (int)topLeft.Y, texture.Width * 4, texture.Height * 4),
            null, Color.White, 0f, Vector2.Zero, SpriteEffects.None, 0.885f);
    }

    private static void Draw0690ConsoleOverlay(SpriteBatch batch)
    {
        int frame = (int)((Environment.TickCount64 / 1150L) % 4L);
        Texture2D? texture = Get0690Overlay(ConsoleOverlays0690, ConsoleOverlayPaths0690, frame);
        if (texture is null)
            return;
        Vector2 topLeft = WorldToScreen(9f * 64f, 5f * 64f);
        batch.Draw(texture,
            new Rectangle((int)topLeft.X, (int)topLeft.Y, texture.Width * 4, texture.Height * 4),
            null, Color.White, 0f, Vector2.Zero, SpriteEffects.None, 0.886f);
    }

'''
if method_anchor not in s:
    raise RuntimeError("renderer method anchor missing")
s = s.replace(method_anchor, new_methods + method_anchor, 1)
write(renderer, s)

audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(read(audit_path))
audit["branch"] = BRANCH
done = audit.setdefault("completedDepthMigrations", [])
marker = "0690 Airship Set01 physical props->TMX; window/console motion->VFX-only overlays"
if marker not in done:
    done.append(marker)
write(audit_path, json.dumps(audit, indent=2) + "\n")

handoff = ROOT / "handoff/ALPHA28_0690_AIRSHIP_INTERIOR_VISUAL_REBUILD.md"
handoff.write_text(f'''# Alpha 28 0690 — Airship Interior Visual Rebuild

Source-of-truth parent: `55157c903f0e45cd29df2711ac8e12b32d8fbb4f` (0688)

Build: `{NEW_VERSION}`

## Purpose
Replace the temporary/vanilla-looking Airship Deck + Sky Dock furniture language with the approved Cardcha wood/brass/purple/teal visual identity.

## 0690 Set 01
- Route Notice Board: map-native physical art.
- Boarding Gate Arch: map-native physical art with open center lane.
- Signal Lamp: map-native physical art.
- Cargo Parcel Crate: map-native physical art.
- Observation Window: map-native body + VFX-only moving sky panes.
- Navigation Command Console: map-native body + VFX-only four-state screen.

## Rendering contract
- Static physical art is owned by `airship_deck.tmx` / `sky_dock_interior.tmx`.
- Runtime only draws transparent sky/screen pixels.
- Old 0677 vanilla furniture clutter is cleared from these two rooms.
- Boss and Region content inherited from 0688 is frozen by CI.

## Layout
Sky Dock: route/service identity left, boarding gate right, center arrival/exit spine preserved.
Airship Deck: observation wall at top, navigation console centered on the existing helm role, lower doorway preserved.

## Acceptance state
CI/compile/package validation is authoritative for this handoff. In-game visual acceptance is pending Ron's later test.
''', encoding="utf-8")

latest = ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md"
latest.write_text(f'''# Latest Cardcha Handoff

Current source-of-truth branch: `{BRANCH}`

Current build: `{NEW_VERSION}`

Current handoff: `handoff/ALPHA28_0690_AIRSHIP_INTERIOR_VISUAL_REBUILD.md`

Parent source-of-truth: `cardcha-alpha28-0688-hollow-curator-visual-identity-rebuild` @ `55157c903f0e45cd29df2711ac8e12b32d8fbb4f`

Status: Airship Set 01 physical visual rebuild integrated; in-game visual acceptance pending.
''', encoding="utf-8")

print("0690 Airship interior visual rebuild integrated.")
