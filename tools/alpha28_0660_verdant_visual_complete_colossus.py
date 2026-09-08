from pathlib import Path
import json, math, colorsys
from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path('src/Cardcha')
ASSET = ROOT / 'assets/bosses/verdant_guardian'
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.26'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.27'
FRAME = 64

# ---------------- version ----------------
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
if data['Version'] != BASE_VERSION:
    raise RuntimeError(f'Expected base {BASE_VERSION}, got {data["Version"]}')
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if BASE_VERSION not in text:
        raise RuntimeError(f'{BASE_VERSION} missing from {rel}')
    p.write_text(text.replace(BASE_VERSION, VERSION), encoding='utf-8')

ASSET.mkdir(parents=True, exist_ok=True)

# ---------------- art helpers ----------------
def split_sheet(path, count):
    img = Image.open(path).convert('RGBA')
    if img.height < FRAME or img.width < FRAME * count:
        raise RuntimeError(f'{path} unexpected size {img.size}, need {FRAME*count}x{FRAME}')
    return [img.crop((i*FRAME, 0, (i+1)*FRAME, FRAME)) for i in range(count)]

def save_sheet(path, frames):
    sheet = Image.new('RGBA', (FRAME * len(frames), FRAME), (0,0,0,0))
    for i, fr in enumerate(frames):
        sheet.alpha_composite(fr, (i*FRAME, 0))
    sheet.save(path, optimize=True)

def mature_palette(img):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r,g,b,a = px[x,y]
            if a == 0:
                continue
            h,s,v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            # Darker bark/moss, less toy-like saturation, stronger ancient contrast.
            s = min(1.0, s * 0.92)
            v = max(0.0, min(1.0, (v - 0.05) * 0.94 + 0.03))
            rr,gg,bb = colorsys.hsv_to_rgb(h,s,v)
            # Pull bright greens toward moss and keep the core as the brightest visual element.
            if g > r * 1.08 and g > b * 1.08 and v > 0.25:
                rr *= 0.92; gg *= 0.92; bb *= 0.86
            px[x,y] = (int(rr*255), int(gg*255), int(bb*255), a)
    return ImageEnhance.Contrast(img).enhance(1.08)

def colossus_frame(frame):
    src = mature_palette(frame.copy())
    alpha = src.getchannel('A')
    bbox = alpha.getbbox()
    if not bbox:
        return src
    crop = src.crop(bbox)
    # Broader shoulders/body and slightly taller, while staying inside the 64px source frame.
    nw = min(62, max(crop.width, int(round(crop.width * 1.14))))
    nh = min(62, max(crop.height, int(round(crop.height * 1.03))))
    crop = crop.resize((nw, nh), Image.Resampling.NEAREST)
    out = Image.new('RGBA', (FRAME, FRAME), (0,0,0,0))
    x = (FRAME - nw)//2
    y = max(1, 62 - nh)
    out.alpha_composite(crop, (x,y))
    return out

def transform(fr, angle=0, dx=0, dy=0, tint=None, alpha=1.0, brightness=1.0):
    out = fr.copy()
    if tint is not None:
        tr,tg,tb,amount = tint
        p = out.load()
        for y in range(FRAME):
            for x in range(FRAME):
                r,g,b,a = p[x,y]
                if a:
                    p[x,y] = (int(r*(1-amount)+tr*amount), int(g*(1-amount)+tg*amount), int(b*(1-amount)+tb*amount), a)
    if brightness != 1.0:
        out = ImageEnhance.Brightness(out).enhance(brightness)
    if angle:
        out = out.rotate(angle, resample=Image.Resampling.NEAREST, center=(32,58), expand=False)
    if dx or dy:
        shifted = Image.new('RGBA', (FRAME,FRAME), (0,0,0,0))
        shifted.alpha_composite(out, (dx,dy))
        out = shifted
    if alpha < 1:
        aa = out.getchannel('A').point(lambda v: int(v*alpha))
        out.putalpha(aa)
    return out

# Mature the four authored body sheets in-place. Their animation identities remain intact.
authored = {
    'boss1_verdant_guardian_idle.png': 6,
    'boss1_verdant_guardian_intro_awaken.png': 10,
    'boss1_verdant_guardian_swipe_attack.png': 9,
    'boss1_verdant_guardian_root_cast.png': 8,
}
for name,count in authored.items():
    frames = [colossus_frame(f) for f in split_sheet(ASSET/name, count)]
    save_sheet(ASSET/name, frames)

idle = split_sheet(ASSET/'boss1_verdant_guardian_idle.png', 6)
root = split_sheet(ASSET/'boss1_verdant_guardian_root_cast.png', 8)
swipe = split_sheet(ASSET/'boss1_verdant_guardian_swipe_attack.png', 9)

