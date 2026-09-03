from pathlib import Path
import hashlib
import json
import re

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
ASSETS = SRC / "assets"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.5"
LOCKED_SHA = "1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132"

source = ASSETS / "airship_visual.png"
if hashlib.sha256(source.read_bytes()).hexdigest() != LOCKED_SHA:
    raise SystemExit("Locked airship_visual.png hash changed; refusing to derive layers from an unapproved sprite.")

im = Image.open(source).convert("RGBA")
if im.size != (384, 256):
    raise SystemExit(f"Unexpected airship sprite size: {im.size}")

px = im.load()
w, h = im.size

# Split the official sprite into real runtime planes. The 112..150 transition band is shared
# smoothly between balloon and hull so the rest pose stays visually continuous, while the renderer
# can give the two masses a tiny independent bob without editing the locked source artwork.
balloon = Image.new("RGBA", im.size, (0, 0, 0, 0))
hull = Image.new("RGBA", im.size, (0, 0, 0, 0))
rigging = Image.new("RGBA", im.size, (0, 0, 0, 0))
glow = Image.new("RGBA", im.size, (0, 0, 0, 0))

for y in range(h):
    if y <= 112:
        bw = 1.0
    elif y >= 150:
        bw = 0.0
    else:
        bw = (150 - y) / 38.0
    hw = 1.0 - bw

    for x in range(w):
        r, g, b, a = px[x, y]
        if a == 0:
            continue

        ba = int(round(a * bw))
        ha = int(round(a * hw))
        if ba:
            balloon.putpixel((x, y), (r, g, b, ba))
        if ha:
            hull.putpixel((x, y), (r, g, b, ha))

        brightness = (r + g + b) / 3.0
        warm_dark = 78 <= y <= 191 and brightness < 125 and r >= b - 10 and g <= r + 12
        if warm_dark:
            rigging.putpixel((x, y), (r, g, b, a))

        cyan = b > 130 and g > 120 and b > r + 30
        violet = b > 110 and r > 70 and b > g + 15
        gold = r > 150 and g > 85 and b < 110 and r > g + 25
        if (cyan or violet or gold) and a >= 64:
            glow.putpixel((x, y), (r, g, b, int(a * 0.80)))

alpha = im.getchannel("A").filter(ImageFilter.GaussianBlur(radius=4))
shadow = Image.new("RGBA", im.size, (22, 16, 29, 0))
shadow.putalpha(alpha.point(lambda value: int(value * 0.42)))

layers = {
    "airship_layer_shadow.png": shadow,
    "airship_layer_balloon.png": balloon,
    "airship_layer_hull.png": hull,
    "airship_layer_rigging.png": rigging,
    "airship_layer_glow.png": glow,
}
for name, layer in layers.items():
    layer.save(ASSETS / name, format="PNG", optimize=False)

renderer = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Real multi-texture Airship renderer. Every layer is derived from the locked official exterior
/// sprite at build time, so the art stays canonical while runtime gains independent depth planes.
/// </summary>
internal static class AirshipLayeredRenderer
{
    private const string ShadowPath = "assets/airship_layer_shadow.png";
    private const string BalloonPath = "assets/airship_layer_balloon.png";
    private const string HullPath = "assets/airship_layer_hull.png";
    private const string RiggingPath = "assets/airship_layer_rigging.png";
    private const string GlowPath = "assets/airship_layer_glow.png";

    private static Texture2D? Shadow;
    private static Texture2D? Balloon;
    private static Texture2D? Hull;
    private static Texture2D? Rigging;
    private static Texture2D? Glow;
    private static bool LoadFailed;
    private static bool LoggedLoaded;

    public static bool HasLayerAssets()
        => EnsureLoaded();

    public static bool TryDraw(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        if (targetWidth <= 0f || !EnsureLoaded() || Balloon is null || Hull is null || Shadow is null || Rigging is null || Glow is null)
            return false;

        float scale = targetWidth / Balloon.Width;
        Vector2 origin = new(Balloon.Width / 2f, Balloon.Height / 2f);
        Vector2 drawScale = new(scale, scale * Math.Max(0.01f, verticalScale));
        float phase = (float)(Environment.TickCount64 / 1000.0);
        float breathe = MathF.Sin(phase * 1.35f) * 1.15f * scale;

        Vector2 shadowOffset = TransformOffset(new Vector2(0f, 8.0f * scale), rotation, verticalScale, effects);
        Vector2 balloonOffset = TransformOffset(new Vector2(0f, -breathe), rotation, verticalScale, effects);
        Vector2 hullOffset = TransformOffset(new Vector2(0f, breathe * 0.45f), rotation, verticalScale, effects);
        Vector2 rigOffset = TransformOffset(new Vector2(0f, breathe * 0.18f), rotation, verticalScale, effects);

        batch.Draw(
            Shadow,
            center + shadowOffset,
            null,
            Color.White * 0.82f,
            rotation,
            origin,
            new Vector2(drawScale.X * 1.018f, drawScale.Y * 1.012f),
            effects,
            1f
        );

        batch.Draw(Balloon, center + balloonOffset, null, tint * 0.99f, rotation, origin, drawScale, effects, 1f);
        batch.Draw(Hull, center + hullOffset, null, tint, rotation, origin, drawScale, effects, 1f);
        batch.Draw(Rigging, center + rigOffset, null, tint * 0.94f, rotation, origin, drawScale, effects, 1f);

        float glowPulse = 0.58f + 0.18f * MathF.Sin(phase * 2.2f);
        batch.Draw(
            Glow,
            center + hullOffset,
            null,
            tint * glowPulse,
            rotation,
            origin,
            drawScale * (1f + 0.003f * MathF.Sin(phase * 1.8f)),
            effects,
            1f
        );
        return true;
    }

