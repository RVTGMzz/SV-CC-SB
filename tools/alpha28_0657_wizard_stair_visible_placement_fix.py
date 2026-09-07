from pathlib import Path
import base64
import json

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.23"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.24"

# Exact pre-0655 ladder artwork from the last build where the ladder was visibly present in-game.
# Do not pixel-shift this sheet again. Placement belongs to the map tile anchor, not PNG surgery.
VISIBLE_STAIR_B64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAABACAYAAAATffeWAAAAjklEQVR42mNgoBAwMjAwMOhKiv/HJnn5+UuC8kyUuoA6BsCcmuMozLCgTAvF+ejy8nwsKGJMVAlEfAGFC8BcwIIuAfMCLpDQdQ2Fj2HAmdMv6esFlEBEjwVkjB4L1E0Ho9E4Go2j0TgajaPROBqNo9E4Go2j0TgajaPROBqNWKIRpwuQ+4345AdJ15cSAACnlfYWVssoWwAAAABJRU5ErkJggg=="


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"0657 {label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def set_version() -> None:
    manifest = CARDCHA / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("Version") != OLD_VERSION:
        raise RuntimeError(f"0657 expected manifest {OLD_VERSION}, got {data.get('Version')}")
    data["Version"] = NEW_VERSION
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rel in ["Cardcha.csproj", "Directory.Build.targets"]:
        path = CARDCHA / rel
        text = path.read_text(encoding="utf-8")
        if OLD_VERSION not in text:
            raise RuntimeError(f"0657 version anchor missing in {rel}")
        path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")

    mod_entry = CARDCHA / "ModEntry.cs"
    text = mod_entry.read_text(encoding="utf-8")
    if OLD_VERSION in text:
        text = text.replace(OLD_VERSION, NEW_VERSION)
        mod_entry.write_text(text, encoding="utf-8")


def restore_visible_stair_art() -> None:
    stair = CARDCHA / "assets" / "mimi_attic_stairs.png"
    raw = base64.b64decode(VISIBLE_STAIR_B64)
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("0657 stair payload is not a PNG")
    stair.write_bytes(raw)


def keep_known_visible_anchor() -> None:
    home = CARDCHA / "Services" / "MimiHomeService.cs"
    text = home.read_text(encoding="utf-8")
    start = text.index("    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)")
    end = text.index("    private static Point ResolveWizardLandingTile", start)
    old_block = text[start:end]
    if "return new Point(15, 15);" not in old_block:
        raise RuntimeError("0657 expected existing x15 Wizard stair anchor")
    new_block = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0657: preserve the last in-game-visible WizardHouse stair column. The regression was\n        // introduced by changing the stair artwork/caching, not by this gameplay anchor. Keep\n        // visual, collision, interaction, ascent and return landing tied to the same x15 route.\n        return new Point(15, 15);\n    }\n\n'''
    text = text[:start] + new_block + text[end:]
    home.write_text(text, encoding="utf-8")


def harden_runtime_stair_install() -> None:
    path = CARDCHA / "Services" / "MimiAtticVisualService.cs"
    text = path.read_text(encoding="utf-8")
    start = text.index("    private void EnsureWizardStairMapTiles(GameLocation location, Point tile)")
    end = text.index("    private static AtticLayout GetLayout", start)
    replacement = r'''    private void EnsureWizardStairMapTiles(GameLocation location, Point tile)
    {
        try
        {
            xTile.Map? map = location.Map;
            if (map is null)
                return;

            var buildings = map.GetLayer("Buildings");
            if (buildings is null)
                return;

            const string tileSheetId = "z_cardcha_mimi_attic_stairs";
            TileSheet? stairSheet = map.GetTileSheet(tileSheetId);
            if (stairSheet is null)
            {
                string imageSource = this.Helper.ModContent.GetInternalAssetName(StairSpritePath).Name;
                stairSheet = new TileSheet(
                    tileSheetId,
                    map,
                    imageSource,
                    new xTile.Dimensions.Size(1, 4),
                    new xTile.Dimensions.Size(16, 16)
                );
                map.AddTileSheet(stairSheet);
                map.LoadTileSheets(Game1.mapDisplayDevice);
            }

            int x = tile.X;
            int firstY = tile.Y - 4;
            if (x < 0 || x >= buildings.LayerWidth || firstY < 0 || tile.Y - 1 >= buildings.LayerHeight)
            {
                ModEntry.StaticMonitor?.Log(
                    $"MiMi stair target {x},{tile.Y} is outside WizardHouse Buildings layer {buildings.LayerWidth}x{buildings.LayerHeight}; stair was not installed.",
                    StardewModdingAPI.LogLevel.Warn
                );
                return;
            }

            // Do not trust a map-reference cache by itself. A live map can be mutated/reloaded by
            // another content mod while keeping the same object. Verify all four actual ladder
            // segments are still present; only reinstall when something is missing or replaced.
            bool complete = true;
            for (int segment = 0; segment < 4; segment++)
            {
                int y = firstY + segment;
                Tile? existing = buildings.Tiles[x, y];
                if (existing is null
                    || !ReferenceEquals(existing.TileSheet, stairSheet)
                    || existing.TileIndex != segment)
                {
                    complete = false;
                    break;
                }
            }

            if (complete)
            {
                this.WizardStairAppliedMap = map;
                return;
            }

            // SVE/other WizardHouse edits can place foreground tiles over this interior strip.
            // Clear only foreground layers at the four ladder cells. Never touch Back/floor art.
            var front = map.GetLayer("Front");
            var alwaysFront = map.GetLayer("AlwaysFront");
            var front2 = map.GetLayer("Front2");

            for (int segment = 0; segment < 4; segment++)
            {
                int y = firstY + segment;

                if (front is not null && x < front.LayerWidth && y < front.LayerHeight)
                    front.Tiles[x, y] = null;
                if (alwaysFront is not null && x < alwaysFront.LayerWidth && y < alwaysFront.LayerHeight)
                    alwaysFront.Tiles[x, y] = null;
                if (front2 is not null && x < front2.LayerWidth && y < front2.LayerHeight)
                    front2.Tiles[x, y] = null;

                // Real Buildings-layer tiles keep the stair in the room's normal world draw order.
                // No RenderedWorld overlay and no pixel-shifted art.
                buildings.Tiles[x, y] = new StaticTile(buildings, stairSheet, BlendMode.Alpha, segment);
            }

            this.WizardStairAppliedMap = map;
            ModEntry.StaticMonitor?.Log(
                $"MiMi WizardHouse stair installed visibly at column x={x}, y={firstY}..{firstY + 3} using the restored 0653 artwork.",
                StardewModdingAPI.LogLevel.Trace
            );
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log(
                $"WizardHouse MiMi stair map-layer install failed safely: {ex.Message}",
                StardewModdingAPI.LogLevel.Warn
            );
        }
    }

'''
    text = text[:start] + replacement + text[end:]
    path.write_text(text, encoding="utf-8")