# ---------------- missing animation sheets ----------------
summon = []
for i in range(10):
    base = root[min(7, int(i * 8 / 10))]
    lift = -min(3, i//3) if i < 7 else -(9-i)
    summon.append(transform(base, dy=lift, tint=(118,150,72,0.10), brightness=0.98 + 0.025*i))
save_sheet(ASSET/'boss1_verdant_guardian_summon_cast.png', summon)

prep_angles = [0,-1,-2,-3,-4,-5,-6]
charge_prep = [transform(idle[i%6], angle=a, dx=min(3,i//2), dy=min(2,i//3)) for i,a in enumerate(prep_angles)]
save_sheet(ASSET/'boss1_verdant_guardian_charge_prep.png', charge_prep)
charge_loop = [transform(idle[i+1], angle=-6, dx=4+i, dy=2) for i in range(3)]
save_sheet(ASSET/'boss1_verdant_guardian_charge_loop.png', charge_loop)
charge_end = [transform(idle[(3-i)%6], angle=a, dx=max(0,3-i), dy=max(0,2-i//2)) for i,a in enumerate([-5,-3,-1,0])]
save_sheet(ASSET/'boss1_verdant_guardian_charge_end.png', charge_end)

vine = [transform(root[i], tint=(65,122,55,0.18)) for i in range(8)]
save_sheet(ASSET/'boss1_verdant_guardian_vine_cast.png', vine)

slam = []
for i in range(11):
    if i < 5:
        slam.append(transform(swipe[min(8,i)], dy=-min(2,i//2)))
    elif i < 8:
        slam.append(transform(root[min(7, i-1)], dy=2 + (i-5)*2, brightness=1.03))
    else:
        slam.append(transform(idle[(i-8)%6], dy=max(0, 3-(i-8))))
save_sheet(ASSET/'boss1_verdant_guardian_slam_attack.png', slam)

phase = []
for i in range(12):
    pulse = 1.0 + 0.14*math.sin(i/11*math.pi)
    fr = transform(idle[i%6], brightness=pulse, tint=(130,185,78,0.08 + 0.08*(i/11)))
    d = ImageDraw.Draw(fr)
    rad = 8 + i//2
    d.ellipse((32-rad,31-rad,32+rad,31+rad), outline=(150,255,105,max(30,140-i*6)), width=1)
    phase.append(fr)
save_sheet(ASSET/'boss1_verdant_guardian_phase_shift.png', phase)

hurt = [transform(idle[0], dx=dx, tint=(120,70,50,0.22), brightness=0.92) for dx in (-2,2,0)]
save_sheet(ASSET/'boss1_verdant_guardian_hurt.png', hurt)

defeat=[]
for i in range(12):
    progress=i/11
    angle=progress*15
    dy=int(progress*12)
    dx=int(progress*4)
    alpha=1.0 if i<8 else max(0.18,1-(i-7)*0.18)
    defeat.append(transform(idle[0], angle=angle, dx=dx, dy=dy, tint=(70,72,52,0.10+0.18*progress), alpha=alpha, brightness=1-0.32*progress))
save_sheet(ASSET/'boss1_verdant_guardian_defeat.png', defeat)

# ---------------- FX sheets ----------------
def fx_sheet(name, count, draw_fn):
    frames=[]
    for i in range(count):
        im=Image.new('RGBA',(FRAME,FRAME),(0,0,0,0))
        draw_fn(ImageDraw.Draw(im), i, count)
        frames.append(im)
    save_sheet(ASSET/name, frames)

def root_warning(d,i,n):
    p=(i+1)/n; r=8+int(12*p); a=90+int(80*p)
    d.ellipse((32-r,32-r//2,32+r,32+r//2), outline=(95,210,92,a), width=2)
    d.line((32-r,32,32+r,32), fill=(75,150,65,a), width=1)
    d.line((32,32-r//2,32,32+r//2), fill=(75,150,65,a), width=1)
fx_sheet('fx_boss1_root_warning.png',4,root_warning)

def root_erupt(d,i,n):
    h=8+i*8; base=52
    for x in (22,32,42):
        lean=(x-32)//5
        d.polygon([(x-3,base),(x+3,base),(x+lean+2,base-h),(x+lean,base-h-7),(x+lean-2,base-h)], fill=(86,70,42,220))
        d.line((x+lean,base-h+2,x+lean,base-h-6), fill=(114,170,71,210), width=2)
fx_sheet('fx_boss1_root_erupt.png',5,root_erupt)

def vine_trap(d,i,n):
    r=10+i*3; a=130+15*i
    d.ellipse((32-r,32-r//2,32+r,32+r//2), outline=(64,145,62,min(230,a)), width=3)
    for k in range(4):
        ang=k*math.pi/2+i*.25
        x=int(32+math.cos(ang)*r); y=int(32+math.sin(ang)*r/2)
        d.ellipse((x-2,y-2,x+2,y+2),fill=(105,190,76,210))
fx_sheet('fx_boss1_vine_trap.png',6,vine_trap)

def slam_warning(d,i,n):
    r=12+i*7
    d.ellipse((32-r,32-r,32+r,32+r), outline=(195,222,92,100+25*i), width=2)
fx_sheet('fx_boss1_slam_warning.png',4,slam_warning)

def shockwave(d,i,n):
    r=8+i*10
    d.ellipse((32-r,32-r,32+r,32+r), outline=(180,225,110,max(50,230-i*35)), width=3)
fx_sheet('fx_boss1_slam_shockwave.png',5,shockwave)

def leaf_burst(d,i,n):
    for k in range(8):
        ang=k*math.pi/4 + i*.08
        r=6+i*5
        x=int(32+math.cos(ang)*r); y=int(32+math.sin(ang)*r)
        d.rectangle((x-2,y-1,x+2,y+1),fill=(95+10*(k%2),168+8*(k%3),72,220-i*18))
fx_sheet('fx_boss1_leaf_burst.png',6,leaf_burst)

def phase_pulse(d,i,n):
    r=9+i*8
    d.ellipse((32-r,32-r,32+r,32+r), outline=(145,245,105,max(40,220-i*28)), width=2)
fx_sheet('fx_boss1_phase_pulse.png',6,phase_pulse)

def core_release(d,i,n):
    y=39-i*4; r=4+i//2
    d.ellipse((32-r*2,y-r*2,32+r*2,y+r*2),fill=(110,240,95,45))
    d.ellipse((32-r,y-r,32+r,y+r),fill=(185,255,132,245))
fx_sheet('fx_boss1_core_release.png',6,core_release)

# ---------------- C# visual service ----------------
visual = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// 0660 visual-complete + Colossus pass. Combat timing remains authoritative in
/// VerdantGuardianBossService; this layer only maps state/elapsed time to Cardcha art and FX.
/// </summary>
internal sealed class VerdantGuardianVisualService
{
    private const int FrameSize = 64;
    private const float DrawScale = 8f; // user-approved x2 visual size from the 0652 4x prototype
    private const float FxScale = 3.25f;
    private static readonly Vector2 FrameOrigin = new(32f, 58f);
    private const string AssetRoot = "assets/bosses/verdant_guardian";

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly VerdantGuardianBossService Boss;
    private readonly Dictionary<string, Texture2D?> Textures = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> Failed = new(StringComparer.OrdinalIgnoreCase);
    private VerdantGuardianState LastState = VerdantGuardianState.Dormant;
    private int LastHealth = -1;
    private long HurtUntilMs;
    private long ChargeEndUntilMs;

    private sealed record Clip(string Key, string File, int Frames, int DurationMs, bool Loop);

    private static readonly Dictionary<string, Clip> Clips = new(StringComparer.OrdinalIgnoreCase)
    {
        ["idle"] = new("idle", "boss1_verdant_guardian_idle.png", 6, 1200, true),
        ["intro"] = new("intro", "boss1_verdant_guardian_intro_awaken.png", 10, 1500, false),
        ["swipe"] = new("swipe", "boss1_verdant_guardian_swipe_attack.png", 9, 700, false),
        ["root"] = new("root", "boss1_verdant_guardian_root_cast.png", 8, 900, false),
        ["summon"] = new("summon", "boss1_verdant_guardian_summon_cast.png", 10, 600, false),
        ["charge_prep"] = new("charge_prep", "boss1_verdant_guardian_charge_prep.png", 7, 900, false),
        ["charge_loop"] = new("charge_loop", "boss1_verdant_guardian_charge_loop.png", 3, 360, true),
        ["charge_end"] = new("charge_end", "boss1_verdant_guardian_charge_end.png", 4, 240, false),
        ["vine"] = new("vine", "boss1_verdant_guardian_vine_cast.png", 8, 900, false),
        ["slam"] = new("slam", "boss1_verdant_guardian_slam_attack.png", 11, 1100, false),
        ["phase"] = new("phase", "boss1_verdant_guardian_phase_shift.png", 12, 1600, false),
        ["hurt"] = new("hurt", "boss1_verdant_guardian_hurt.png", 3, 180, false),
        ["defeat"] = new("defeat", "boss1_verdant_guardian_defeat.png", 12, 2200, false),
    };

    public VerdantGuardianVisualService(IModHelper helper, IMonitor monitor, VerdantGuardianBossService boss)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Boss = boss;
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!this.Boss.IsInArena)
            return;

        Monster? actor = this.Boss.VisualBoss;
        if (actor is null)
            return;

        long now = Environment.TickCount64;
        VerdantGuardianState state = this.Boss.VisualState;
        if (this.LastState == VerdantGuardianState.Charging && state == VerdantGuardianState.Decision)
            this.ChargeEndUntilMs = now + 240;
        if (this.LastHealth >= 0 && actor.Health < this.LastHealth && actor.Health > 0 && state == VerdantGuardianState.Decision)
            this.HurtUntilMs = now + 180;
        this.LastHealth = actor.Health;
        this.LastState = state;

        this.DrawCombatFx(e.SpriteBatch, state, now, actor);
        if (state == VerdantGuardianState.Victory)
            return;

        Clip clip = this.ResolveClip(state, now);
        Texture2D? texture = this.Load(clip.File);
        if (texture is null)
            return;

        long elapsed = clip.Key switch
        {
            "hurt" => Math.Max(0L, 180L - (this.HurtUntilMs - now)),
            "charge_end" => Math.Max(0L, 240L - (this.ChargeEndUntilMs - now)),
            _ => Math.Max(0L, now - this.Boss.VisualStateStartedAtMs),
        };
        int frame = ResolveFrame(clip, elapsed);
        Rectangle source = new(frame * FrameSize, 0, FrameSize, FrameSize);
        if (source.Right > texture.Width || source.Bottom > texture.Height)
        {
            this.LogFailureOnce(clip.File, $"sheet dimensions {texture.Width}x{texture.Height} cannot supply frame {frame}/{clip.Frames}");
            return;
        }

        Vector2 feetWorld = actor.Position + new Vector2(32f, 58f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, feetWorld);
        float phaseScale = this.Boss.VisualPhase switch { 1 => 1f, 2 => 1.025f, _ => 1.05f };
        Color tint = this.Boss.VisualPhase switch
        {
            1 => new Color(242, 238, 220),
            2 => new Color(230, 244, 210),
            _ => new Color(224, 248, 198),
        };

        int shadowWidth = 255 + this.Boss.VisualPhase * 18;
        Rectangle shadow = new((int)local.X - shadowWidth/2, (int)local.Y - 22, shadowWidth, 42);
        e.SpriteBatch.Draw(Game1.staminaRect, shadow, Color.Black * 0.32f);

        float layer = Math.Clamp((actor.Position.Y + 128f) / 10000f, 0f, 0.99f);
        e.SpriteBatch.Draw(texture, local, source, tint, 0f, FrameOrigin, DrawScale * phaseScale, SpriteEffects.None, layer);

        if (state != VerdantGuardianState.Defeated)
        {
            Texture2D? glow = this.Load("boss1_verdant_guardian_core_glow.png");
            if (glow is not null && glow.Width >= FrameSize * 6 && glow.Height >= FrameSize)
            {
                int glowFrame = (int)((now / 115L) % 6L);
                Rectangle glowSource = new(glowFrame * FrameSize, 0, FrameSize, FrameSize);
                float glowAlpha = this.Boss.VisualPhase switch { 1 => 0.42f, 2 => 0.68f, _ => 0.94f };
                e.SpriteBatch.Draw(glow, local, glowSource, Color.White * glowAlpha, 0f, FrameOrigin,
                    DrawScale * phaseScale, SpriteEffects.None, Math.Min(0.995f, layer + 0.0005f));
            }
        }

        if (state == VerdantGuardianState.Defeated)
            this.DrawReleasedCore(e.SpriteBatch, now, actor, layer);
    }

    private Clip ResolveClip(VerdantGuardianState state, long now)
    {
        if (state == VerdantGuardianState.Decision && now < this.HurtUntilMs)
            return Clips["hurt"];
        if (state == VerdantGuardianState.Decision && now < this.ChargeEndUntilMs)
            return Clips["charge_end"];
        return state switch
        {
            VerdantGuardianState.Intro => Clips["intro"],
            VerdantGuardianState.SwipeTelegraph => Clips["swipe"],
            VerdantGuardianState.RootSpikesTelegraph => Clips["root"],
            VerdantGuardianState.SummonAdds => Clips["summon"],
            VerdantGuardianState.ChargeTelegraph => Clips["charge_prep"],
            VerdantGuardianState.Charging => Clips["charge_loop"],
            VerdantGuardianState.VineTrapTelegraph => Clips["vine"],
            VerdantGuardianState.VineTrapActive => Clips["vine"],
            VerdantGuardianState.AreaSlamTelegraph => Clips["slam"],
            VerdantGuardianState.PhaseTransition => Clips["phase"],
            VerdantGuardianState.Defeated => Clips["defeat"],
            _ => Clips["idle"],
        };
    }

    private void DrawCombatFx(SpriteBatch batch, VerdantGuardianState state, long now, Monster actor)
    {
        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        switch (state)
        {
            case VerdantGuardianState.RootSpikesTelegraph:
                foreach (Point tile in this.Boss.VisualRootTargets)
                {
                    Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 34f);
                    this.DrawFx(batch, "fx_boss1_root_warning.png", 4, elapsed, 900, center, 1.45f, 0.82f);
                    if (elapsed >= 650)
                        this.DrawFx(batch, "fx_boss1_root_erupt.png", 5, elapsed - 650, 250, center, 1.75f, 0.94f);
                }
                break;
            case VerdantGuardianState.SummonAdds:
                this.DrawFx(batch, "fx_boss1_leaf_burst.png", 6, elapsed, 600, this.Boss.VisualBossCenter, 2.25f, 0.86f);
                break;
            case VerdantGuardianState.VineTrapTelegraph:
            case VerdantGuardianState.VineTrapActive:
                Point vine = this.Boss.VisualVineTarget;
                this.DrawFx(batch, "fx_boss1_vine_trap.png", 6, elapsed, state == VerdantGuardianState.VineTrapActive ? 900 : 900,
                    new Vector2(vine.X * 64f + 32f, vine.Y * 64f + 32f), 2.5f, state == VerdantGuardianState.VineTrapActive ? 0.92f : 0.62f);
                break;
            case VerdantGuardianState.AreaSlamTelegraph:
                this.DrawFx(batch, "fx_boss1_slam_warning.png", 4, elapsed, 900, this.Boss.VisualBossCenter, 4.2f, 0.64f);
                if (elapsed >= 820)
                    this.DrawFx(batch, "fx_boss1_slam_shockwave.png", 5, elapsed - 820, 280, this.Boss.VisualBossCenter, 4.7f, 0.88f);
                break;
            case VerdantGuardianState.PhaseTransition:
                this.DrawFx(batch, "fx_boss1_phase_pulse.png", 6, elapsed, 1600, this.Boss.VisualBossCenter, 4.6f, 0.78f);
                this.DrawFx(batch, "fx_boss1_leaf_burst.png", 6, elapsed, 800, this.Boss.VisualBossCenter, 2.8f, 0.86f);
                break;
        }

        if (this.Boss.VisualPhase >= 2 && state is not VerdantGuardianState.Defeated and not VerdantGuardianState.Victory)
        {
            long aura = now % 1400L;
            float alpha = this.Boss.VisualPhase == 2 ? 0.18f : 0.30f;
            this.DrawFx(batch, "fx_boss1_phase_pulse.png", 6, aura, 1400, this.Boss.VisualBossCenter,
                this.Boss.VisualPhase == 2 ? 3.5f : 4.1f, alpha);
        }
    }

    private void DrawReleasedCore(SpriteBatch batch, long now, Monster actor, float layer)
    {
        Texture2D? fx = this.Load("fx_boss1_core_release.png");
        if (fx is null) return;
        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        int frame = Math.Clamp((int)(elapsed * 6 / 2200), 0, 5);
        Rectangle src = new(frame * FrameSize, 0, FrameSize, FrameSize);
        Vector2 world = actor.Position + new Vector2(32f, 18f - Math.Min(82f, elapsed * 0.035f));
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        batch.Draw(fx, local, src, Color.White, 0f, new Vector2(32,32), 4.2f, SpriteEffects.None, Math.Min(0.999f, layer + 0.001f));
    }

    private void DrawFx(SpriteBatch batch, string file, int frames, long elapsed, int duration, Vector2 worldCenter, float scale, float alpha)
    {
        Texture2D? texture = this.Load(file);
        if (texture is null || texture.Width < frames * FrameSize) return;
        int frame = Math.Clamp((int)((elapsed % Math.Max(1,duration)) * frames / Math.Max(1,duration)), 0, frames-1);
        Rectangle src = new(frame * FrameSize, 0, FrameSize, FrameSize);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, worldCenter);
        batch.Draw(texture, local, src, Color.White * alpha, 0f, new Vector2(32,32), scale, SpriteEffects.None,
            Math.Clamp((worldCenter.Y + 64f) / 10000f, 0f, 0.985f));
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        foreach (Texture2D? texture in this.Textures.Values) texture?.Dispose();
        this.Textures.Clear();
        this.Failed.Clear();
        this.LastState = VerdantGuardianState.Dormant;
        this.LastHealth = -1;
        this.HurtUntilMs = 0;
        this.ChargeEndUntilMs = 0;
    }

    public string Describe()
    {
        Clip clip = this.ResolveClip(this.Boss.VisualState, Environment.TickCount64);
        string loaded = string.Join(",", this.Textures.Where(p => p.Value is not null).Select(p => p.Key));
        return $"State={this.Boss.VisualState} | Clip={clip.Key} | Phase={this.Boss.VisualPhase} | Scale={DrawScale:0.##}x | Colossus=ON | ProxyHidden=ON | Loaded=[{loaded}] | Failed={this.Failed.Count}";
    }

    private Texture2D? Load(string file)
    {
        if (this.Textures.TryGetValue(file, out Texture2D? cached)) return cached;
        if (this.Failed.Contains(file)) return null;
        try
        {
            Texture2D texture = this.Helper.ModContent.Load<Texture2D>($"{AssetRoot}/{file}");
            this.Textures[file] = texture;
            return texture;
        }
        catch (Exception ex)
        {
            this.LogFailureOnce(file, $"{ex.GetType().Name}: {ex.Message}");
            return null;
        }
    }

    private void LogFailureOnce(string file, string reason)
    {
        if (!this.Failed.Add(file)) return;
        this.Textures[file] = null;
        this.Monitor.Log($"Verdant Guardian visual asset '{file}' unavailable. {reason}", LogLevel.Warn);
    }

    private static int ResolveFrame(Clip clip, long elapsedMs)
    {
        if (clip.Frames <= 1) return 0;
        if (clip.Loop)
        {
            long duration = Math.Max(1, clip.DurationMs);
            return Math.Clamp((int)((elapsedMs % duration) * clip.Frames / duration), 0, clip.Frames - 1);
        }
        long clamped = Math.Clamp(elapsedMs, 0L, Math.Max(1, clip.DurationMs) - 1L);
        return Math.Clamp((int)(clamped * clip.Frames / Math.Max(1, clip.DurationMs)), 0, clip.Frames - 1);
    }
}
'''
(ROOT/'Services/VerdantGuardianVisualService.cs').write_text(visual, encoding='utf-8')

# ---------------- proxy draw suppression patch ----------------
proxy_patch = r'''using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>0660: keep the Green Slime as a gameplay proxy but never render it for Boss I.</summary>
internal static class VerdantGuardianProxyDrawPatch
{
    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.Method(typeof(GreenSlime), "draw", new[] { typeof(SpriteBatch) });
        if (target is null)
            throw new MissingMethodException("Could not find GreenSlime.draw(SpriteBatch) for Verdant Guardian proxy suppression.");
        harmony.Patch(target, prefix: new HarmonyMethod(typeof(VerdantGuardianProxyDrawPatch), nameof(Prefix)));
    }

    private static bool Prefix(GreenSlime __instance)
        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey);
}
'''
(ROOT/'Patches/VerdantGuardianProxyDrawPatch.cs').write_text(proxy_patch, encoding='utf-8')

# ---------------- heavy-weight and delayed victory ----------------
boss_path = ROOT/'Services/VerdantGuardianBossService.cs'
boss = boss_path.read_text(encoding='utf-8')
boss = boss.replace('    private const int VictoryReturnDelayMs = 3500;\n', '    private const int VictoryReturnDelayMs = 3500;\n    private const int DefeatSequenceDurationMs = 2200;\n', 1)
boss = boss.replace('    private Vector2 ChargeDirection;\n    private Random EncounterRandom = new(1);\n', '    private Vector2 ChargeDirection;\n    private Vector2 HeavyAnchor;\n    private Random EncounterRandom = new(1);\n', 1)
boss = boss.replace(
'''    internal VerdantGuardianState VisualState => this.State;\n    internal int VisualPhase => this.Phase;\n    internal long VisualStateStartedAtMs => this.StateStartedAtMs;\n    internal Monster? VisualBoss => this.ResolveBoss();\n''',
'''    internal VerdantGuardianState VisualState => this.State;\n    internal int VisualPhase => this.Phase;\n    internal long VisualStateStartedAtMs => this.StateStartedAtMs;\n    internal Monster? VisualBoss => this.ResolveBoss();\n    internal Point[] VisualRootTargets => this.RootTargets;\n    internal Point VisualVineTarget => this.VineTarget;\n    internal Vector2 VisualChargeDirection => this.ChargeDirection;\n    internal Vector2 VisualBossCenter => BossCenter(this.ResolveBoss());\n''', 1)
old_death = '''        Monster? boss = this.ResolveBoss();\n        if (boss is null || boss.Health <= 0)\n        {\n            this.HandleVictory(now);\n            return;\n        }\n\n        if (this.State != VerdantGuardianState.PhaseTransition)\n'''
new_death = '''        Monster? boss = this.ResolveBoss();\n        if (boss is null || boss.Health <= 0)\n        {\n            if (this.State != VerdantGuardianState.Defeated)\n                this.BeginDefeat(now);\n            else if (now - this.StateStartedAtMs >= DefeatSequenceDurationMs)\n                this.CompleteVictory(now);\n            return;\n        }\n\n        // Colossus weight: normal attacks cannot shove the boss around. Only Cardcha-owned\n        // movement (Charge or phase recenter) changes HeavyAnchor.\n        if (this.State != VerdantGuardianState.Charging && this.State != VerdantGuardianState.PhaseTransition)\n            boss.Position = this.HeavyAnchor;\n\n        if (this.State != VerdantGuardianState.PhaseTransition)\n'''
if old_death not in boss: raise RuntimeError('boss death block not found')
boss = boss.replace(old_death, new_death, 1)
boss = boss.replace('                boss.Position = BossSpawnPosition();\n', '                boss.Position = BossSpawnPosition();\n                this.HeavyAnchor = boss.Position;\n', 1)
boss = boss.replace('        this.BossProxy = proxy;\n        this.Phase = 1;\n', '        this.BossProxy = proxy;\n        this.HeavyAnchor = proxy.Position;\n        this.Phase = 1;\n', 1)
boss = boss.replace('        boss.Position = next;\n', '        boss.Position = next;\n        this.HeavyAnchor = next;\n', 1)
old_victory = '''    private void HandleVictory(long now)\n    {\n        if (this.VictoryHandled) return;\n        this.VictoryHandled = true;\n        this.State = VerdantGuardianState.Defeated;\n        this.StateStartedAtMs = now;\n        this.RemoveAdds();\n        bool firstClear = !this.Save.Data.Region1BossDefeated;\n        if (firstClear)\n        {\n            this.Save.Data.Region1BossDefeated = true;\n            this.Save.Data.BossCardsUnlocked ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n            this.Save.Data.BossCardsUnlocked.Add(BossCardId);\n            if (string.IsNullOrWhiteSpace(this.Save.Data.EquippedBossCardId)) this.Save.Data.EquippedBossCardId = BossCardId;\n            this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(2, this.Save.Data.AirshipHighestRegionUnlocked);\n            bool portableGranted = this.PortableMachine.GrantRegion1BossReward();\n            this.Save.Save();\n            Game1.playSound("yoba");\n            Game1.showGlobalMessage(ModEntry.T("boss.verdant.victory.first", new { card = ModEntry.T("boss.verdant.card.name"), portable = portableGranted ? ModEntry.T("boss.verdant.reward.portable") : "" }));\n        }\n        else\n        {\n            Game1.playSound("questcomplete");\n            Game1.showGlobalMessage(ModEntry.T("boss.verdant.victory.rematch"));\n        }\n        this.State = VerdantGuardianState.Victory;\n        this.VictoryReturnAtMs = now + VictoryReturnDelayMs;\n        this.Monitor.Log($"Verdant Guardian defeated. firstClear={firstClear}, bossCard={BossCardId}, regionUnlock={this.Save.Data.AirshipHighestRegionUnlocked}.", LogLevel.Info);\n    }\n'''
new_victory = '''    private void BeginDefeat(long now)\n    {\n        if (this.State == VerdantGuardianState.Defeated || this.State == VerdantGuardianState.Victory) return;\n        this.State = VerdantGuardianState.Defeated;\n        this.StateStartedAtMs = now;\n        this.RemoveAdds();\n        Game1.playSound("thudStep");\n    }\n\n    private void CompleteVictory(long now)\n    {\n        if (this.VictoryHandled) return;\n        this.VictoryHandled = true;\n        bool firstClear = !this.Save.Data.Region1BossDefeated;\n        if (firstClear)\n        {\n            this.Save.Data.Region1BossDefeated = true;\n            this.Save.Data.BossCardsUnlocked ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n            this.Save.Data.BossCardsUnlocked.Add(BossCardId);\n            if (string.IsNullOrWhiteSpace(this.Save.Data.EquippedBossCardId)) this.Save.Data.EquippedBossCardId = BossCardId;\n            this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(2, this.Save.Data.AirshipHighestRegionUnlocked);\n            bool portableGranted = this.PortableMachine.GrantRegion1BossReward();\n            this.Save.Save();\n            Game1.playSound("yoba");\n            Game1.showGlobalMessage(ModEntry.T("boss.verdant.victory.first", new { card = ModEntry.T("boss.verdant.card.name"), portable = portableGranted ? ModEntry.T("boss.verdant.reward.portable") : "" }));\n        }\n        else\n        {\n            Game1.playSound("questcomplete");\n            Game1.showGlobalMessage(ModEntry.T("boss.verdant.victory.rematch"));\n        }\n        this.State = VerdantGuardianState.Victory;\n        this.VictoryReturnAtMs = now + VictoryReturnDelayMs;\n        this.Monitor.Log($"Verdant Guardian defeat sequence complete. firstClear={firstClear}, bossCard={BossCardId}, regionUnlock={this.Save.Data.AirshipHighestRegionUnlocked}.", LogLevel.Info);\n    }\n'''
if old_victory not in boss: raise RuntimeError('old HandleVictory not found')
boss = boss.replace(old_victory, new_victory, 1)
boss = boss.replace('        this.ChargeDirection = Vector2.Zero;\n        this.CooldownUntil.Clear();\n', '        this.ChargeDirection = Vector2.Zero;\n        this.HeavyAnchor = Vector2.Zero;\n        this.CooldownUntil.Clear();\n', 1)
boss_path.write_text(boss, encoding='utf-8')

# ---------------- zero knockback trajectory ----------------
damage_path = ROOT/'Patches/MonsterDamagePatch.cs'
damage = damage_path.read_text(encoding='utf-8')
needle = '''            TestArena?.TryOverrideOutgoingDamage(__instance, ref damage, isBomb, who);\n\n            if (Combat is not null)\n'''
replacement = '''            TestArena?.TryOverrideOutgoingDamage(__instance, ref damage, isBomb, who);\n\n            // Boss I Colossus pass: weapon/team trajectories do not launch the Guardian.\n            if (__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey))\n            {\n                xTrajectory = 0;\n                yTrajectory = 0;\n            }\n\n            if (Combat is not null)\n'''
if needle not in damage: raise RuntimeError('MonsterDamagePatch insertion point missing')
damage = damage.replace(needle, replacement, 1)
damage_path.write_text(damage, encoding='utf-8')

# ---------------- register draw suppression and update log ----------------
mod_path = ROOT/'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
needle = '        MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths, this.CardArena);\n'
if needle not in mod: raise RuntimeError('ModEntry damage patch registration missing')
mod = mod.replace(needle, needle + '        VerdantGuardianProxyDrawPatch.Apply(harmony);\n', 1)
# Replace whichever materialized 0659 still inherited as its startup label.
import re
mod = re.sub(r'Cardcha! 0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.\d+[^"\\n]*',
             'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.27 VERDANT GUARDIAN VISUAL COMPLETE + COLOSSUS TEST', mod, count=1)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- handoff ----------------
handoff = Path('handoff/ALPHA28_0660_VERDANT_VISUAL_COMPLETE_COLOSSUS.md')
handoff.write_text('''# Alpha28 0660 - Verdant Guardian Visual Complete + Colossus Pass\n\nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.27`\nBranch: `cardcha-alpha28-0660-verdant-visual-complete-colossus`\nStatus: implementation candidate, in-game acceptance pending.\n\n## Scope\n- Green Slime gameplay proxy is suppressed at draw time but remains HP/hitbox authority.\n- Verdant Guardian display scale is 8x, exactly 2x the prior 4x prototype scale.\n- Existing authored idle/intro/swipe/root sheets receive a darker, broader Colossus art-direction pass.\n- Added summon, charge prep/loop/end, vine, slam, phase shift, hurt and defeat sheets.\n- Added root warning/erupt, vine trap, slam warning/shockwave, leaf burst, phase pulse and core-release FX.\n- Phase 2/3 receive progressively stronger glow/aura presentation.\n- Death now has a 2.2s visual sequence before first-clear/rematch rewards fire.\n- Boss knockback trajectory is zeroed and HeavyAnchor rejects external shove/pin movement; Cardcha-owned Charge movement remains authoritative.\n\n## Locked systems preserved\nSave schema 19, 20/40/60/80 milestones, 76/76 card audit, Boss Form 10 sec, Boss Energy 1/3, Forest gate, Airship routes/upgrades, MiMi profile/stair 0659 behavior, controller mapping, Hunt Run 4-of-6, and Region I Boss Gate threshold are unchanged.\n\n## Acceptance pending\nVerify in game: x2 size feels correct, proxy never flashes, boss cannot be team-pushed into walls, all attack states have distinct animation, phase escalation reads clearly, and rewards wait until the defeat/core-release sequence completes.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text('''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0660-verdant-visual-complete-colossus`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.27`\n\nContinue from:\n`handoff/ALPHA28_0660_VERDANT_VISUAL_COMPLETE_COLOSSUS.md`\n\nImportant: in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'drawScale': 8,
    'proxyHidden': True,
    'heavyAnchor': True,
    'defeatSequenceMs': 2200,
    'bodyClips': 13,
    'fxSheets': 7,
}, indent=2))
