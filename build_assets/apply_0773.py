from pathlib import Path
from PIL import Image
import hashlib
import json
import re

ROOT = Path("src/Cardcha")
TARGET_VERSION = "0.3.0-alpha.27.0.7.7.3"
WALK_PATH = ROOT / "assets/mimi_walk.png"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def set_version_text(path: Path) -> None:
    text = path.read_text()
    if TARGET_VERSION in text:
        return
    pattern = r"0\.3\.0-alpha\.27\.0\.7\.7(?:\.2)?(?!\.\d)"
    text, count = re.subn(pattern, TARGET_VERSION, text)
    if count == 0:
        raise AssertionError(f"Could not update version in {path}")
    path.write_text(text)


def patch_binder() -> None:
    path = ROOT / "UI/CardchaBinderMenu.cs"
    text = path.read_text()
    if "binder.status.preview" not in text:
        return

    text = replace_once(
        text,
        '''        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n            ? ModEntry.T("binder.status.preview", new { name = card.Name })\n            : ModEntry.T("binder.status.not-owned");''',
        '''        this.Status = this.Save.Data.OwnedCards.Contains(card.Id)\n            ? ModEntry.T("binder.status.pick")\n            : ModEntry.T("binder.status.not-owned");''',
        "Binder preview status assignment",
    )

    text = replace_once(
        text,
        '''        if (owned)\n        {\n            Rectangle viewingArea = new(nameArea.X + nameArea.Width / 2, nameArea.Bottom, nameArea.Width / 2, 27);\n            string viewing = ModEntry.T("binder.status.preview", new { name = this.Selected.Name });\n            this.DrawRightAlignedSingleLine(b, viewing, viewingArea, Color.DarkSlateGray);\n        }\n''',
        "",
        "Binder right-page preview draw",
    )

    text = replace_once(
        text,
        '''        if (this.Selected is not null)\n        {\n            string preview = ModEntry.T("binder.status.preview", new { name = this.Selected.Name });\n            string selected = ModEntry.T("binder.status.selected", new { name = this.Selected.Name });\n            if (this.Status == preview || this.Status == selected)\n                return;\n        }''',
        '''        if (this.Selected is not null)\n        {\n            string selected = ModEntry.T("binder.status.selected", new { name = this.Selected.Name });\n            if (this.Status == selected)\n                return;\n        }''',
        "Binder preview guard",
    )

    if "binder.status.preview" in text:
        raise AssertionError("Binder still requests binder.status.preview")
    path.write_text(text)


def patch_world_actor() -> None:
    path = ROOT / "Services/WorldActorService.cs"
    text = path.read_text()

    if "int spriteWidth = broom ? 48 : 32;" not in text:
        text = replace_once(
            text,
            '''        if (actor.Sprite is null\n            || actor.Sprite.SpriteWidth != 32\n            || actor.Sprite.SpriteHeight != 48\n            || !string.Equals(actor.Sprite.loadedTexture, asset, StringComparison.OrdinalIgnoreCase))\n        {\n            actor.Sprite = new AnimatedSprite(asset, 0, 32, 48);\n        }''',
            '''        int spriteWidth = broom ? 48 : 32;\n        const int spriteHeight = 48;\n        if (actor.Sprite is null\n            || actor.Sprite.SpriteWidth != spriteWidth\n            || actor.Sprite.SpriteHeight != spriteHeight\n            || !string.Equals(actor.Sprite.loadedTexture, asset, StringComparison.OrdinalIgnoreCase))\n        {\n            actor.Sprite = new AnimatedSprite(asset, 0, spriteWidth, spriteHeight);\n        }''',
            "MiMi native broom frame size",
        )

    if "MimiProfileCharacterAsset" not in text:
        text = replace_once(
            text,
            '    public const string MimiBroomCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Broom";\n',
            '    public const string MimiBroomCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Broom";\n'
            '    public const string MimiProfileCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Profile";\n',
            "MiMi profile character asset constant",
        )
        text = replace_once(
            text,
            '    private const string MimiBroomSheetPath = "assets/mimi_broom.png";\n',
            '    private const string MimiBroomSheetPath = "assets/mimi_broom.png";\n'
            '    private const string MimiProfileSheetPath = "assets/mimi_profile.png";\n',
            "MiMi profile sheet path constant",
        )
        text = replace_once(
            text,
            '''    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)\n    {\n''',
            '''    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)\n    {\n        if (e.Name.IsEquivalentTo(MimiProfileCharacterAsset))\n        {\n            e.LoadFromModFile<Texture2D>(MimiProfileSheetPath, AssetLoadPriority.Medium);\n            return;\n        }\n\n''',
            "MiMi profile asset handler",
        )

    path.write_text(text)


def rebuild_broom() -> None:
    path = ROOT / "assets/mimi_broom.png"
    with Image.open(path) as image:
        image = image.convert("RGBA")
        if image.size == (192, 192):
            return
        if image.size != (128, 192):
            raise AssertionError(f"Unexpected mimi_broom.png size: {image.size}")

        output = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
        for row in range(4):
            for col in range(4):
                frame = image.crop((col * 32, row * 48, (col + 1) * 32, (row + 1) * 48))
                frame = frame.resize((48, 48), Image.Resampling.NEAREST)
                output.alpha_composite(frame, (col * 48, row * 48))
        output.save(path, optimize=True)


