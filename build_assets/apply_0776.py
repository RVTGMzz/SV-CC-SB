from pathlib import Path
from PIL import Image
import base64
import hashlib
import io
import json
import re

ROOT = Path('src/Cardcha')
TARGET_VERSION = '0.3.0-alpha.27.0.7.7.6'
TARGET_DECOR = 'alpha.27.0.7.7.6'
LOCKED_WALK_SHA = '04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7'
APPROVED_BROOM_SHA = '875c305258151512e46a66d42574a271590f4d184269c03be7b1c1f4f6a161e8'
MUGSHOT_SHA = '7db5cd2f6c8815148d68e534bda26036c55f200402f09713d742d1ab1bfebd11'

# User-approved MiMi friend-list mugshot, normalized to Stardew's 16x24 social slot.
MUGSHOT_B64 = '''iVBORw0KGgoAAAANSUhEUgAAABAAAAAYCAYAAADzoH0MAAADpUlEQVR42u2T20+bdRjHv7/3fUvfFgKF8qbl0LIVi4MNGbKxMGCZCOg8RCXRABoynYteeLEtajQeotHFLGpCPOxuu9DMmSUeMFnCllCW6GAOWQEJYCm00AMtbemR9m1Lfz8vDDpd/AeM36vnufh8kiffPMD/+Q+Ev30RIbScEE1XH8jXv+TOZgo2WDrSIGheOKY2fj5QZHglmkzpVpAe+VdbOyn6inX2Mbm2i30EM3u9sJoNopqxhkcYO9THekn5yj8ZYXsoV2kfrU2LHTesrq3Zui4SbnsCOwopLwe9uSXXTyzt9JM15PEAagDYtjkCAFAqd75MJNuDJY2C/8W3WVP7PhILAIIKrMIEMmexYuSNV+lTYoL7MOF3fZl0GLcFHAAgnc44i6vjJe8Nsp7n90GgWdTuzUCnz5FEIIvqpkZ0nL2IsHEP43Kp8O0ncACwV9d86sjR8xqp3kRXxsJEMTMK3xJFZGoeiRWCjG8W992zQKfbTpLvM9mhOwQChLL4eoKkAmDfXRzEj/OfgvPegiI1hi/OHcXC+A9YunyJ0+QIdusPP35Hjd5N1zdyNPSsmjtYLEkeVrCRIff2SdiMJMG8LlS2HkMsJkHJ5Yh1OaC0B8fO/E1QCEV/14HjPdpSs0g3PaT/pInwJA/FZglmXSnc3kLMhDREX7WLikohb2JyWJSRGgEAfrfU8M7xnrOfDDwzIGq1PAnKhJx+9xz0YgTOCRtOnbGi+aFeOG0xVFQVkK6HG0ilurN9K5F8Ori+4BDyFcXNzQdaKKWUTUx6+LoWA45cAEquzSIbJ3jS1AxvIIbLV76FnOyDyawlTQfrMxzeNHu8M72cWiUindzC1KSHzE9dwdDXFpDCMly1/IaAzY6NdRkzI6Ooq+DhmD0Py5ADPKcgc4vToFRe5FXgKiBL3cFIjhnEEZIKzmFd4Uf9Y4cwH5jGsDuOu/U57DGG4PaHkeUaKU0IwqXh16xTocl+PiiHrjtWR9M04uk0lO5i47ZfiUrgoOEUcIeyaNU7MW4PYjlaBpXCxJY8NlgmBm/c9I/2A9jgAEAHmvfZ+20w1aRpXDYiq+7GtdUaTLP7EaPl6DakIEYX8MFbVbnDtTe5n32WjwHY/6xRK4j7TVJRt98Rgpi/g7RWUyRZJcxaJZajgIbYkdlcZK4Q5ZfXfPFb/uggpdm1v57pj5wYqOs4vb9Kp9p5l4as+gBRsQWVcgu2GTubXkviF697cRX+5wBc34Z+B+0Al9woA8YpAAAAAElFTkSuQmCC'''


def replace_optional(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        if text.count(old) != 1:
            raise AssertionError(f'{label}: expected one old match, got {text.count(old)}')
        return text.replace(old, new, 1)
    if new not in text:
        raise AssertionError(f'{label}: neither old nor new form found')
    return text


def set_versions() -> None:
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.7(?:\.\d+)?(?!\.\d)'
    for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'ModEntry.cs']:
        path = ROOT / rel
        text = path.read_text()
        text, count = re.subn(pattern, TARGET_VERSION, text)
        if count == 0 and TARGET_VERSION not in text:
            raise AssertionError(f'Could not update version in {rel}')
        path.write_text(text)

    manifest_path = ROOT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['Version'] = TARGET_VERSION
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


