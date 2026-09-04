from pathlib import Path
import re

ROOT = Path("src/Cardcha")
ASSETS = ROOT / "assets"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.8"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.9"
ATTIC_DECOR_VERSION = "alpha.28.0.4.14.4.5.9"
WIDTH = 22
HEIGHT = 14


def replace_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if NEW_VERSION in text:
        return
    if OLD_VERSION not in text:
        raise RuntimeError(f"Expected {OLD_VERSION} in {path}")
    path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")


def grid():
    return [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]


def csv(layer):
    return ",\n".join(",".join(str(v) for v in row) for row in layer)


def build_attic_map() -> None:
    back = grid()
    buildings = grid()
    front = grid()

    # Real townInterior shell. No room-sized custom backdrop is used in .5.9.
    # Wall cap + warm wall body.
    for x in range(1, 21):
        back[1][x] = 171
        back[2][x] = 171
        back[3][x] = 113
        back[4][x] = 200

    # Warm vanilla wood floor. Furniture/rugs provide zone identity without fake painted scenery.
    for y in range(5, 13):
        pair = (232, 233) if (y - 5) % 2 == 0 else (264, 265)
        for x in range(1, 21):
            back[y][x] = pair[(x - 1) % 2]

    # Two-tile stair landing extending into the black void.
    back[13][10] = 264
    back[13][11] = 265

    # Vanilla room outline.
    buildings[1][1] = 155
    buildings[1][20] = 156
    buildings[2][1] = 187
    for x in range(2, 20):
        buildings[2][x] = 81
    buildings[2][20] = 188
    for x in range(1, 21):
        buildings[3][x] = 113
    for y in range(4, 12):
        buildings[y][1] = 68
        buildings[y][20] = 69

    # Bottom edge leaves only the central stair/door opening.
    for x in range(1, 21):
        if x not in (10, 11):
            buildings[12][x] = 1

    for x in range(1, 21):
        if x not in (10, 11):
            front[12][x] = 166 if x < 20 else 167

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{WIDTH}" height="{HEIGHT}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
 <properties>
  <property name="CardchaAtticVersion" value="{ATTIC_DECOR_VERSION}"/>
  <property name="CardchaZoneLayout" value="landing|research|personal|tv-secret|chacha"/>
  <property name="CardchaVisualDirection" value="true-stardew-map|vanilla-townInterior|vanilla-furniture-runtime|five-zone-home|no-room-overlay|strict-csv"/>
 </properties>
 <tileset firstgid="1" name="townInterior" tilewidth="16" tileheight="16" tilecount="2176" columns="32">
  <image source=".townInterior.png" width="512" height="1088"/>
 </tileset>
 <layer id="1" name="Back" width="{WIDTH}" height="{HEIGHT}">
  <data encoding="csv">
{csv(back)}
  </data>
 </layer>
 <layer id="2" name="Buildings" width="{WIDTH}" height="{HEIGHT}">
  <data encoding="csv">
{csv(buildings)}
  </data>
 </layer>
 <layer id="3" name="Front" width="{WIDTH}" height="{HEIGHT}">
  <data encoding="csv">
{csv(front)}
  </data>
 </layer>
</map>
'''
    (ASSETS / "mimi_attic.tmx").write_text(xml, encoding="utf-8")


def patch_attic_service() -> None:
    path = ROOT / "Services" / "MimiAtticVisualService.cs"
    text = path.read_text(encoding="utf-8")

    # Remove the last room-sized concept-art style overlay. The TMX + vanilla furniture now own
    # the visual presentation so farmer draw order and Stardew pixel language stay native.
    text = re.sub(r'^\s*private const string RoomFrameSpritePath = "assets/mimi_attic_room_frame\.png";\s*\n', '', text, flags=re.M)
    text = re.sub(
        r'private const string DecorVersion = "[^"]+";',
        f'private const string DecorVersion = "{ATTIC_DECOR_VERSION}";',
        text,
        count=1,
    )
    text = text.replace("            this.DrawRoomFrame(e.SpriteBatch);\n", "")

    method_pattern = re.compile(
        r'\n    private void DrawRoomFrame\(SpriteBatch batch\)\n    \{.*?\n    \}\n\n(?=    private static AtticLayout GetLayout)',
        re.S,
    )
    text, removed = method_pattern.subn("\n", text, count=1)
    if removed == 0 and "DrawRoomFrame" in text:
        raise RuntimeError("Could not safely remove DrawRoomFrame method")

    text = text.replace(
        "/// Alpha.27.0.7.1 true-Stardew visual layer with test access for MiMi's attic.",
        "/// Alpha28 .5.9 true-Stardew MiMi Attic rebuild with test access.",
    )
    text = text.replace(
        "/// The TMX now provides a tile-based vanilla townInterior shell; this service adds real vanilla",
        "/// The TMX provides the vanilla townInterior shell; this service adds real vanilla",
    )
    text = text.replace(
        "/// Furniture instances for the five locked room zones, keeps inspect points, and preserves the",
        "/// Furniture instances for the five locked zones with no room-sized visual overlay, keeps inspect points, and preserves the",
    )

    if "mimi_attic_room_frame.png" in text or "DrawRoomFrame" in text or "RoomFrameSpritePath" in text:
        raise RuntimeError("Room-frame overlay references remain after patch")
    if f'DecorVersion = "{ATTIC_DECOR_VERSION}"' not in text:
        raise RuntimeError("Decor version patch failed")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    for p in [ROOT / "manifest.json", ROOT / "Cardcha.csproj", ROOT / "Directory.Build.targets"]:
        replace_version(p)

    build_attic_map()
    patch_attic_service()

    # Remove the obsolete room-sized concept frame from source/package entirely.
    old_frame = ASSETS / "mimi_attic_room_frame.png"
    if old_frame.exists():
        old_frame.unlink()

    print(f"alpha28 .5.9 MiMi Attic Stardew rebuild prepared: {NEW_VERSION}")


if __name__ == "__main__":
    main()
