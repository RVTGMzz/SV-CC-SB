from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import hashlib
import json
import re
import subprocess

ROOT = Path('src/Cardcha')
TARGET_VERSION = '0.3.0-alpha.27.0.7.7.5'
TARGET_DECOR = 'alpha.27.0.7.7.5'
LOCKED_WALK_SHA = '04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7'
APPROVED_BROOM_COMMIT = 'a1241688bf509ef1abcf6609135b72576738116a'
APPROVED_BROOM_SHA = '875c305258151512e46a66d42574a271590f4d184269c03be7b1c1f4f6a161e8'
WALK_PATH = ROOT / 'assets/mimi_walk.png'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f'{label}: expected exactly one match, got {count}')
    return text.replace(old, new, 1)


def set_version_text(path: Path) -> None:
    text = path.read_text()
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.7(?:\.\d+)?(?!\.\d)'
    text, count = re.subn(pattern, TARGET_VERSION, text)
    if count == 0 and TARGET_VERSION not in text:
        raise AssertionError(f'Could not update version in {path}')
    path.write_text(text)


def patch_reveal_rarity() -> None:
    path = ROOT / 'UI/CardchaRevealMenu.cs'
    text = path.read_text()
    old = 'CardchaUi.DrawScaledText(b, Game1.smallFont, result.Card.Rarity.ToString(), rarity, CardchaUi.RarityColor(result.Card.Rarity), false, true, 2, 1.05f);'
    new = 'CardchaUi.DrawScaledText(b, Game1.smallFont, RarityLabel(result.Card.Rarity), rarity, CardchaUi.RarityColor(result.Card.Rarity), false, true, 2, 1.05f);'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError('Unexpected reveal rarity draw line')

    helper = '''\n    private static string RarityLabel(CardRarity rarity)\n        => rarity switch\n        {\n            CardRarity.Common => ModEntry.T("rarity.common"),\n            CardRarity.Rare => ModEntry.T("rarity.rare"),\n            CardRarity.Epic => ModEntry.T("rarity.epic"),\n            CardRarity.Legendary => ModEntry.T("rarity.legendary"),\n            CardRarity.Mythic => ModEntry.T("rarity.mythic"),\n            _ => ModEntry.T("rarity.common")\n        };\n'''
    if 'private static string RarityLabel(CardRarity rarity)' not in text:
        marker = '\n    private void RevealEverything()\n'
        if marker not in text:
            raise AssertionError('Could not locate reveal helper insertion point')
        text = text.replace(marker, helper + marker, 1)

    if 'result.Card.Rarity.ToString()' in text:
        raise AssertionError('Reveal overlay still prints raw rarity enum')
    path.write_text(text)


