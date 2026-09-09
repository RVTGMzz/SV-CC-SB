from pathlib import Path
import json, re, struct, zlib

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.45'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.44'
BRANCH = 'cardcha-alpha28-0676-region3-region4-terrain-depth-pass'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


# ---------- deterministic stdlib PNG writer ----------
def write_png(path: Path, w: int, h: int, pix):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(pix[y][x])

    def chunk(kind: bytes, data: bytes):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

    data = b'\x89PNG\r\n\x1a\n'
    data += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    data += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    data += chunk(b'IEND', b'')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def canvas(w, h):
    return [[(0, 0, 0, 0) for _ in range(w)] for _ in range(h)]


def put(p, x, y, c):
    if 0 <= y < len(p) and 0 <= x < len(p[0]):
        p[y][x] = c


def rect(p, x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(p, xx, yy, c)


def ellipse(p, cx, cy, rx, ry, c):
    if rx <= 0 or ry <= 0:
        return
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) * (x - cx)) / (rx * rx) + ((y - cy) * (y - cy)) / (ry * ry) <= 1.0:
                put(p, x, y, c)


def diamond(p, cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        rem = r - abs(y - cy)
        for x in range(cx - rem, cx + rem + 1):
            put(p, x, y, c)


def line(p, x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put(p, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def ring(p, cx, cy, rx, ry, outer, inner):
    ellipse(p, cx, cy, rx, ry, outer)
    if rx > 2 and ry > 2:
        ellipse(p, cx, cy, rx - 2, ry - 2, inner)


# Terrain cells are 64x64 logical pixels and always drawn at Stardew's fixed 4x pixel scale.
# They are low-profile ground forms, so the player never sees a fake collider or giant foreground prop.
TRANSPARENT = (0, 0, 0, 0)
R3_DARK = (70, 97, 128, 150)
R3_MID = (112, 166, 190, 170)
R3_LIGHT = (179, 219, 226, 190)
R3_LILAC = (181, 164, 210, 170)
R3_GREEN = (118, 158, 133, 155)
R4_IGNIS = (205, 103, 72, 175)
R4_VITA = (102, 169, 109, 175)
R4_AETHER = (91, 143, 205, 175)
R4_RESONANCE = (180, 117, 194, 180)
STONE = (90, 91, 103, 165)
PALE = (226, 237, 231, 185)
GOLD = (224, 190, 102, 190)
SHADOW = (35, 38, 48, 85)


def terrain_cell(p, ox, kind, region):
    cx = ox + 32
    if region == 3:
        if kind == 0:  # reflection basin
            ellipse(p, cx, 34, 27, 13, SHADOW)
            ellipse(p, cx, 32, 25, 11, (83, 133, 158, 125))
            ellipse(p, cx, 31, 21, 8, (143, 194, 207, 105))
            line(p, ox + 14, 29, ox + 50, 29, R3_LIGHT)
            line(p, ox + 19, 35, ox + 45, 35, R3_MID)
            for x in (20, 32, 44):
                put(p, ox + x, 27, PALE)
        elif kind == 1:  # mirror fracture tracery
            for dx, dy in ((0, -23), (18, -12), (22, 8), (8, 21), (-15, 17), (-22, -3)):
                line(p, cx, 32, cx + dx, 32 + dy, R3_MID)
            diamond(p, cx, 32, 3, R3_LIGHT)
            for x, y in ((13, 18), (48, 17), (17, 48), (47, 45)):
                diamond(p, ox + x, y, 2, R3_LILAC)
        elif kind == 2:  # pale pebble clearing
            ellipse(p, cx, 35, 24, 12, (98, 125, 112, 58))
            for x, y, r in ((15, 34, 4), (24, 27, 3), (37, 39, 5), (48, 30, 3), (28, 44, 2)):
                ellipse(p, ox + x, y, r, max(2, r - 2), STONE)
                put(p, ox + x - 1, y - 1, R3_LIGHT)
        elif kind == 3:  # ghost-bloom bed
            ellipse(p, cx, 39, 25, 9, (95, 142, 111, 65))
            for x, y in ((12, 40), (20, 34), (29, 42), (39, 35), (49, 41), (55, 35)):
                line(p, ox + x, y + 5, ox + x, y - 3, R3_GREEN)
                diamond(p, ox + x, y - 4, 3, R3_LIGHT if x % 2 else R3_LILAC)
                put(p, ox + x, y - 4, PALE)
        elif kind == 4:  # twin root reflection
            ring(p, ox + 23, 34, 13, 8, R3_GREEN, TRANSPARENT)
            ring(p, ox + 41, 34, 13, 8, R3_GREEN, TRANSPARENT)
            line(p, ox + 12, 34, ox + 52, 34, R3_DARK)
            diamond(p, cx, 34, 3, R3_LIGHT)
        elif kind == 5:  # scattered shard dust
            for x, y, r, c in ((12, 21, 3, R3_MID), (23, 39, 2, R3_LIGHT), (34, 20, 4, R3_LILAC), (45, 43, 3, R3_MID), (53, 28, 2, PALE), (16, 49, 2, R3_LIGHT)):
                diamond(p, ox + x, y, r, c)
                put(p, ox + x, y - r, PALE)
        elif kind == 6:  # quiet reflection ring
            ring(p, cx, 32, 22, 12, R3_DARK, TRANSPARENT)
            ring(p, cx, 32, 16, 8, R3_MID, TRANSPARENT)
            line(p, ox + 18, 32, ox + 46, 32, R3_LIGHT)
            diamond(p, cx, 32, 2, PALE)
        else:  # fern mat
            ellipse(p, cx, 43, 26, 7, (83, 126, 91, 65))
            for x in range(12, 55, 6):
                line(p, ox + x, 47, ox + x + (2 if x % 12 else -3), 31 - (x % 5), R3_GREEN)
                line(p, ox + x, 39, ox + x - 4, 35, R3_GREEN)
                line(p, ox + x, 36, ox + x + 4, 33, R3_GREEN)
    else:
        if kind == 0:  # ignis scorch patch
            ellipse(p, cx, 35, 26, 12, (93, 61, 54, 90))
            ring(p, cx, 34, 20, 9, R4_IGNIS, TRANSPARENT)
            for x0, y0, x1, y1 in ((16, 42, 25, 31), (47, 43, 39, 30), (27, 48, 31, 36), (38, 48, 35, 35)):
                line(p, ox + x0, y0, ox + x1, y1, R4_IGNIS)
        elif kind == 1:  # vita root patch
            ellipse(p, cx, 40, 26, 9, (69, 111, 71, 70))
            for x0, y0, x1, y1 in ((9, 45, 31, 33), (55, 45, 33, 33), (18, 51, 31, 35), (47, 52, 34, 35), (30, 53, 32, 35)):
                line(p, ox + x0, y0, ox + x1, y1, R4_VITA)
            diamond(p, cx, 33, 4, PALE)
        elif kind == 2:  # aether current patch
            for y in (24, 32, 40):
                line(p, ox + 9, y, ox + 24, y - 5, R4_AETHER)
                line(p, ox + 24, y - 5, ox + 40, y + 3, R4_AETHER)
                line(p, ox + 40, y + 3, ox + 55, y - 4, R4_RESONANCE)
            for x, y in ((15, 22), (31, 35), (50, 28)):
                diamond(p, ox + x, y, 2, PALE)
        elif kind == 3:  # tricolor resonance sigil
            ring(p, cx, 32, 24, 14, R4_RESONANCE, TRANSPARENT)
            line(p, cx, 32, ox + 32, 12, R4_IGNIS)
            line(p, cx, 32, ox + 14, 45, R4_VITA)
            line(p, cx, 32, ox + 50, 45, R4_AETHER)
            diamond(p, cx, 32, 4, GOLD)
            diamond(p, cx, 32, 1, PALE)
        elif kind == 4:  # harmonic grass mat
            ellipse(p, cx, 44, 26, 7, (72, 110, 74, 60))
            cols = [R4_IGNIS, R4_VITA, R4_AETHER, R4_RESONANCE]
            for i, x in enumerate(range(10, 57, 5)):
                line(p, ox + x, 48, ox + x + (i % 3 - 1) * 3, 31 + (i % 4), cols[i % 4])
        elif kind == 5:  # resonant shard dust
            cols = [R4_IGNIS, R4_VITA, R4_AETHER, R4_RESONANCE]
            for i, (x, y, r) in enumerate(((12, 23, 3), (20, 43, 2), (31, 27, 4), (42, 43, 3), (52, 24, 2), (48, 34, 2), (16, 34, 2))):
                diamond(p, ox + x, y, r, cols[i % 4])
                put(p, ox + x, y - r, PALE)
        elif kind == 6:  # braided resonance rings
            ring(p, ox + 25, 33, 16, 10, R4_VITA, TRANSPARENT)
            ring(p, ox + 39, 33, 16, 10, R4_AETHER, TRANSPARENT)
            line(p, ox + 21, 33, ox + 43, 33, R4_IGNIS)
            diamond(p, cx, 33, 3, R4_RESONANCE)
        else:  # tri-pebble field
            ellipse(p, cx, 39, 24, 10, (83, 80, 92, 55))
            cols = [R4_IGNIS, R4_VITA, R4_AETHER]
            for i, (x, y, r) in enumerate(((14, 40, 4), (24, 31, 3), (34, 43, 4), (45, 32, 3), (53, 43, 2))):
                ellipse(p, ox + x, y, r, max(2, r - 2), STONE)
                put(p, ox + x, y - 1, cols[i % 3])


def build_terrain_atlas(path: Path, region: int):
    p = canvas(512, 64)
    for i in range(8):
        terrain_cell(p, i * 64, i, region)
    write_png(path, 512, 64, p)


build_terrain_atlas(ROOT / 'assets/region3_mirrorwild_terrain.png', 3)
build_terrain_atlas(ROOT / 'assets/region4_resonance_terrain.png', 4)


# ---------- version bump ----------
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if VERSION not in text:
        if PREV not in text:
            raise RuntimeError(f'version {rel}: {PREV} not found')
        text = text.replace(PREV, VERSION)
        path.write_text(text, encoding='utf-8')


# ---------- map metadata + safe Back-layer ground variation ----------
def deepen_map(rel: str, region: int):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    text = text.replace('CardchaRegionVersion" value="0675"', 'CardchaRegionVersion" value="0676"')
    text = text.replace(
        'cardcha-owned-map|vanilla-tiles|authored-native-enemies|authored-biome-decor',
        'cardcha-owned-map|vanilla-tiles|authored-native-enemies|authored-biome-decor|authored-terrain-depth'
    )
    if 'CardchaTerrainDepth' not in text:
        terrain_value = 'reflection-basin|paired-clearings|ground-clusters' if region == 3 else 'resonance-core|ignis-vita-aether-triad|ground-clusters'
        text = text.replace('  <property name="CardchaLayout"', f'  <property name="CardchaTerrainDepth" value="{terrain_value}" />\n  <property name="CardchaLayout"', 1)
    if region == 3:
        text = text.replace('mirrored-trails|reflection-crossings|south-airship-pad', 'mirrored-trails|reflection-basin|paired-clearings|south-airship-pad')
    else:
        text = text.replace('central-resonance-lane|tricolor-spokes|south-airship-pad', 'central-resonance-core|ignis-vita-aether-spokes|south-airship-pad')

    # Only Back-layer appearance changes. Buildings/collision and combat lanes remain untouched.
    m = re.search(r'(<layer id="1" name="Back"[^>]*>\s*<data encoding="csv">)(.*?)(</data>)', text, flags=re.S)
    if not m:
        raise RuntimeError(f'{rel}: Back CSV not found')
    vals = [int(tok.strip()) for tok in m.group(2).split(',') if tok.strip()]
    w, h = 40, 28
    if len(vals) != w * h:
        raise RuntimeError(f'{rel}: Back CSV {len(vals)} != {w*h}')

    centers = (
        [(20, 14, 3, 2), (10, 7, 2, 2), (30, 7, 2, 2), (7, 16, 2, 2), (33, 16, 2, 2), (12, 22, 2, 1), (28, 22, 2, 1)]
        if region == 3 else
        [(20, 14, 3, 2), (20, 6, 2, 2), (9, 19, 2, 2), (31, 19, 2, 2), (13, 11, 2, 1), (27, 11, 2, 1)]
    )
    for cx, cy, rx, ry in centers:
        for y in range(max(1, cy - ry), min(h - 1, cy + ry + 1)):
            for x in range(max(1, cx - rx), min(w - 1, cx + rx + 1)):
                i = y * w + x
                if vals[i] != 457 and ((x + y + region) % 3 != 0):
                    vals[i] = 382

    new_csv = ',\n'.join(','.join(str(vals[y * w + x]) for x in range(w)) for y in range(h))
    text = text[:m.start(2)] + new_csv + text[m.end(2):]
    path.write_text(text, encoding='utf-8')


deepen_map('assets/region3_mirrorwild.tmx', 3)
deepen_map('assets/region4_resonance_verge.tmx', 4)


# ---------- Region expedition visual renderer ----------
path = ROOT / 'Services/RegionExpeditionService.cs'
s = path.read_text(encoding='utf-8')
s = s.replace('0675', '0676')
s = s.replace(
    '/// 0676 authored visual pass for Region III Mirrorwild and Region IV Resonance Verge.\n'
    '/// Three-wave gameplay, rewards, route gates and extraction remain the 0674 contract.\n'
    '/// Vanilla monsters are gameplay proxies only; their draw is suppressed and native 32px Cardcha art\n'
    '/// is rendered at Stardew\'s fixed 4x world pixel scale.',
    '/// 0676 terrain-depth pass for Region III Mirrorwild and Region IV Resonance Verge.\n'
    '/// Three-wave gameplay, rewards, route gates, authored enemy silhouettes and extraction remain frozen.\n'
    '/// Low-profile 64px terrain clusters deepen the two biomes without screen tinting, fake colliders,\n'
    '/// or any per-enemy sprite enlargement.'
)

s = replace_once(
    s,
    '    private const string Region3DecorAtlasPath = "assets/region3_mirrorwild_decor.png";\n'
    '    private const string Region4DecorAtlasPath = "assets/region4_resonance_decor.png";\n'
    '    public const string EnemyMarkerKey',
    '    private const string Region3DecorAtlasPath = "assets/region3_mirrorwild_decor.png";\n'
    '    private const string Region4DecorAtlasPath = "assets/region4_resonance_decor.png";\n'
    '    private const string Region3TerrainAtlasPath = "assets/region3_mirrorwild_terrain.png";\n'
    '    private const string Region4TerrainAtlasPath = "assets/region4_resonance_terrain.png";\n'
    '    public const string EnemyMarkerKey',
    'terrain atlas constants'
)

s = replace_once(
    s,
    '    private Texture2D? Region3DecorAtlas;\n'
    '    private Texture2D? Region4DecorAtlas;\n'
    '    private bool Region3ArtLoadFailed;\n'
    '    private bool Region4ArtLoadFailed;',
    '    private Texture2D? Region3DecorAtlas;\n'
    '    private Texture2D? Region4DecorAtlas;\n'
    '    private Texture2D? Region3TerrainAtlas;\n'
    '    private Texture2D? Region4TerrainAtlas;\n'
    '    private bool Region3ArtLoadFailed;\n'
    '    private bool Region4ArtLoadFailed;\n'
    '    private bool Region3TerrainLoadFailed;\n'
    '    private bool Region4TerrainLoadFailed;',
    'terrain atlas fields'
)

if 'private void DrawTerrainClusters(' not in s:
    start = s.index('    private void DrawRegionIdentity(')
    end = s.index('    private void DrawEnemyIdentity(', start)
    renderer = r'''    private void DrawRegionIdentity(SpriteBatch batch, GameLocation location, ExpeditionRegion region)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;

        Texture2D? terrain = this.GetTerrainAtlas(region);
        if (terrain is not null)
            this.DrawTerrainClusters(batch, terrain, region);

        Texture2D? decor = this.GetDecorAtlas(region);
        if (decor is not null)
            this.DrawDecorClusters(batch, decor, region);

        Point extract = ResolveExtractionTile(location);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(extract.X * 64f + 32f, extract.Y * 64f + 32f));
        Color c = region == ExpeditionRegion.Mirrorwild ? new Color(143, 187, 226) : new Color(197, 135, 218);
        float pulse = 0.44f + 0.11f * (float)Math.Sin(Environment.TickCount64 / 260d);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 25, (int)local.Y - 2, 50, 4), c * pulse);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 2, (int)local.Y - 25, 4, 50), c * pulse);

        // Small ambient flecks only. Terrain identity comes from authored ground forms, not a screen tint.
        for (int i = 0; i < 12; i++)
        {
            int x = 3 + (i * 11 + (int)region * 7) % Math.Max(4, width - 6);
            int y = 3 + (i * 7 + (int)region * 5) % Math.Max(4, height - 7);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, new Vector2(x * 64f + 32f, y * 64f + 32f));
            int size = i % 4 == 0 ? 3 : 2;
            batch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y, size, size), c * 0.24f);
        }
    }

    private void DrawTerrainClusters(SpriteBatch batch, Texture2D terrain, ExpeditionRegion region)
    {
        // Mirrorwild is deliberately bilateral; Resonance Verge reads as a three-pole elemental triad.
        (Point, int)[] clusters = region == ExpeditionRegion.Mirrorwild
            ? new (Point, int)[]
            {
                (new Point(20,14),0),
                (new Point(10,7),6),(new Point(30,7),6),
                (new Point(7,16),2),(new Point(33,16),2),
                (new Point(12,22),3),(new Point(28,22),3),
                (new Point(13,4),5),(new Point(27,4),5),
                (new Point(5,23),7),(new Point(35,23),7),
                (new Point(17,10),1),(new Point(23,10),1),
                (new Point(15,18),4),(new Point(25,18),4),
            }
            : new (Point, int)[]
            {
                (new Point(20,14),3),
                (new Point(20,6),0),
                (new Point(8,19),1),(new Point(32,19),2),
                (new Point(14,11),6),(new Point(26,11),6),
                (new Point(12,23),4),(new Point(28,23),4),
                (new Point(6,8),5),(new Point(34,8),5),
                (new Point(20,22),7),
                (new Point(8,14),1),(new Point(32,14),2),
            };

        for (int i = 0; i < clusters.Length; i++)
        {
            Point anchor = clusters[i].Item1;
            int cell = clusters[i].Item2;
            Rectangle src = new(cell * 64, 0, 64, 64);
            Vector2 world = new(anchor.X * 64f + 32f, anchor.Y * 64f + 32f);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);
            float alpha = i == 0 ? 0.92f : 0.72f;
            batch.Draw(terrain, p, src, Color.White * alpha, 0f, new Vector2(32f, 32f),
                AuthoredWorldScale, SpriteEffects.None, 0.001f);
        }
    }

    private void DrawDecorClusters(SpriteBatch batch, Texture2D decor, ExpeditionRegion region)
    {
        (Point, int)[] anchors = region == ExpeditionRegion.Mirrorwild
            ? new (Point, int)[]
            {
                (new Point(4,5),0),(new Point(36,5),0),
                (new Point(8,10),3),(new Point(32,10),3),
                (new Point(4,18),6),(new Point(36,18),6),
                (new Point(10,23),1),(new Point(30,23),1),
                (new Point(14,5),2),(new Point(26,5),2),
                (new Point(8,14),7),(new Point(32,14),7),
                (new Point(13,19),4),(new Point(27,19),4),
                (new Point(17,7),5),(new Point(23,7),5),
            }
            : new (Point, int)[]
            {
                (new Point(4,6),6),(new Point(36,6),6),
                (new Point(10,10),0),(new Point(30,10),0),
                (new Point(5,20),3),(new Point(35,20),3),
                (new Point(13,23),1),(new Point(27,23),1),
                (new Point(15,7),2),(new Point(25,7),2),
                (new Point(9,16),7),(new Point(31,16),7),
                (new Point(14,18),4),(new Point(26,18),4),
                (new Point(20,5),5),(new Point(20,20),5),
            };

        for (int i = 0; i < anchors.Length; i++)
        {
            Point a = anchors[i].Item1;
            int cell = anchors[i].Item2;
            Rectangle src = new(cell * 32, 0, 32, 32);
            Vector2 world = new(a.X * 64f + 32f, a.Y * 64f + 58f);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);
            float layer = Math.Clamp((world.Y + 22f) / 10000f, 0f, 0.92f);
            batch.Draw(decor, p, src, Color.White, 0f, new Vector2(16f, 28f),
                AuthoredWorldScale, SpriteEffects.None, layer);
        }
    }

'''
    s = s[:start] + renderer + s[end:]

if 'private Texture2D? GetTerrainAtlas(' not in s:
    anchor = '    private Texture2D? GetEnemyAtlas(ExpeditionRegion region)\n'
    idx = s.index(anchor)
    terrain_loader = r'''    private Texture2D? GetTerrainAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
                return this.Region3TerrainAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region3TerrainAtlasPath);
            return this.Region4TerrainAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region4TerrainAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.Mirrorwild && !this.Region3TerrainLoadFailed)
            {
                this.Region3TerrainLoadFailed = true;
                this.Monitor.Log($"0676 Mirrorwild terrain atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            else if (region == ExpeditionRegion.ResonanceVerge && !this.Region4TerrainLoadFailed)
            {
                this.Region4TerrainLoadFailed = true;
                this.Monitor.Log($"0676 Resonance terrain atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            return null;
        }
    }

'''
    s = s[:idx] + terrain_loader + s[idx:]

path.write_text(s, encoding='utf-8')


# ---------- ModEntry identity ----------
path = ROOT / 'ModEntry.cs'
entry = path.read_text(encoding='utf-8')
entry = entry.replace(PREV, VERSION)
entry = entry.replace('REGION III / IV AUTHORED VISUAL PASS TEST', 'REGION III / IV TERRAIN DEPTH PASS TEST')
path.write_text(entry, encoding='utf-8')


# ---------- handoff ----------
handoff = f'''# Alpha28 0676 - Region III / IV Terrain Depth Pass

Build: `{VERSION}`  
Branch: `{BRANCH}`
Status: CI validation first, in-game visual acceptance pending.

## What 0676 changes
- Mirrorwild gains a dedicated 512x64 authored terrain atlas with a central reflection basin, bilateral reflection rings, pale clearings, shard dust, bloom beds and fern mats.
- Resonance Verge gains a separate 512x64 terrain atlas with a tricolor resonance core and distinct Ignis, Vita and Aether ground formations.
- Terrain clusters are low-profile ground art at fixed Stardew 4x pixel scale. No new fake collider, no full-screen tint and no enlarged monster art.
- Existing 0675 enemy silhouettes and proxy suppression remain unchanged.
- Existing 0675 decor remains unchanged; 0676 reorganizes its placement into stronger Mirrorwild bilateral composition and Resonance triad composition.
- The TMX Back layer gets safe ground-only variation around landmark clearings. Buildings/collision layers and combat lanes are untouched.

## Frozen gameplay contract
- Region III/IV remain three-wave expeditions.
- Region III full clear remains 47 Scrap + 3 Shiny.
- Region IV full clear remains 69 Scrap + 6 Shiny.
- Region III fare remains 500g; Region IV fare remains 1000g.
- Unbanked extraction and return flight remain unchanged.
- Boss II/III/IV 40/60/80-card milestone priority remains unchanged.
- Save schema remains 19 and the active card audit remains 76/80.
- Enemy HP/speed/archetype selection from 0674/0675 is unchanged.

## In-game acceptance
1. `cardcha_test_region3`: confirm the center reads as a reflective wilderness landmark and the left/right composition feels intentionally mirrored.
2. Run/clear all three Region III waves. Verify authored enemies are still targetable and no vanilla Bat/Bug/Slime art bleeds through.
3. `cardcha_test_region4`: confirm the center reads as a resonance core and the three elemental ground languages are visually distinct without screen tinting.
4. Run/clear all three Region IV waves and verify target/damage/death/drop behavior is unchanged.
5. Capture one screenshot of each region with enemies active. Judge map density, landmark readability and whether any ground cluster covers the player awkwardly.
6. Extract once from each region and confirm the frozen 0674 reward totals and return flight.

## Next decision after screenshots
- If density is good, continue Region III/IV encounter identity/replayability rather than adding more decoration.
- If any cluster reads like a fake obstacle, move it to the perimeter or convert it into lower ground art. Do not solve it by enlarging enemy sprites.
'''
write_text(Path('handoff/ALPHA28_0676_REGION3_REGION4_TERRAIN_DEPTH_PASS.md'), handoff)
write_text(Path('handoff/LATEST_CARDCHA_HANDOFF.md'), f'''# Latest Cardcha Handoff

Current branch: `{BRANCH}`
Current build: `{VERSION}`
Continue from: `handoff/ALPHA28_0676_REGION3_REGION4_TERRAIN_DEPTH_PASS.md`

0676 in-game visual acceptance is pending. Do not resume from stale `main` or pre-0676 branches.
''')

print('0676 Region III / IV terrain depth pass generated')