def write_handoff() -> None:
    handoff = ROOT / "handoff" / "ALPHA28_0657_WIZARD_STAIR_VISIBLE_PLACEMENT_FIX.md"
    handoff.write_text(f'''# Alpha28 0657 - Wizard stair visible placement fix

Branch: `cardcha-alpha28-0657-wizard-stair-visible-placement-fix`

Build target: `{NEW_VERSION}`

## User-reported regression
- In 0655/0656 the WizardHouse ladder is not visibly present in the intended right-side interior strip.
- Do not infer a new left/right tile from the screenshot. The last visibly working presentation was the pre-0655 art on the x15 route.

## 0657 fix
- Keep the canonical Wizard stair gameplay anchor `(15,15)` so ascent, collision/interaction and return landing remain one route.
- Restore `mimi_attic_stairs.png` byte-for-byte to the pre-0655 / 0653 visible artwork. Remove the rejected one-source-pixel PNG nudge.
- Replace the map-reference-only render cache with verification of all four real Buildings-layer stair segments.
- If a live WizardHouse map mutates/reloads and any segment disappears, reinstall the four ladder tiles.
- Clear only `Front`, `AlwaysFront`, and `Front2` at those four stair cells so foreign foreground content cannot completely cover the ladder. Back/floor art is untouched.
- Continue using real map tiles, not a post-world overlay, so the ladder stays in normal Stardew world draw order.

## Preserved from 0656
- Community Center MiMi work tile cache / ghosting fix.
- Community Center continuity dialogue and route cache refresh.
- MiMi Gift Log native 16x32 profile sprite pipeline.
- 0653 strict TMX runtime compatibility fix.

## In-game acceptance pending
- Ladder must be clearly visible inside WizardHouse in the right-side strip near the wall.
- Ladder must not require a separate invisible exit route.
- Entering and returning from the attic must use the same stair route.
''', encoding="utf-8")

    latest = ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(f'''# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0657-wizard-stair-visible-placement-fix`

Current build target:
`{NEW_VERSION}`

Read first:
- `handoff/ALPHA28_0657_WIZARD_STAIR_VISIBLE_PLACEMENT_FIX.md`
- `handoff/ALPHA28_0656_MIMI_COMMUNITY_CENTER_STABILITY_DIALOGUE.md`
- `handoff/ALPHA28_0655_MIMI_NATIVE_PROFILE_STAIR_ANCHOR_FIX.md`
- `handoff/ALPHA28_0653_TMX_RUNTIME_COMPAT_FIX.md`
- `handoff/BOSS_CONCEPT_CANON.md`

## Current acceptance state
- 0657 restores the last visibly working ladder artwork and verifies/reinstalls its four WizardHouse map tiles instead of guessing a new coordinate. In-game acceptance pending.
- 0656 Community Center MiMi stability/dialogue fix remains included.
- 0655 MiMi native Gift Log/Profile pipeline remains included; final visual acceptance still depends on user screenshot.
- Hunt Run/Boss I systems remain implemented and unchanged by 0657.

## Locked regression guard
Save schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate/collision; Airship route/visual; MiMi HOME/TV/LATE and attic furniture/layout; card canon; controller profile.
''', encoding="utf-8")


set_version()
restore_visible_stair_art()
keep_known_visible_anchor()
harden_runtime_stair_install()
write_handoff()
print("0657 Wizard stair visible placement generator complete", NEW_VERSION)
