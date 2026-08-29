from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json
import re

ROOT = Path("src/Cardcha")
TARGET_VERSION = "0.3.0-alpha.27.0.7.7.4"
WALK_PATH = ROOT / "assets/mimi_walk.png"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def set_version_text(path: Path) -> None:
    text = path.read_text()
    pattern = r"0\.3\.0-alpha\.27\.0\.7\.7(?:\.\d+)?(?!\.\d)"
    text, count = re.subn(pattern, TARGET_VERSION, text)
    if count == 0 and TARGET_VERSION not in text:
        raise AssertionError(f"Could not update version in {path}")
    path.write_text(text)


def patch_binder_status() -> None:
    path = ROOT / "UI/CardchaBinderMenu.cs"
    text = path.read_text()
    text = text.replace('ModEntry.T("binder.status.pick")', 'string.Empty')
    if 'binder.status.pick' in text:
        raise AssertionError("binder.status.pick still requested by CardchaBinderMenu")
    path.write_text(text)


def rebuild_social_mugshot() -> None:
    walk = Image.open(WALK_PATH).convert("RGBA")
    if walk.size != (128, 192):
        raise AssertionError(f"Unexpected mimi_walk size {walk.size}")

    # Use the approved front pose, but crop to head + shoulders so SocialPage reads like
    # a vanilla mugshot instead of a tiny full-body character.
    front = walk.crop((32, 0, 64, 48))
    bust = front.crop((5, 0, 27, 31))
    bust = bust.resize((16, 23), Image.Resampling.NEAREST)
    mug = Image.new("RGBA", (16, 24), (0, 0, 0, 0))
    mug.alpha_composite(bust, (0, 1))
    mug.save(ROOT / "assets/mimi_social_mugshot.png", optimize=True)

    runtime = Image.new("RGBA", (128, 216), (0, 0, 0, 0))
    runtime.alpha_composite(walk, (0, 0))
    runtime.alpha_composite(mug, (0, 192))
    runtime.save(ROOT / "assets/mimi_walk_runtime.png", optimize=True)


def normalize_broom_asset() -> None:
    path = ROOT / "assets/mimi_broom.png"
    source = Image.open(path).convert("RGBA")
    if source.size == (192, 192):
        # Already canonical/native. Do not widen again on the second CI pass.
        return
    if source.size != (128, 192):
        raise AssertionError(f"Unexpected mimi_broom size {source.size}")

    # User-approved replacement is a 4x4 sheet of 32x48 frames. Runtime broom frames are
    # native 48x48, so first restore that geometry frame-by-frame without filtering.
    native = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    for row in range(4):
        for col in range(4):
            frame = source.crop((col * 32, row * 48, (col + 1) * 32, (row + 1) * 48))
            frame = frame.resize((48, 48), Image.Resampling.NEAREST)

            # The user wants MiMi/??? about 30% broader while mounted, but with unchanged height.
            bbox = frame.getchannel("A").getbbox()
            if bbox is not None:
                x0, y0, x1, y1 = bbox
                content = frame.crop(bbox)
                wide_w = max(1, round(content.width * 1.30))
                wide = content.resize((wide_w, content.height), Image.Resampling.NEAREST)
                center_x = (x0 + x1) / 2
                dst_x = round(center_x - wide_w / 2)
                widened_frame = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
                widened_frame.alpha_composite(wide, (dst_x, y0))
                frame = widened_frame

            native.alpha_composite(frame, (col * 48, row * 48))
    native.save(path, optimize=True)


