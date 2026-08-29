from pathlib import Path
import re
import apply_0784 as base

ROOT = Path('src/Cardcha')


def patch_attic_exact() -> None:
    path = ROOT / 'Services/MimiAtticVisualService.cs'
    text = path.read_text()
    text = re.sub(
        r'private const string DecorVersion = "alpha\.27\.0\.7\.8(?:\.\d+)?";',
        'private const string DecorVersion = "alpha.27.0.7.8.4";',
        text,
        count=1,
    )
    text, count = re.subn(
        r'TryAddFurniture\(attic, "\(F\)1456", 16, 9, pixelOffsetX: -24\);[^\n]*',
        'TryAddFurniture(attic, "(F)1456", 16, 9, pixelOffsetX: -32);  // Final left nudge: rug visual center under the prototype table.',
        text,
        count=1,
    )
    if count != 1 and '"(F)1456", 16, 9, pixelOffsetX: -32' not in text:
        raise AssertionError('Could not update prototype rug from -24 to -32')
    if '"(F)1466", 4, 7, pixelOffsetX: -32' not in text:
        raise AssertionError('Accepted TV offset was unexpectedly changed')
    path.write_text(text)


def main() -> None:
    base.patch_binder()
    patch_attic_exact()
    base.set_versions()
    base.validate()
    print('0.7.8.4 corrected runner PASS')


if __name__ == '__main__':
    main()