def rebuild_social_mugshot() -> None:
    walk = Image.open(WALK_PATH).convert('RGBA')
    if walk.size != (128, 192):
        raise AssertionError(f'Unexpected mimi_walk size {walk.size}')

    front = walk.crop((32, 0, 64, 48))
    bust = front.crop((4, 0, 28, 34))
    scale = min(14 / bust.width, 20 / bust.height)
    target = (max(1, round(bust.width * scale)), max(1, round(bust.height * scale)))
    bust = bust.resize(target, Image.Resampling.NEAREST)

    sprite = Image.new('RGBA', (16, 24), (0, 0, 0, 0))
    x = (16 - bust.width) // 2
    y = 2 + max(0, (20 - bust.height) // 2)
    sprite.alpha_composite(bust, (x, y))

    alpha = sprite.getchannel('A')
    dilated = alpha.filter(ImageFilter.MaxFilter(3))
    outline_mask = Image.new('L', alpha.size, 0)
    a = alpha.load()
    d = dilated.load()
    o = outline_mask.load()
    for yy in range(alpha.height):
        for xx in range(alpha.width):
            if d[xx, yy] > 0 and a[xx, yy] == 0:
                o[xx, yy] = 255

    outlined = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
    black = Image.new('RGBA', sprite.size, (8, 8, 12, 255))
    outlined.alpha_composite(Image.composite(black, Image.new('RGBA', sprite.size, (0, 0, 0, 0)), outline_mask))
    outlined.alpha_composite(sprite)
    outlined.save(ROOT / 'assets/mimi_social_mugshot.png', optimize=True)

    runtime = Image.new('RGBA', (128, 216), (0, 0, 0, 0))
    runtime.alpha_composite(walk, (0, 0))
    runtime.alpha_composite(outlined, (0, 192))
    runtime.save(ROOT / 'assets/mimi_walk_runtime.png', optimize=True)


def restore_approved_broom() -> None:
    result = subprocess.run(
        ['git', 'show', f'{APPROVED_BROOM_COMMIT}:src/Cardcha/assets/mimi_broom.png'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    path = ROOT / 'assets/mimi_broom.png'
    path.write_bytes(result.stdout)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != APPROVED_BROOM_SHA:
        raise AssertionError(f'Approved broom hash mismatch: {actual}')
    if Image.open(path).size != (192, 192):
        raise AssertionError('Approved broom is not 192x192')


def patch_broom_scale() -> None:
    path = ROOT / 'Services/WorldActorService.cs'
    text = path.read_text()
    current = '''    // 0.7.7.4 broom art is already widened horizontally by ~30% inside native 48x48 frames.\n    // Keep runtime scale equal to normal MiMi so only width changes; do not inflate her height too.\n    private const float MimiBroomNativeScale = MimiNativeScale;'''
    approved = '''    // Restored approved pre-0.7.7.4 broom animation. The older sheet renders MiMi slightly\n    // smaller inside its native 48x48 frames, so keep the accepted 10% runtime compensation.\n    private const float MimiBroomNativeScale = MimiNativeScale * 1.10f;'''
    if current in text:
        text = text.replace(current, approved, 1)
    elif approved not in text:
        raise AssertionError('Unexpected MiMi broom scale block')
    path.write_text(text)


def patch_machine_nonplaceable() -> None:
    item_path = ROOT / 'Services/ItemAssetService.cs'
    text = item_path.read_text()
    block_old = '''                    Fragility = 0,\n                    CanBePlacedIndoors = true,\n                    CanBePlacedOutdoors = false,\n                    IsLamp = false,'''
    block_new = '''                    Fragility = 0,\n                    CanBePlacedIndoors = false,\n                    CanBePlacedOutdoors = false,\n                    IsLamp = false,'''
    if block_old in text:
        text = text.replace(block_old, block_new, 1)
    elif block_new not in text:
        raise AssertionError('Unexpected Cardcha machine placement flags')
    item_path.write_text(text)

    patch_path = ROOT / 'Patches/MachineInteractionPatch.cs'
    text = patch_path.read_text()
    marker = '        harmony.Patch(target, prefix: prefix);\n'
    add = '''        harmony.Patch(target, prefix: prefix);\n\n        // The story Machine is a menu key / home appliance entitlement, not a placeable\n        // big-craftable. Returning false here also prevents Stardew from drawing the green\n        // placement ghost while the player is holding it.\n        MethodInfo? placeable = AccessTools.Method(typeof(SObject), nameof(SObject.isPlaceable), System.Type.EmptyTypes);\n        if (placeable is not null)\n        {\n            harmony.Patch(\n                placeable,\n                postfix: new HarmonyMethod(typeof(MachineInteractionPatch), nameof(IsPlaceablePostfix))\n            );\n        }\n'''
    if 'nameof(IsPlaceablePostfix)' not in text:
        if marker not in text:
            raise AssertionError('Could not locate MachineInteractionPatch patch point')
        text = text.replace(marker, add, 1)

    method = '''\n    private static void IsPlaceablePostfix(SObject __instance, ref bool __result)\n    {\n        if (__result && IsCardchaMachine(__instance))\n            __result = false;\n    }\n'''
    if 'private static void IsPlaceablePostfix' not in text:
        insert = '\n    public static bool IsCardchaMachine(SObject? obj)\n'
        if insert not in text:
            raise AssertionError('Could not locate MachineInteractionPatch helper insertion point')
        text = text.replace(insert, method + insert, 1)
    patch_path.write_text(text)


def generate_ladder() -> None:
    out = Image.new('RGBA', (16, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    dark = (45, 25, 23, 255)
    shadow = (76, 39, 27, 255)
    wood = (153, 90, 42, 255)
    light = (205, 143, 65, 255)

    # Dark silhouette first, then rails/rungs. The narrow 1-tile shape intentionally resembles
    # the fixed mine/cave ladders instead of a freestanding furniture staircase.
    d.rectangle((2, 1, 5, 62), fill=dark)
    d.rectangle((10, 1, 13, 62), fill=dark)
    d.rectangle((3, 2, 4, 61), fill=wood)
    d.rectangle((11, 2, 12, 61), fill=wood)
    d.line((4, 2, 4, 61), fill=light)
    d.line((12, 2, 12, 61), fill=shadow)

    for yy in range(7, 59, 7):
        d.rectangle((3, yy - 1, 12, yy + 2), fill=dark)
        d.rectangle((4, yy, 11, yy + 1), fill=wood)
        d.line((4, yy, 11, yy), fill=light)

    # Small cap/feet pixels keep the silhouette readable against dark WizardHouse walls.
    d.rectangle((1, 1, 6, 3), fill=dark)
    d.rectangle((9, 1, 14, 3), fill=dark)
    d.rectangle((2, 60, 5, 63), fill=dark)
    d.rectangle((10, 60, 13, 63), fill=dark)
    out.save(ROOT / 'assets/mimi_attic_stairs.png', optimize=True)


def generate_room_frame() -> None:
    # Native map-pixel overlay: 22x14 tiles at 16px each. Only the perimeter is painted, so the
    # frame can't cover furniture or actors. Rendered at x4 it adds the dark/wood casing visible
    # around vanilla interior rooms while preserving the actual townInterior shell below it.
    w, h = 22 * 16, 14 * 16
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    left, top, right, bottom = 16, 16, 20 * 16 + 15, 12 * 16 + 15
    dark = (38, 18, 25, 255)
    mid = (91, 46, 35, 255)
    warm = (151, 80, 46, 255)

    # Slightly rounded outer casing.
    for i, color in enumerate((dark, mid, warm)):
        l, t, r, b = left + i, top + i, right - i, bottom - i
        d.line((l + 4, t, r - 4, t), fill=color)
        d.line((l, t + 4, l, b - 4), fill=color)
        d.line((r, t + 4, r, b - 4), fill=color)
        # Bottom has a two-tile doorway gap at map columns 10-11.
        gap_l, gap_r = 10 * 16, 12 * 16 - 1
        d.line((l + 4, b, gap_l - 1, b), fill=color)
        d.line((gap_r + 1, b, r - 4, b), fill=color)
        d.line((l + 1, t + 2, l + 4, t), fill=color)
        d.line((r - 4, t, r - 1, t + 2), fill=color)
        d.line((l, b - 4, l + 3, b - 1), fill=color)
        d.line((r - 3, b - 1, r, b - 4), fill=color)

    img.save(ROOT / 'assets/mimi_attic_room_frame.png', optimize=True)


def patch_attic_visuals() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()

    text = text.replace('private const string StairSpritePath = "assets/mimi_attic_stairs.png";\n    private const string DecorVersion = "alpha.27.0.7.7.4";',
                        'private const string StairSpritePath = "assets/mimi_attic_stairs.png";\n    private const string RoomFrameSpritePath = "assets/mimi_attic_room_frame.png";\n    private const string DecorVersion = "alpha.27.0.7.7.5";')

    attic_old = '''        if (location.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            if (this.Save.Data.MimiMeetupCompleted || this.TestAccessActive)\n                EnsureVanillaFurniture(location);\n            return;\n        }'''
    attic_new = '''        if (location.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            if (this.Save.Data.MimiMeetupCompleted || this.TestAccessActive)\n                EnsureVanillaFurniture(location);\n            this.DrawRoomFrame(e.SpriteBatch);\n            return;\n        }'''
    if attic_old in text:
        text = text.replace(attic_old, attic_new, 1)
    elif attic_new not in text:
        raise AssertionError('Unexpected attic render block')

    text = text.replace('TryAddFurniture(attic, "(F)1466", 3, 7);                 // TV pushed toward the wall.',
                        'TryAddFurniture(attic, "(F)1466", 4, 7);                 // TV shifted right to center with the sofa/rug.')
    text = text.replace('        TryAddFurniture(attic, "(F)724", 6, 9, heldId: "(F)1364");  // Coffee Table + bowl/snacks stand-in.\n', '')
    text = text.replace('TryAddFurniture(attic, "(F)1541", 6, 2);                 // A Night On Eco-Hill.',
                        'TryAddFurniture(attic, "(F)1541", 6, 1);                 // A Night On Eco-Hill, hung higher on the wall.')

    text = text.replace('else if (Touches(actionTile, layout.Television) || Touches(actionTile, layout.TvChair) || Touches(actionTile, layout.TvTable))',
                        'else if (Touches(actionTile, layout.Television) || Touches(actionTile, layout.TvChair))')
    text = text.replace('            TvChair: P(2, 10),\n            TvTable: P(6, 9),',
                        '            TvChair: P(2, 10),')
    text = text.replace('        Point TvChair,\n        Point TvTable,',
                        '        Point TvChair,')

    old_prepare = '''            for (int x = tile.X - 1; x <= tile.X; x++)\n            {\n                for (int y = tile.Y - 2; y <= tile.Y; y++)'''
    new_prepare = '''            for (int x = tile.X - 1; x <= tile.X; x++)\n            {\n                for (int y = tile.Y - 3; y <= tile.Y; y++)'''
    if old_prepare in text:
        text = text.replace(old_prepare, new_prepare, 1)

    old_draw = '''            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n            Vector2 world = new(tile.X * 64f - 32f, (tile.Y - 2) * 64f);\n            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);\n            batch.Draw(staircase, screen, null, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.995f);'''
    new_draw = '''            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n            Vector2 world = new(tile.X * 64f, (tile.Y - 3) * 64f);\n            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);\n            batch.Draw(staircase, screen, null, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.995f);'''
    if old_draw in text:
        text = text.replace(old_draw, new_draw, 1)
    elif new_draw not in text:
        raise AssertionError('Unexpected stair draw block')

    frame_method = '''\n    private void DrawRoomFrame(SpriteBatch batch)\n    {\n        try\n        {\n            Texture2D frame = this.Helper.ModContent.Load<Texture2D>(RoomFrameSpritePath);\n            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, Vector2.Zero);\n            batch.Draw(frame, screen, null, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.999f);\n        }\n        catch\n        {\n            // The room itself remains fully usable if the cosmetic frame can't be loaded.\n        }\n    }\n'''
    if 'private void DrawRoomFrame(SpriteBatch batch)' not in text:
        marker = '\n    private static AtticLayout GetLayout(GameLocation location)\n'
        if marker not in text:
            raise AssertionError('Could not locate room frame insertion point')
        text = text.replace(marker, frame_method + marker, 1)

    if '"(F)724"' in text:
        raise AssertionError('TV coffee table still present')
    path.write_text(text)


def patch_stair_stability() -> None:
    path = ROOT / 'Services/MimiHomeService.cs'
    text = path.read_text()
    old = '        return FindClearTileNear(wizard, preferred);'
    new = '''        // Keep the entrance visually fixed. 0.7.7.4 re-ran collision search every render,\n        // so clearing the stair area could change the "nearest clear" result and make the ladder\n        // appear to move when the player approached it. The landing below is still resolved safely.\n        return preferred;'''
    if old in text:
        text = text.replace(old, new, 1)
    elif 'return preferred;' not in text:
        raise AssertionError('Unexpected Wizard stair resolver')
    text = text.replace('alpha.27.0.7.7.4 stair-safe attic build', 'alpha.27.0.7.7.5 fixed-ladder framed attic build')
    path.write_text(text)


def patch_attic_map_metadata() -> None:
    path = ROOT / 'assets/mimi_attic.tmx'
    text = path.read_text()
    text = text.replace('CardchaAtticVersion" value="alpha.27.0.7.7.4"', 'CardchaAtticVersion" value="alpha.27.0.7.7.5"')
    text = text.replace('true-stardew-map|clean-closed-shell|bed-rug|spaced-tv-sofa|wizard-upper-right-stair|strict-csv',
                        'true-stardew-map|framed-room-shell|bed-rug|centered-tv-sofa|fixed-wizard-ladder|strict-csv')
    path.write_text(text)


def validate() -> None:
    if hashlib.sha256(WALK_PATH.read_bytes()).hexdigest() != LOCKED_WALK_SHA:
        raise AssertionError('mimi_walk.png changed unexpectedly')
    if hashlib.sha256((ROOT / 'assets/mimi_broom.png').read_bytes()).hexdigest() != APPROVED_BROOM_SHA:
        raise AssertionError('Broom did not restore to the approved old animation')


walk_before = hashlib.sha256(WALK_PATH.read_bytes()).hexdigest()
if walk_before != LOCKED_WALK_SHA:
    raise AssertionError(f'Locked mimi_walk source hash changed before patch: {walk_before}')

patch_reveal_rarity()
rebuild_social_mugshot()
restore_approved_broom()
patch_broom_scale()
patch_machine_nonplaceable()
generate_ladder()
generate_room_frame()
patch_attic_visuals()
patch_stair_stability()
patch_attic_map_metadata()

set_version_text(ROOT / 'Cardcha.csproj')
set_version_text(ROOT / 'Directory.Build.targets')
set_version_text(ROOT / 'ModEntry.cs')
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
manifest['Version'] = TARGET_VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

validate()
print('0.7.7.5 candidate applied; locked walk preserved and approved broom restored.')