def patch_broom_runtime_scale() -> None:
    path = ROOT / "Services/WorldActorService.cs"
    text = path.read_text()
    old = '''    // The approved alpha.22 broom sheet intentionally draws MiMi/??? about 10% smaller inside\n    // the same 32x48 frame. Compensate at runtime so mounting the broom doesn't shrink her body.\n    private const float MimiBroomNativeScale = MimiNativeScale * 1.10f;'''
    new = '''    // 0.7.7.4 broom art is already widened horizontally by ~30% inside native 48x48 frames.\n    // Keep runtime scale equal to normal MiMi so only width changes; do not inflate her height too.\n    private const float MimiBroomNativeScale = MimiNativeScale;'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("Unexpected MiMi broom scale block")
    path.write_text(text)


def create_stair_sprite() -> None:
    path = ROOT / "assets/mimi_attic_stairs.png"
    im = Image.new("RGBA", (32, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    outline = (48, 26, 50, 255)
    deep = (28, 22, 42, 255)
    purple = (94, 48, 102, 255)
    wood_dark = (92, 50, 39, 255)
    wood = (153, 91, 55, 255)
    wood_light = (205, 139, 74, 255)
    edge = (236, 180, 93, 255)

    # Dark attic opening with wizard-tower trim.
    d.rectangle((4, 1, 27, 18), fill=outline)
    d.rectangle((6, 3, 25, 18), fill=purple)
    d.rectangle((8, 5, 23, 18), fill=deep)
    d.rectangle((3, 17, 28, 20), fill=wood_dark)

    # Five broad steps that widen toward the player, making the direction clearly "up".
    steps = [
        (10, 18, 21, 23),
        (8, 23, 23, 28),
        (6, 28, 25, 33),
        (4, 33, 27, 39),
        (2, 39, 29, 46),
    ]
    for i, rect in enumerate(steps):
        x0, y0, x1, y1 = rect
        d.rectangle(rect, fill=outline)
        d.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=wood if i % 2 == 0 else wood_light)
        d.line((x0 + 2, y0 + 1, x1 - 2, y0 + 1), fill=edge)
        d.line((x0 + 2, y1 - 1, x1 - 2, y1 - 1), fill=wood_dark)

    # Side rails / stringers.
    d.line((3, 19, 1, 46), fill=outline, width=2)
    d.line((28, 19, 30, 46), fill=outline, width=2)
    d.line((5, 20, 3, 45), fill=wood_dark, width=1)
    d.line((26, 20, 28, 45), fill=wood_dark, width=1)
    im.save(path, optimize=True)


def patch_attic_visuals() -> None:
    path = ROOT / "Services/MimiAtticVisualService.cs"
    text = path.read_text()

    text = text.replace('private const string DecorVersion = "alpha.27.0.7.7";', 'private const string DecorVersion = "alpha.27.0.7.7.4";')

    if 'private const string StairSpritePath = "assets/mimi_attic_stairs.png";' not in text:
        text = replace_once(
            text,
            '    private const string DecorMarkerKey = "Ronvotri.Cardcha/MiMiAtticDecor";\n',
            '    private const string DecorMarkerKey = "Ronvotri.Cardcha/MiMiAtticDecor";\n    private const string StairSpritePath = "assets/mimi_attic_stairs.png";\n',
            "stair sprite constant",
        )

    old_wizard = '''        if (location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))\n            DrawStairMarker(e.SpriteBatch, MimiHomeService.ResolvePreferredWizardStairTile(location));'''
    new_wizard = '''        if (location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))\n        {\n            Point stair = MimiHomeService.ResolvePreferredWizardStairTile(location);\n            PrepareWizardStairArea(location, stair);\n            this.DrawStairMarker(e.SpriteBatch, stair);\n        }'''
    if old_wizard in text:
        text = text.replace(old_wizard, new_wizard, 1)
    elif new_wizard not in text:
        raise AssertionError("Unexpected WizardHouse stair render block")

    text = text.replace(
        'TryAddFurniture(attic, "(F)432", 2, 10, rotation: 2);    // Couch near the wall with usable viewing distance.',
        'TryAddFurniture(attic, "(F)432", 2, 11, rotation: 2);    // Couch tight to the bottom wall, centered beneath the TV.',
    )

    old_marker = '''    private static void DrawStairMarker(SpriteBatch batch, Point tile)\n    {\n        try\n        {\n            Item staircase = ItemRegistry.Create("(O)71"); // vanilla Staircase object\n            Vector2 world = new(tile.X * 64f, tile.Y * 64f);\n            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);\n            staircase.drawInMenu(batch, screen, 1f, 0.96f, 0.995f, StackDrawType.Hide);\n        }\n        catch\n        {\n            // Access remains functional if another mod replaces/removes the vanilla decorative icon.\n        }\n    }'''
    new_marker = '''    private static void PrepareWizardStairArea(GameLocation location, Point tile)\n    {\n        // The old marker sat beside decorative plant/wall tiles and could visually/collision-wise\n        // pinch the player into the wall. Reserve a clean 2x3 opening for the real stair graphic.\n        foreach (string layerName in new[] { "Buildings", "Front" })\n        {\n            var layer = location.Map?.GetLayer(layerName);\n            if (layer is null)\n                continue;\n\n            for (int x = tile.X - 1; x <= tile.X; x++)\n            {\n                for (int y = tile.Y - 2; y <= tile.Y; y++)\n                {\n                    if (x >= 0 && y >= 0 && x < layer.LayerWidth && y < layer.LayerHeight)\n                        layer.Tiles[x, y] = null;\n                }\n            }\n        }\n    }\n\n    private void DrawStairMarker(SpriteBatch batch, Point tile)\n    {\n        try\n        {\n            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n            Vector2 world = new(tile.X * 64f - 32f, (tile.Y - 2) * 64f);\n            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);\n            batch.Draw(staircase, screen, null, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.995f);\n        }\n        catch\n        {\n            // The actual warp still works if the visual asset can't be loaded.\n        }\n    }'''
    if old_marker in text:
        text = text.replace(old_marker, new_marker, 1)
    elif new_marker not in text:
        raise AssertionError("Unexpected DrawStairMarker block")

    path.write_text(text)


def patch_attic_warps() -> None:
    path = ROOT / "Services/MimiHomeService.cs"
    text = path.read_text()

    old = '''            GameLocation? wizard = Game1.getLocationFromName("WizardHouse");\n            Point target = wizard is null ? new Point(4, 6) : this.ResolveWizardStairTile(wizard);\n            Game1.warpFarmer("WizardHouse", target.X, Math.Min(target.Y + 1, Math.Max(1, wizard?.Map?.Layers.FirstOrDefault()?.LayerHeight - 2 ?? target.Y + 1)), 2);'''
    new = '''            GameLocation? wizard = Game1.getLocationFromName("WizardHouse");\n            Point target = wizard is null ? new Point(4, 6) : this.ResolveWizardStairTile(wizard);\n            Point landing = wizard is null ? new Point(target.X, target.Y + 1) : ResolveWizardLandingTile(wizard, target);\n            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);'''
    if old in text:
        text = text.replace(old, new, 1)

    old2 = '''            Point target = this.ResolveWizardStairTile(wizard);\n            int targetY = Math.Min(\n                target.Y + 1,\n                Math.Max(1, wizard.Map?.Layers.FirstOrDefault()?.LayerHeight - 2 ?? target.Y + 1)\n            );\n            Game1.warpFarmer("WizardHouse", target.X, targetY, 2);'''
    new2 = '''            Point target = this.ResolveWizardStairTile(wizard);\n            Point landing = ResolveWizardLandingTile(wizard, target);\n            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);'''
    if old2 in text:
        text = text.replace(old2, new2, 1)

    old3 = '''        Point target = this.ResolveWizardStairTile(wizard);\n        int targetY = Math.Min(\n            target.Y + 1,\n            Math.Max(1, wizard.Map?.Layers.FirstOrDefault()?.LayerHeight - 2 ?? target.Y + 1)\n        );\n        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;\n        Game1.warpFarmer("WizardHouse", target.X, targetY, 2);'''
    new3 = '''        Point target = this.ResolveWizardStairTile(wizard);\n        Point landing = ResolveWizardLandingTile(wizard, target);\n        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;\n        Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);'''
    if old3 in text:
        text = text.replace(old3, new3, 1)

    helper = '''    private static Point ResolveWizardLandingTile(GameLocation wizard, Point stair)\n    {\n        Point[] candidates =\n        {\n            new(stair.X, stair.Y + 1),\n            new(stair.X, stair.Y + 2),\n            new(stair.X - 1, stair.Y + 1),\n            new(stair.X + 1, stair.Y + 1),\n            new(stair.X - 1, stair.Y + 2),\n            new(stair.X + 1, stair.Y + 2),\n            new(stair.X, stair.Y + 3)\n        };\n\n        foreach (Point candidate in candidates)\n        {\n            if (IsTileClear(wizard, candidate))\n                return candidate;\n        }\n\n        return FindClearTileNear(wizard, new Point(stair.X, stair.Y + 2));\n    }\n\n'''
    marker = '    private Point ResolveAtticStairTile(GameLocation attic)\n'
    if helper not in text:
        if marker not in text:
            raise AssertionError("Could not locate ResolveAtticStairTile for landing helper insertion")
        text = text.replace(marker, helper + marker, 1)

    text = text.replace(
        "Created MiMi attic location '{AtticLocationName}' using the alpha.27.0.7.4 strict-TMX map hotfix with guarded runtime access.",
        "Created MiMi attic location '{AtticLocationName}' using the alpha.27.0.7.7.4 stair-safe attic build.",
    )

    if 'targetY' in text and 'warpFarmer("WizardHouse", target.X, targetY' in text:
        raise AssertionError("An old unsafe WizardHouse targetY warp remains")
    path.write_text(text)


def patch_attic_tmx_version() -> None:
    path = ROOT / "assets/mimi_attic.tmx"
    text = path.read_text()
    text = text.replace('CardchaAtticVersion" value="alpha.27.0.7.7"', 'CardchaAtticVersion" value="alpha.27.0.7.7.4"')
    path.write_text(text)


def patch_versions() -> None:
    for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        set_version_text(ROOT / rel)
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest["Version"] = TARGET_VERSION
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


walk_before = hashlib.sha256(WALK_PATH.read_bytes()).hexdigest()
patch_binder_status()
rebuild_social_mugshot()
normalize_broom_asset()
patch_broom_runtime_scale()
create_stair_sprite()
patch_attic_visuals()
patch_attic_warps()
patch_attic_tmx_version()
patch_versions()
walk_after = hashlib.sha256(WALK_PATH.read_bytes()).hexdigest()
if walk_after != walk_before:
    raise AssertionError("mimi_walk.png changed unexpectedly")
print("0.7.7.4 candidate applied; locked mimi_walk preserved:", walk_after)
