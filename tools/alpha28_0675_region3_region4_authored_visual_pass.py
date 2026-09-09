from pathlib import Path
import json, struct, zlib

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.44'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.43'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


# ---------- deterministic tiny PNG writer (stdlib only) ----------
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
    return [[(0,0,0,0) for _ in range(w)] for _ in range(h)]


def put(p, x, y, c):
    if 0 <= y < len(p) and 0 <= x < len(p[0]): p[y][x] = c


def rect(p, x, y, w, h, c):
    for yy in range(y, y+h):
        for xx in range(x, x+w): put(p, xx, yy, c)


def ellipse(p, cx, cy, rx, ry, c):
    if rx <= 0 or ry <= 0: return
    for y in range(cy-ry, cy+ry+1):
        for x in range(cx-rx, cx+rx+1):
            if ((x-cx)*(x-cx))/(rx*rx) + ((y-cy)*(y-cy))/(ry*ry) <= 1.0: put(p,x,y,c)


def diamond(p, cx, cy, r, c):
    for y in range(cy-r, cy+r+1):
        rem = r-abs(y-cy)
        for x in range(cx-rem, cx+rem+1): put(p,x,y,c)


def line(p, x0, y0, x1, y1, c):
    dx=abs(x1-x0); sx=1 if x0<x1 else -1; dy=-abs(y1-y0); sy=1 if y0<y1 else -1; err=dx+dy
    while True:
        put(p,x0,y0,c)
        if x0==x1 and y0==y1: break
        e2=2*err
        if e2>=dy: err+=dy; x0+=sx
        if e2<=dx: err+=dx; y0+=sy


OUTLINE=(38,34,48,255); SHADOW=(28,28,38,210); WHITE=(235,244,247,255); GOLD=(232,201,106,255)
R3=[(93,132,169,255),(128,190,214,255),(177,224,230,255),(200,184,226,255)]
R4=[(218,112,82,255),(111,188,119,255),(101,151,220,255),(197,132,213,255)]