def rebuild_social_and_profile_assets() -> None:
    walk = Image.open(WALK_PATH).convert("RGBA")
    if walk.size != (128, 192):
        raise AssertionError(f"Unexpected mimi_walk.png size: {walk.size}")

    # Frame 0 is reserved for old map-marker compatibility. Frame 1 is the approved front pose.
    front = walk.crop((32, 0, 64, 48))
    mugshot = front.resize((16, 24), Image.Resampling.NEAREST)
    mugshot.save(ROOT / "assets/mimi_social_mugshot.png", optimize=True)

    runtime = Image.new("RGBA", (128, 216), (0, 0, 0, 0))
    runtime.alpha_composite(walk, (0, 0))
    runtime.alpha_composite(mugshot, (0, 192))
    runtime.save(ROOT / "assets/mimi_walk_runtime.png", optimize=True)

    # ProfileMenu always renders NPC sprite frames at x4. Keep a logical 32x48 frame but
    # shrink visible MiMi art to roughly 4/7 so only the gift-profile screen becomes smaller.
    profile = Image.new("RGBA", (128, 192), (0, 0, 0, 0))
    target_w = round(32 * 4 / 7)
    target_h = round(48 * 4 / 7)
    for row in range(4):
        for col in range(4):
            source_col = 1 if row == 0 and col == 0 else col
            frame = walk.crop((source_col * 32, row * 48, (source_col + 1) * 32, (row + 1) * 48))
            frame = frame.resize((target_w, target_h), Image.Resampling.NEAREST)
            x = col * 32 + (32 - target_w) // 2
            y = row * 48 + (48 - target_h)
            profile.alpha_composite(frame, (x, y))
    profile.save(ROOT / "assets/mimi_profile.png", optimize=True)


def write_profile_patch() -> None:
    path = ROOT / "Patches/MimiProfileMenuPatch.cs"
    path.write_text('''using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

internal static class MimiProfileMenuPatch
{
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");

    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );

        if (target is null || AnimatedSpriteField is null)
        {
            ModEntry.StaticMonitor?.Log("Could not install MiMi ProfileMenu sprite-size patch.", StardewModdingAPI.LogLevel.Warn);
            return;
        }

        harmony.Patch(
            target,
            postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(Postfix))
        );
    }

    private static void Postfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        if (entry.Character is not NPC npc
            || !string.Equals(npc.Name, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        try
        {
            AnimatedSprite sprite = new(WorldActorService.MimiProfileCharacterAsset, 0, 32, 48);
            sprite.faceDirection(2);
            AnimatedSpriteField?.SetValue(__instance, sprite);
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log(
                $"MiMi ProfileMenu sprite substitution failed safely: {ex.Message}",
                StardewModdingAPI.LogLevel.Trace
            );
        }
    }
}
''')


def patch_inventory_only_tab() -> None:
    path = ROOT / "UI/CardchaBookTabService.cs"
    text = path.read_text()
    old = '''    private static bool IsSupported(IClickableMenu? menu)\n        => menu is GameMenu or ItemGrabMenu;'''
    new = '''    private static bool IsSupported(IClickableMenu? menu)\n    {\n        if (menu is not GameMenu gameMenu)\n            return false;\n\n        return GetGraphOwner(gameMenu) is InventoryPage;\n    }'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError("Unexpected CardchaBookTabService.IsSupported shape")
    path.write_text(text)


def register_profile_patch() -> None:
    path = ROOT / "ModEntry.cs"
    text = path.read_text()
    if "MimiProfileMenuPatch.Apply(harmony);" not in text:
        text = replace_once(
            text,
            "        BookNavigationPatch.Apply(harmony, this.BookTab);\n",
            "        BookNavigationPatch.Apply(harmony, this.BookTab);\n        MimiProfileMenuPatch.Apply(harmony);\n",
            "MiMi profile Harmony registration",
        )
    path.write_text(text)


def validate_locked_walk(walk_before: str) -> None:
    walk_after = hashlib.sha256(WALK_PATH.read_bytes()).hexdigest()
    if walk_after != walk_before:
        raise AssertionError("mimi_walk.png changed unexpectedly")

    mystery = (ROOT / "Services/MimiMysteryTownService.cs").read_text()
    if 'MugShotSourceRect", 0, 192, 16, 24' not in mystery:
        raise AssertionError("MiMi MugShotSourceRect is not wired to the appended 16x24 strip")
    if 'assets/mimi_walk_runtime.png' not in mystery:
        raise AssertionError("MiMi character texture is not using mimi_walk_runtime.png")


walk_before = hashlib.sha256(WALK_PATH.read_bytes()).hexdigest()
patch_binder()
patch_world_actor()
rebuild_broom()
rebuild_social_and_profile_assets()
write_profile_patch()
patch_inventory_only_tab()
register_profile_patch()
set_version_text(ROOT / "Cardcha.csproj")
set_version_text(ROOT / "Directory.Build.targets")
set_version_text(ROOT / "ModEntry.cs")
manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
manifest["Version"] = TARGET_VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
validate_locked_walk(walk_before)
print("0.7.7.3 candidate applied; mimi_walk SHA256 preserved:", walk_before)