    private static bool EnsureLoaded()
    {
        if (Balloon is not null && Hull is not null && Shadow is not null && Rigging is not null && Glow is not null)
            return true;
        if (LoadFailed || ModEntry.StaticHelper is null)
            return false;

        try
        {
            Shadow = ModEntry.StaticHelper.ModContent.Load<Texture2D>(ShadowPath);
            Balloon = ModEntry.StaticHelper.ModContent.Load<Texture2D>(BalloonPath);
            Hull = ModEntry.StaticHelper.ModContent.Load<Texture2D>(HullPath);
            Rigging = ModEntry.StaticHelper.ModContent.Load<Texture2D>(RiggingPath);
            Glow = ModEntry.StaticHelper.ModContent.Load<Texture2D>(GlowPath);
            if (!LoggedLoaded)
            {
                LoggedLoaded = true;
                ModEntry.StaticMonitor?.Log(
                    "Airship layered assets loaded: shadow + balloon + hull + rigging + glow.",
                    LogLevel.Info
                );
            }
            return true;
        }
        catch (Exception ex)
        {
            LoadFailed = true;
            ModEntry.StaticMonitor?.Log(
                $"Airship layered assets unavailable; falling back to locked single sprite. {ex.GetType().Name}: {ex.Message}",
                LogLevel.Warn
            );
            return false;
        }
    }

    private static Vector2 TransformOffset(Vector2 offset, float rotation, float verticalScale, SpriteEffects effects)
    {
        if ((effects & SpriteEffects.FlipHorizontally) != SpriteEffects.None)
            offset.X = -offset.X;
        offset.Y *= Math.Max(0.01f, verticalScale);
        float cos = MathF.Cos(rotation);
        float sin = MathF.Sin(rotation);
        return new Vector2(offset.X * cos - offset.Y * sin, offset.X * sin + offset.Y * cos);
    }
}
'''
(SRC / "Services" / "AirshipLayeredRenderer.cs").write_text(renderer, encoding="utf-8")

# Make the actual Airship foundation use the layered renderer first. Locked single-sprite drawing stays
# as an automatic fallback if any derived layer fails to load.
service_path = SRC / "Services" / "AirshipFoundationService.cs"
service = service_path.read_text(encoding="utf-8")
needle = '''    private bool TryDrawAirshipSprite(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        Texture2D? sprite = this.GetAirshipVisual();'''
replacement = '''    private bool TryDrawAirshipSprite(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        if (AirshipLayeredRenderer.TryDraw(batch, center, targetWidth, tint, effects, rotation, verticalScale))
            return true;

        Texture2D? sprite = this.GetAirshipVisual();'''
if needle not in service:
    if "AirshipLayeredRenderer.TryDraw(batch, center, targetWidth" not in service:
        raise SystemExit("Couldn't locate TryDrawAirshipSprite overload for layered renderer injection.")
else:
    service = service.replace(needle, replacement, 1)
service_path.write_text(service, encoding="utf-8")

# The .5.4 runtime-only sprite shadow/rigging hook should stand down when real layer assets exist.
depth_path = SRC / "Patches" / "AirshipVisualDepthPatch.cs"
depth = depth_path.read_text(encoding="utf-8")
if "if (AirshipLayeredRenderer.HasLayerAssets())\n            return;" not in depth:
    depth = depth.replace(
        '''    {
        Texture2D? sprite = GetAirshipTexture();
        if (sprite is null || targetWidth <= 0f)
            return;''',
        '''    {
        if (AirshipLayeredRenderer.HasLayerAssets())
            return;

        Texture2D? sprite = GetAirshipTexture();
        if (sprite is null || targetWidth <= 0f)
            return;''',
        1
    )
    marker = '''    {
        Texture2D? sprite = GetAirshipTexture();
        if (!__result || sprite is null || targetWidth <= 0f)
            return;'''
    replacement2 = '''    {
        if (AirshipLayeredRenderer.HasLayerAssets())
            return;

        Texture2D? sprite = GetAirshipTexture();
        if (!__result || sprite is null || targetWidth <= 0f)
            return;'''
    if marker not in depth:
        raise SystemExit("Couldn't locate AfterAirshipSprite fallback hook.")
    depth = depth.replace(marker, replacement2, 1)
depth_path.write_text(depth, encoding="utf-8")

# Version metadata.
manifest_path = SRC / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

csproj_path = SRC / "Cardcha.csproj"
csproj = csproj_path.read_text(encoding="utf-8")
csproj = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", csproj, count=1)
csproj_path.write_text(csproj, encoding="utf-8")

(SRC / "Directory.Build.targets").write_text(f'''<Project>
  <PropertyGroup>
    <Version>{VERSION}</Version>
  </PropertyGroup>

  <!-- .4.14.4.5.5 Real Layered Airship Assets: generated planes from locked official sprite. -->
  <Target Name="CardchaAlpha280414455Manifest" BeforeTargets="BeforeBuild">
    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />
  </Target>
</Project>
''', encoding="utf-8")

mod_path = SRC / "ModEntry.cs"
mod = mod_path.read_text(encoding="utf-8")
mod = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.\d+[^\"]*TEST with',
    f'Cardcha! {VERSION} REAL LAYERED AIRSHIP ASSETS TEST with',
    mod,
    count=1,
)
mod_path.write_text(mod, encoding="utf-8")

marker = ROOT / "tools" / "airship_layered_assets_marker.txt"
if marker.exists():
    marker.unlink()

print(f"Prepared {VERSION} real Airship layers")
for name in layers:
    path = ASSETS / name
    print(name, hashlib.sha256(path.read_bytes()).hexdigest())