def enemy_cell(p, ox, role, frame):
    # Every frame is authored directly inside a 32x32 logical cell. World draw is fixed Stardew 4x.
    bob = frame
    if role == 'mirror_wisp':
        ellipse(p,ox+16,12+bob,8,8,OUTLINE); ellipse(p,ox+16,12+bob,6,6,R3[2]); diamond(p,ox+16,12+bob,3,WHITE)
        for i in range(4): line(p,ox+12+i*3,18+bob,ox+9+i*4,27-bob,R3[1])
        put(p,ox+13,10+bob,WHITE); put(p,ox+19,10+bob,WHITE)
    elif role == 'glass_scarab':
        ellipse(p,ox+16,17-bob,9,7,OUTLINE); ellipse(p,ox+16,16-bob,7,6,R3[1]); diamond(p,ox+16,15-bob,5,R3[2]); line(p,ox+16,10,ox+16,22,OUTLINE)
        for dy in (13,17,21):
            line(p,ox+8,dy-bob,ox+3,dy-2+(frame*4),R3[0]); line(p,ox+24,dy-bob,ox+29,dy-2+(frame*4),R3[0])
        diamond(p,ox+16,15-bob,2,WHITE)
    elif role == 'echo_slime':
        ellipse(p,ox+16,19-bob,10,9,OUTLINE); rect(p,ox+6,19-bob,21,7,OUTLINE); ellipse(p,ox+16,18-bob,8,7,R3[0]); rect(p,ox+8,18-bob,17,7,R3[0])
        put(p,ox+12,17-bob,WHITE); put(p,ox+20,17-bob,WHITE); line(p,ox+14,22-bob,ox+18,22-bob,R3[2]); rect(p,ox+8,24-bob,16,2,R3[1])
    elif role == 'mirror_sentinel':
        rect(p,ox+12,8-bob,9,17,OUTLINE); rect(p,ox+14,9-bob,5,15,R3[0]); diamond(p,ox+16,8-bob,6,OUTLINE); diamond(p,ox+16,8-bob,4,GOLD)
        rect(p,ox+8,15-bob,5,9,OUTLINE); diamond(p,ox+8,18-bob,5,R3[2]); diamond(p,ox+8,18-bob,2,WHITE); rect(p,ox+21,13-bob,3,12,GOLD)
        rect(p,ox+11,25-bob,5,3,OUTLINE); rect(p,ox+18,25-bob,5,3,OUTLINE)
    elif role == 'ignis_echo':
        diamond(p,ox+16,16-bob,10,OUTLINE); diamond(p,ox+16,16-bob,8,R4[0]); diamond(p,ox+16,13-bob,5,(244,162,94,255)); diamond(p,ox+16,12-bob,2,WHITE)
        for x in (10,16,22): line(p,ox+x,21-bob,ox+x+(frame*2-1),28,R4[0])
    elif role == 'vita_husk':
        rect(p,ox+10,12-bob,13,14,OUTLINE); rect(p,ox+12,13-bob,9,12,(84,130,82,255)); ellipse(p,ox+16,9-bob,8,5,OUTLINE); ellipse(p,ox+16,9-bob,6,4,R4[1]); diamond(p,ox+16,17-bob,3,(167,221,138,255))
        line(p,ox+10,17,ox+5,21+(frame*2),R4[1]); line(p,ox+22,17,ox+27,21+(frame*2),R4[1]); rect(p,ox+10,26-bob,5,3,OUTLINE); rect(p,ox+19,26-bob,5,3,OUTLINE)
    elif role == 'aether_mite':
        diamond(p,ox+16,16-bob,7,OUTLINE); diamond(p,ox+16,16-bob,5,R4[2]); diamond(p,ox+16,14-bob,2,WHITE)
        diamond(p,ox+7,15-bob+(frame*2),6,(125,185,233,220)); diamond(p,ox+25,15-bob+(frame*2),6,(125,185,233,220)); line(p,ox+14,10,ox+11,5,R4[3]); line(p,ox+18,10,ox+21,5,R4[3])
    elif role == 'resonant_prime':
        rect(p,ox+10,10-bob,13,16,OUTLINE); rect(p,ox+12,12-bob,9,12,(86,75,107,255)); diamond(p,ox+16,10-bob,7,OUTLINE); diamond(p,ox+16,10-bob,5,R4[3]); diamond(p,ox+16,16-bob,3,GOLD)
        diamond(p,ox+8,18-bob,5,R4[0]); diamond(p,ox+24,18-bob,5,R4[2]); rect(p,ox+11,26-bob,5,3,OUTLINE); rect(p,ox+19,26-bob,5,3,OUTLINE); put(p,ox+16,8-bob,WHITE)


def build_enemy_atlas(path, roles):
    p=canvas(32*len(roles)*2,32)
    for ri, role in enumerate(roles):
        for frame in range(2): enemy_cell(p,(ri*2+frame)*32,role,frame)
    write_png(path,len(roles)*64,32,p)