def install_user_mugshot() -> None:
    raw = base64.b64decode(MUGSHOT_B64)
    if hashlib.sha256(raw).hexdigest() != MUGSHOT_SHA:
        raise AssertionError('Embedded MiMi mugshot hash mismatch')
    mug = Image.open(io.BytesIO(raw)).convert('RGBA')
    if mug.size != (16, 24):
        raise AssertionError(f'Unexpected mugshot size {mug.size}')

    mug_path = ROOT / 'assets/mimi_social_mugshot.png'
    mug_path.write_bytes(raw)

    walk_path = ROOT / 'assets/mimi_walk.png'
    if hashlib.sha256(walk_path.read_bytes()).hexdigest() != LOCKED_WALK_SHA:
        raise AssertionError('Locked mimi_walk.png changed')
    walk = Image.open(walk_path).convert('RGBA')
    if walk.size != (128, 192):
        raise AssertionError(f'Unexpected mimi_walk size {walk.size}')

    runtime = Image.new('RGBA', (128, 216), (0, 0, 0, 0))
    runtime.alpha_composite(walk, (0, 0))
    runtime.alpha_composite(mug, (0, 192))
    runtime.save(ROOT / 'assets/mimi_walk_runtime.png', optimize=True)


def patch_attic_layout() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()

    text = replace_optional(
        text,
        'private const string DecorVersion = "alpha.27.0.7.7.5";',
        'private const string DecorVersion = "alpha.27.0.7.7.6";',
        'decor version'
    )

    # Move the research rug to the lower prototype table.
    text = replace_optional(
        text,
        'TryAddFurniture(attic, "(F)1456", 3, 5);   // Patchwork Rug — research zone.',
        'TryAddFurniture(attic, "(F)1456", 15, 9);  // Patchwork Rug — moved beneath the lower prototype table.',
        'research rug'
    )

    # Push the upper table to the wall; replace its crystal with the plant.
    text = replace_optional(
        text,
        'TryAddFurniture(attic, "(F)1120", 4, 5, heldId: "(F)1368"); // Oak Table + Small Crystal.',
        'TryAddFurniture(attic, "(F)1120", 4, 4, heldId: "(F)1362"); // Oak Table against the wall + Small Plant.',
        'upper table'
    )
    text = replace_optional(
        text,
        'TryAddFurniture(attic, "(F)1443", 8, 5);                 // Country Lamp.',
        'TryAddFurniture(attic, "(F)1443", 9, 4);                 // Country Lamp tucked beside the raised window.',
        'lamp'
    )
    old_plant = '        TryAddFurniture(attic, "(F)1362", 9, 5);                 // Small Plant.\n'
    if old_plant in text:
        text = text.replace(old_plant, '', 1)
    elif 'TryAddFurniture(attic, "(F)1362", 9, 5)' in text:
        raise AssertionError('Unexpected standalone plant line')

    # Keep TV in its current nook, but shift the couch right one tile so their visual centers align.
    text = replace_optional(
        text,
        'TryAddFurniture(attic, "(F)432", 2, 11, rotation: 2);    // Couch tight to the bottom wall, centered beneath the TV.',
        'TryAddFurniture(attic, "(F)432", 3, 11, rotation: 2);    // Couch shifted right to visually center beneath the TV.',
        'tv couch'
    )

    # Raise the wall window one tile.
    text = replace_optional(
        text,
        'TryAddFurniture(attic, "(F)1614", 10, 2);                // Basic Window.',
        'TryAddFurniture(attic, "(F)1614", 10, 1);                // Basic Window raised to mid-wall height.',
        'window'
    )

    # Keep inspect targets synchronized with the moved furniture.
    text = replace_optional(text, 'DeskLeft: P(4, 5),', 'DeskLeft: P(4, 4),', 'desk inspect left')
    text = replace_optional(text, 'DeskRight: P(6, 5),', 'DeskRight: P(6, 4),', 'desk inspect right')
    text = replace_optional(text, 'Television: P(3, 7),', 'Television: P(4, 7),', 'tv inspect')
    text = replace_optional(text, 'TvChair: P(2, 10),', 'TvChair: P(3, 10),', 'couch inspect')

    path.write_text(text)


