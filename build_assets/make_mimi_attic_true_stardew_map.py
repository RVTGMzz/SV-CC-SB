from pathlib import Path

WIDTH = 22
HEIGHT = 14
OUT = Path('src/Cardcha/assets/mimi_attic.tmx')


def grid():
    return [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]


def csv(layer):
    """Emit strict TMX CSV: commas separate values, never leave an empty trailing token."""
    return ',\n'.join(','.join(str(v) for v in row) for row in layer)


back = grid()
buildings = grid()
front = grid()

# Standalone room shell: one tile of black void around a 20-tile-wide interior.
# These are vanilla townInterior GIDs, adapted from vanilla-style spouse/interior maps.
for x in range(1, 21):
    back[1][x] = 171
    back[2][x] = 171
    back[3][x] = 113
    back[4][x] = 200

# Warm vanilla wood floor pattern. Keep the lower middle open as an entrance/landing.
floor_rows = (
    (232, 233),
    (264, 265),
    (232, 233),
    (264, 265),
    (232, 233),
    (264, 265),
    (232, 233),
)
for y in range(5, 12):
    pair = floor_rows[(y - 5) % len(floor_rows)]
    for x in range(1, 21):
        back[y][x] = pair[(x - 1) % 2]

# Bottom interior row and a two-tile landing into the black void.
for x in range(1, 21):
    back[12][x] = (264, 265)[(x - 1) % 2]
back[13][10] = 264
back[13][11] = 265

# Vanilla wall/room outline. 68/69 are paired side-edge tiles; 155/156 and 187/188
# are paired upper corners from townInterior. 113 provides the solid wall base.
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

# Closed bottom edge except the central doorway / stair landing.
for x in range(1, 21):
    if x not in (10, 11):
        buildings[12][x] = 1

# Vanilla foreground trim across the bottom edge, broken at the doorway.
for x in range(1, 20):
    if x not in (10, 11):
        front[12][x] = 166
front[12][20] = 167

xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{WIDTH}" height="{HEIGHT}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
 <properties>
  <property name="CardchaAtticVersion" value="alpha.27.0.7.4"/>
  <property name="CardchaZoneLayout" value="landing|research|personal|tv-secret|chacha"/>
  <property name="CardchaVisualDirection" value="true-stardew-map|vanilla-townInterior|vanilla-furniture-runtime|strict-csv"/>
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

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(xml, encoding='utf-8')

# alpha.27.0.6 used one giant room-shaped PNG as a pseudo-tilesheet. 0.7 intentionally removes it.
old = OUT.parent / 'mimi_attic_tiles.png'
if old.exists():
    old.unlink()

print(f'wrote {OUT} ({WIDTH}x{HEIGHT}) with strict TMX CSV and vanilla townInterior fallback')