def decor_cell(p, ox, kind, region):
    c = R3 if region==3 else R4
    if kind==0: # shrub/crystal clump
        ellipse(p,ox+16,23,10,4,SHADOW); diamond(p,ox+11,17,6,c[0]); diamond(p,ox+19,14,8,c[1]); diamond(p,ox+24,19,5,c[2]); put(p,ox+19,10,WHITE)
    elif kind==1: # mushroom / harmonic flower
        rect(p,ox+15,17,3,10,(93,75,60,255)); ellipse(p,ox+16,15,8,4,c[2]); rect(p,ox+10,15,13,2,WHITE)
    elif kind==2: # stone
        ellipse(p,ox+16,21,10,6,OUTLINE); ellipse(p,ox+16,20,8,5,(90,95,112,255)); line(p,ox+11,18,ox+20,22,c[2]); line(p,ox+12,23,ox+21,17,c[3])
    elif kind==3: # reeds / resonance grass
        for x in range(8,26,3): line(p,ox+x,27,ox+x+(x%2)*2-1,11+(x%5),c[(x//3)%4]); rect(p,ox+7,27,20,2,SHADOW)
    elif kind==4: # pool / rune plate
        ellipse(p,ox+16,23,12,5,OUTLINE); ellipse(p,ox+16,23,10,3,c[0]); line(p,ox+8,23,ox+24,23,c[2]); diamond(p,ox+16,23,2,WHITE)
    elif kind==5: # broken arch
        rect(p,ox+7,11,4,17,OUTLINE); rect(p,ox+22,11,4,17,OUTLINE); rect(p,ox+9,9,15,4,OUTLINE); rect(p,ox+9,11,15,2,c[1]); diamond(p,ox+16,11,3,c[2])
    elif kind==6: # shard fan
        ellipse(p,ox+16,27,11,3,SHADOW); diamond(p,ox+12,20,7,c[0]); diamond(p,ox+18,17,9,c[2]); diamond(p,ox+24,22,5,c[3]); put(p,ox+18,9,WHITE)
    else: # tiny landmark flower/obelisk
        rect(p,ox+15,8,3,20,OUTLINE); diamond(p,ox+16,10,6,c[3]); diamond(p,ox+16,10,2,GOLD); line(p,ox+15,19,ox+9,15,c[1]); line(p,ox+18,21,ox+24,16,c[2])


def build_decor_atlas(path, region):
    p=canvas(256,32)
    for i in range(8): decor_cell(p,i*32,i,region)
    write_png(path,256,32,p)


build_enemy_atlas(ROOT/'assets/region3_mirrorwild_enemies.png', ['mirror_wisp','glass_scarab','echo_slime','mirror_sentinel'])
build_enemy_atlas(ROOT/'assets/region4_resonance_enemies.png', ['ignis_echo','vita_husk','aether_mite','resonant_prime'])
build_decor_atlas(ROOT/'assets/region3_mirrorwild_decor.png',3)
build_decor_atlas(ROOT/'assets/region4_resonance_decor.png',4)

# Version bump, including the manifest rewrite target.
for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets']:
    path=ROOT/rel; text=path.read_text(encoding='utf-8')
    if VERSION not in text:
        if PREV not in text: raise RuntimeError(f'version {rel}: {PREV} not found')
        path.write_text(text.replace(PREV,VERSION),encoding='utf-8')

# Mark the maps as 0675 authored-biome maps without altering combat lanes/collision.
for rel in ['assets/region3_mirrorwild.tmx','assets/region4_resonance_verge.tmx']:
    path=ROOT/rel; text=path.read_text(encoding='utf-8')
    text=text.replace('CardchaRegionVersion" value="0674"','CardchaRegionVersion" value="0675"')
    text=text.replace('cardcha-owned-map|vanilla-tiles-only|native-size-enemies','cardcha-owned-map|vanilla-tiles|authored-native-enemies|authored-biome-decor')
    path.write_text(text,encoding='utf-8')

# Expedition renderer upgrade. Gameplay/reward/fare logic stays untouched.
path=ROOT/'Services/RegionExpeditionService.cs'
s=path.read_text(encoding='utf-8')
s=s.replace('''/// 0674 gameplay foundation for the post-Boss-II and post-Boss-III regions.\n/// These are short three-wave expeditions, intentionally separate from Region I Hunt Run 2.0.\n/// Enemy proxies stay at native Stardew sprite scale; authored replacement art can land later\n/// without changing the combat/progression contract.''','''/// 0675 authored visual pass for Region III Mirrorwild and Region IV Resonance Verge.\n/// Three-wave gameplay, rewards, route gates and extraction remain the 0674 contract.\n/// Vanilla monsters are gameplay proxies only; their draw is suppressed and native 32px Cardcha art\n/// is rendered at Stardew's fixed 4x world pixel scale.''')
s=replace_once(s,
'''    private const string Region3MapPath = "assets/region3_mirrorwild.tmx";\n    private const string Region4MapPath = "assets/region4_resonance_verge.tmx";\n    private const string EnemyMarkerKey = "Ronvotri.Cardcha/0674ExpeditionEnemy";\n    private const string EnemyRoleKey = "Ronvotri.Cardcha/0674ExpeditionRole";''',
'''    private const string Region3MapPath = "assets/region3_mirrorwild.tmx";\n    private const string Region4MapPath = "assets/region4_resonance_verge.tmx";\n    private const string Region3EnemyAtlasPath = "assets/region3_mirrorwild_enemies.png";\n    private const string Region4EnemyAtlasPath = "assets/region4_resonance_enemies.png";\n    private const string Region3DecorAtlasPath = "assets/region3_mirrorwild_decor.png";\n    private const string Region4DecorAtlasPath = "assets/region4_resonance_decor.png";\n    public const string EnemyMarkerKey = "Ronvotri.Cardcha/0674ExpeditionEnemy";\n    public const string EnemyRoleKey = "Ronvotri.Cardcha/0674ExpeditionRole";\n    private const float AuthoredWorldScale = 4f;''','service art constants')
s=replace_once(s,
'''    private int DebugBypassRegion;\n\n    public RegionExpeditionService''',
'''    private int DebugBypassRegion;\n    private Texture2D? Region3EnemyAtlas;\n    private Texture2D? Region4EnemyAtlas;\n    private Texture2D? Region3DecorAtlas;\n    private Texture2D? Region4DecorAtlas;\n    private bool Region3ArtLoadFailed;\n    private bool Region4ArtLoadFailed;\n\n    public RegionExpeditionService''','service texture fields')
s=s.replace('0674 blocked unauthorized Region','0675 blocked unauthorized Region')
s=s.replace('0674 expedition started: {region}, native-size enemy proxies, 3-wave contract.','0675 expedition started: {region}, authored native-size enemy art, 3-wave gameplay contract unchanged.')
s=s.replace('enemy.modData[EnemyMarkerKey] = $"0674:{(int)region}:{wave}";','enemy.modData[EnemyMarkerKey] = $"0675:{(int)region}:{wave}";')
s=s.replace('0674 {region} wave {wave}/{WaveCount}: spawned={spawned}.','0675 {region} wave {wave}/{WaveCount}: spawned={spawned}.')
s=s.replace('0674 couldn\'t create {name}:','0675 couldn\'t create {name}:')

start=s.index('    private static void DrawRegionIdentity(')
end=s.index('    public string Describe()', start)
renderer=r'''    private void DrawRegionIdentity(SpriteBatch batch, GameLocation location, ExpeditionRegion region)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        Point extract = ResolveExtractionTile(location);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(extract.X * 64f + 32f, extract.Y * 64f + 32f));
        Color c = region == ExpeditionRegion.Mirrorwild ? new Color(143, 187, 226) : new Color(197, 135, 218);
        float pulse = 0.46f + 0.12f * (float)Math.Sin(Environment.TickCount64 / 260d);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 28, (int)local.Y - 2, 56, 4), c * pulse);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 2, (int)local.Y - 28, 4, 56), c * pulse);

        Texture2D? decor = this.GetDecorAtlas(region);
        if (decor is not null)
        {
            Point[] anchors = region == ExpeditionRegion.Mirrorwild
                ? new[] { new Point(4,5),new Point(9,9),new Point(4,18),new Point(11,23),new Point(29,5),new Point(35,11),new Point(34,19),new Point(27,23),new Point(15,5),new Point(24,18),new Point(31,15),new Point(8,14) }
                : new[] { new Point(4,6),new Point(10,11),new Point(5,20),new Point(13,23),new Point(34,6),new Point(30,12),new Point(35,20),new Point(27,23),new Point(15,7),new Point(25,8),new Point(10,17),new Point(30,18) };
            for (int i = 0; i < anchors.Length; i++)
            {
                Point a = anchors[i];
                Rectangle src = new((i % 8) * 32, 0, 32, 32);
                Vector2 world = new(a.X * 64f + 32f, a.Y * 64f + 58f);
                Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);
                float layer = Math.Clamp((world.Y + 22f) / 10000f, 0f, 0.92f);
                batch.Draw(decor, p, src, Color.White, 0f, new Vector2(16f, 28f), AuthoredWorldScale, SpriteEffects.None, layer);
            }
        }

        // Tiny ambient pixels support the biome without tinting the whole screen.
        for (int i = 0; i < 10; i++)
        {
            int x = 3 + (i * 11 + (int)region * 7) % Math.Max(4, width - 6);
            int y = 3 + (i * 7 + (int)region * 5) % Math.Max(4, height - 7);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, new Vector2(x * 64f + 32f, y * 64f + 32f));
            batch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y, 2, 2), c * 0.26f);
        }
    }

    private void DrawEnemyIdentity(SpriteBatch batch, Monster monster, ExpeditionRegion region)
    {
        if (!monster.modData.TryGetValue(EnemyRoleKey, out string? role) || string.IsNullOrWhiteSpace(role))
            return;

        Texture2D? atlas = this.GetEnemyAtlas(region);
        int roleIndex = RoleIndex(region, role);
        Vector2 world = monster.Position + new Vector2(32f, 64f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float layer = Math.Clamp((world.Y + 32f) / 10000f, 0f, 0.94f);
        bool floating = role is "mirror_wisp" or "ignis_echo" or "aether_mite";
        float bob = floating ? (float)Math.Sin(Environment.TickCount64 / 210d + monster.GetHashCode() * 0.01) * 4f : 0f;

        // A quiet authored shadow keeps the new silhouettes grounded even though their AI proxy is hidden.
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 31, (int)local.Y - 8, 62, 8), Color.Black * 0.20f);
        if (atlas is null || roleIndex < 0)
        {
            Color fallback = region == ExpeditionRegion.Mirrorwild ? new Color(139, 201, 226) : new Color(203, 137, 211);
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 18, (int)local.Y - 52, 36, 48), fallback * 0.82f);
            return;
        }

        int frame = (int)((Environment.TickCount64 / 280L + Math.Abs(monster.GetHashCode())) % 2L);
        Rectangle src = new((roleIndex * 2 + frame) * 32, 0, 32, 32);
        batch.Draw(atlas, local + new Vector2(0f, bob), src, Color.White, 0f,
            new Vector2(16f, 28f), AuthoredWorldScale, SpriteEffects.None, layer);
    }

    private Texture2D? GetEnemyAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
                return this.Region3EnemyAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region3EnemyAtlasPath);
            return this.Region4EnemyAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region4EnemyAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.Mirrorwild && !this.Region3ArtLoadFailed)
            {
                this.Region3ArtLoadFailed = true;
                this.Monitor.Log($"0675 Mirrorwild enemy atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            else if (region == ExpeditionRegion.ResonanceVerge && !this.Region4ArtLoadFailed)
            {
                this.Region4ArtLoadFailed = true;
                this.Monitor.Log($"0675 Resonance enemy atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            return null;
        }
    }

    private Texture2D? GetDecorAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
                return this.Region3DecorAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region3DecorAtlasPath);
            return this.Region4DecorAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region4DecorAtlasPath);
        }
        catch
        {
            return null;
        }
    }

    private static int RoleIndex(ExpeditionRegion region, string role)
        => region switch
        {
            ExpeditionRegion.Mirrorwild => role switch
            {
                "mirror_wisp" => 0,
                "glass_scarab" => 1,
                "echo_slime" => 2,
                "mirror_sentinel" => 3,
                _ => -1,
            },
            _ => role switch
            {
                "ignis_echo" => 0,
                "vita_husk" => 1,
                "aether_mite" => 2,
                "resonant_prime" => 3,
                _ => -1,
            }
        };

'''
s=s[:start]+renderer+s[end:]
s=s.replace('return "0674 Expedition=<no save>";','return "0675 Expedition=<no save>";')
s=s.replace('return $"0674 Expedition |','return $"0675 Expedition |')
s=s.replace('return "0674 TEST: load a save and use region 3 or 4.";','return "0675 TEST: load a save and use region 3 or 4.";')
s=s.replace('return $"0674 TEST: Region {region} map unavailable.";','return $"0675 TEST: Region {region} map unavailable.";')
s=s.replace('return $"0674 TEST: entered Region {region}','return $"0675 TEST: entered Region {region}')
s=s.replace('return "0674 TEST: enter an active Region III/IV expedition first.";','return "0675 TEST: enter an active Region III/IV expedition first.";')
s=s.replace('return $"0674 TEST: cleared current wave actors.','return $"0675 TEST: cleared current wave actors.')
path.write_text(s,encoding='utf-8')

# Hide only 0674/0675 expedition gameplay proxies. Other monsters are untouched.
patch=r'''using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>0675: expedition monsters keep real AI/hitboxes while Cardcha owns their visible authored art.</summary>
internal static class RegionExpeditionProxyDrawPatch
{
    public static void Apply(Harmony harmony)
    {
        HashSet<MethodInfo> targets = new();
        foreach (Type type in new[] { typeof(GreenSlime), typeof(Bat), typeof(Bug) })
        {
            MethodInfo? target = AccessTools.Method(type, "draw", new[] { typeof(SpriteBatch) });
            if (target is not null)
                targets.Add(target);
        }
        if (targets.Count == 0)
            throw new MissingMethodException("Could not resolve expedition monster draw methods.");
        HarmonyMethod prefix = new(typeof(RegionExpeditionProxyDrawPatch), nameof(Prefix));
        foreach (MethodInfo target in targets)
            harmony.Patch(target, prefix: prefix);
    }

    private static bool Prefix(Monster __instance)
        => !__instance.modData.ContainsKey(RegionExpeditionService.EnemyMarkerKey);
}
'''
write_text(ROOT/'Patches/RegionExpeditionProxyDrawPatch.cs',patch)

# Register the proxy renderer patch and bump visible build label.
entry=ROOT/'ModEntry.cs'; m=entry.read_text(encoding='utf-8')
m=replace_once(m,'        VerdantGuardianProxyDrawPatch.Apply(harmony);\n','        VerdantGuardianProxyDrawPatch.Apply(harmony);\n        RegionExpeditionProxyDrawPatch.Apply(harmony);\n','ModEntry expedition draw patch')
m=m.replace('Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.43 REGION III / IV EXPEDITION FOUNDATION TEST',
            'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.44 REGION III / IV AUTHORED VISUAL PASS TEST')
entry.write_text(m,encoding='utf-8')

handoff=f'''# Alpha28 0675 - Region III / IV Authored Visual Pass\n\nBuild: `{VERSION}`  \nBranch: `cardcha-alpha28-0675-region3-region4-authored-visual-pass`\nStatus: CI validation first, in-game visual acceptance pending.\n\n## What 0675 changes\n- Mirrorwild now has a dedicated authored decor atlas and four native 32px enemy silhouettes: Mirror Wisp, Glass Scarab, Echo Slime, Mirror Sentinel.\n- Resonance Verge now has a separate authored decor atlas and four native 32px enemy silhouettes: Ignis Echo, Vita Husk, Aether Mite, Resonant Prime.\n- All authored actors render at the fixed Stardew `4x` world pixel scale. There is no per-enemy blow-up multiplier.\n- Vanilla GreenSlime/Bat/Bug actors remain authoritative for AI, collision, damage, team targeting, death and Scrap drops, but their visible draw is suppressed only when marked as Region III/IV expedition proxies.\n- Biome identity uses small physical props and edge clusters. No full-screen tint, giant sci-fi overlay, or floating room labels.\n\n## Frozen 0674 gameplay contract\n- Region III and IV remain three-wave expeditions.\n- Region III full clear remains 47 Scrap + 3 Shiny.\n- Region IV full clear remains 69 Scrap + 6 Shiny.\n- Unbanked extraction behavior is unchanged.\n- Region III fare remains 500g; Region IV fare remains 1000g.\n- 40/60/80-card milestone priority and Boss II/III/IV behavior are unchanged.\n- Save schema remains 19.\n\n## In-game acceptance\n1. `cardcha_test_region3`: inspect all four Mirrorwild silhouettes across waves. No vanilla Bat/Bug/Slime art should bleed through.\n2. `cardcha_expedition_clear`: advance waves and verify all enemies remain targetable/damageable.\n3. Confirm Mirrorwild reads as pale reflective wilderness, not a recolored test room.\n4. `cardcha_test_region4`: inspect Ignis/Vita/Aether differentiation and Resonant Prime.\n5. Confirm Resonance Verge looks materially different from Mirrorwild without a screen tint.\n6. Complete/extract once from each region and verify 0674 reward totals and return flight remain unchanged.\n7. If screenshots still feel sparse, 0676 should deepen authored terrain clusters rather than enlarge sprites.\n'''
write_text(Path('handoff/ALPHA28_0675_REGION3_REGION4_AUTHORED_VISUAL_PASS.md'),handoff)
write_text(Path('handoff/LATEST_CARDCHA_HANDOFF.md'),f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0675-region3-region4-authored-visual-pass`\nCurrent build: `{VERSION}`\nContinue from: `handoff/ALPHA28_0675_REGION3_REGION4_AUTHORED_VISUAL_PASS.md`\n\n0675 in-game visual acceptance is pending. Do not resume from stale `main` or pre-0675 branches.\n''')

print('0675 authored Region III / IV visual pass generated')