def patch_wizard_ladder_position() -> None:
    path = ROOT / 'Services/MimiHomeService.cs'
    text = path.read_text()
    old = '''        Point preferred = new(\n            Math.Clamp(width - 3, 2, Math.Max(2, width - 2)),\n            Math.Clamp((int)Math.Round(height * 0.28f), 2, Math.Max(2, height - 3))\n        );'''
    new = '''        Point preferred = new(\n            Math.Clamp(width - 2, 2, Math.Max(2, width - 2)),\n            Math.Clamp((int)Math.Round(height * 0.20f), 2, Math.Max(2, height - 3))\n        );'''
    text = replace_optional(text, old, new, 'wizard ladder position')

    old_comment = '''        // Keep the entrance visually fixed. 0.7.7.4 re-ran collision search every render,\n        // so clearing the stair area could change the "nearest clear" result and make the ladder\n        // appear to move when the player approached it. The landing below is still resolved safely.'''
    new_comment = '''        // Keep the entrance visually fixed and one tile farther right / higher than 0.7.7.5,\n        // separating the ladder from the fireplace while preserving the safe landing resolver.\n        // Never re-run a nearest-clear search here, or the ladder can visually move as tiles change.'''
    text = replace_optional(text, old_comment, new_comment, 'wizard ladder comment')
    path.write_text(text)


def patch_tmx_metadata() -> None:
    path = ROOT / 'assets/mimi_attic.tmx'
    text = path.read_text()
    text = text.replace('CardchaAtticVersion" value="alpha.27.0.7.7.5"', 'CardchaAtticVersion" value="alpha.27.0.7.7.6"')
    text = text.replace(
        'true-stardew-map|framed-room-shell|bed-rug|centered-tv-sofa|fixed-wizard-ladder|strict-csv',
        'true-stardew-map|framed-room-shell|raised-window|wall-desk|centered-tv-sofa|right-high-fixed-wizard-ladder|strict-csv'
    )
    path.write_text(text)


def validate() -> None:
    assert hashlib.sha256((ROOT / 'assets/mimi_walk.png').read_bytes()).hexdigest() == LOCKED_WALK_SHA
    assert hashlib.sha256((ROOT / 'assets/mimi_broom.png').read_bytes()).hexdigest() == APPROVED_BROOM_SHA
    assert hashlib.sha256((ROOT / 'assets/mimi_social_mugshot.png').read_bytes()).hexdigest() == MUGSHOT_SHA
    assert Image.open(ROOT / 'assets/mimi_social_mugshot.png').size == (16, 24)
    assert Image.open(ROOT / 'assets/mimi_walk_runtime.png').size == (128, 216)

    walk = Image.open(ROOT / 'assets/mimi_walk.png').convert('RGBA')
    runtime = Image.open(ROOT / 'assets/mimi_walk_runtime.png').convert('RGBA')
    mug = Image.open(ROOT / 'assets/mimi_social_mugshot.png').convert('RGBA')
    assert runtime.crop((0, 0, 128, 192)).tobytes() == walk.tobytes()
    assert runtime.crop((0, 192, 16, 216)).tobytes() == mug.tobytes()

    attic = (ROOT / 'Services/MimiAtticVisualService.cs').read_text()
    for needle in [
        '"(F)1456", 15, 9',
        '"(F)1120", 4, 4, heldId: "(F)1362"',
        '"(F)1443", 9, 4',
        '"(F)432", 3, 11',
        '"(F)1614", 10, 1',
        'alpha.27.0.7.7.6',
    ]:
        assert needle in attic, needle
    assert '"(F)1362", 9, 5' not in attic

    home = (ROOT / 'Services/MimiHomeService.cs').read_text()
    assert 'Math.Clamp(width - 2, 2, Math.Max(2, width - 2))' in home
    assert 'Math.Round(height * 0.20f)' in home

    manifest = json.loads((ROOT / 'manifest.json').read_text())
    assert manifest['Version'] == TARGET_VERSION
    assert TARGET_VERSION in (ROOT / 'Cardcha.csproj').read_text()
    assert TARGET_VERSION in (ROOT / 'Directory.Build.targets').read_text()
    assert TARGET_VERSION in (ROOT / 'ModEntry.cs').read_text()


def main() -> None:
    install_user_mugshot()
    patch_attic_layout()
    patch_wizard_ladder_position()
    patch_tmx_metadata()
    set_versions()
    validate()
    print('Cardcha alpha27 0.7.7.6 candidate applied and validated.')


if __name__ == '__main__':
    main()
