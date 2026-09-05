from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing patch anchor: {label}")
    return text.replace(old, new, 1)


# Version bump.
for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets"]:
    p = CARDCHA / rel
    s = read(p)
    if NEW_VERSION not in s:
        if OLD_VERSION not in s:
            raise RuntimeError(f"version anchor missing in {rel}")
        s = s.replace(OLD_VERSION, NEW_VERSION)
        write(p, s)

# One canonical on-disk MiMi portrait source.
for obsolete in [
    CARDCHA / "assets" / "mimi_portraits_runtime64.png",
    CARDCHA / "assets" / "mimi_npc_portraits.png",
]:
    if obsolete.exists():
        obsolete.unlink()

# Stardew's vanilla DialogueBox still expects 64x64 portrait frames. Cardcha derives that
# compatibility sheet in memory from the 128px master with nearest-neighbour sampling, so hard
# pixel edges stay sharp and assets/mimi_portraits.png remains the only on-disk portrait source.
nearest_method = r'''    private static Texture2D CreateRuntimePortraitSheet(Texture2D master)
    {
        const int frameCount = 6;
        const int targetSize = 64;
        if (master.Width % frameCount != 0)
            throw new InvalidOperationException($"MiMi master portrait width {master.Width} is not divisible by {frameCount}.");

        int sourceFrameWidth = master.Width / frameCount;
        int sourceFrameHeight = master.Height;
        Color[] source = new Color[master.Width * master.Height];
        master.GetData(source);
        Color[] output = new Color[frameCount * targetSize * targetSize];

        // Preserve hard pixel edges. Do NOT average multiple master pixels into one output pixel.
        // This is a vanilla-dialogue compatibility texture generated in memory only.
        for (int frame = 0; frame < frameCount; frame++)
        {
            int frameX = frame * sourceFrameWidth;
            for (int ty = 0; ty < targetSize; ty++)
            {
                int sy = Math.Min(sourceFrameHeight - 1, ty * sourceFrameHeight / targetSize);
                for (int tx = 0; tx < targetSize; tx++)
                {
                    int sx = Math.Min(sourceFrameWidth - 1, tx * sourceFrameWidth / targetSize);
                    output[ty * (frameCount * targetSize) + frame * targetSize + tx]
                        = source[sy * master.Width + frameX + sx];
                }
            }
        }

        Texture2D runtime = new Texture2D(Game1.graphics.GraphicsDevice, frameCount * targetSize, targetSize);
        runtime.SetData(output);
        return runtime;
    }
'''

method_pattern = re.compile(
    r"    private static Texture2D CreateRuntimePortraitSheet\(Texture2D master\)\n    \{.*?\n    \}\n\n(?=    private static void AssignPortraitTexture)",
    re.S,
)

# Mystery/Town/Home/Shop portrait pipeline.
mystery_path = CARDCHA / "Services" / "MimiMysteryTownService.cs"
mystery = read(mystery_path)
mystery = mystery.replace(
    '    private const string MimiNativePortraitsPath = "assets/mimi_portraits_runtime64.png";\n',
    '',
)
old_loader = '            e.LoadFromModFile<Texture2D>(MimiNativePortraitsPath, AssetLoadPriority.Medium);'
bad_loader = '            e.LoadFrom<Texture2D>(() => this.GetNativePortraitCompatibilitySheet(), AssetLoadPriority.Medium);'
good_loader = '            e.LoadFrom(() => this.GetNativePortraitCompatibilitySheet(), AssetLoadPriority.Medium);'
if bad_loader in mystery:
    mystery = mystery.replace(bad_loader, good_loader, 1)
elif good_loader not in mystery:
    mystery = replace_once(mystery, old_loader, good_loader, 'MiMi native portrait asset loader')

prepare_anchor = '''    internal void PrepareCrispPortrait(NPC speaker)\n    {\n        this.EnsureTextures();\n        AssignPortraitTexture(speaker, this.RuntimePortraitSheet);\n    }\n\n'''
prepare_insert = prepare_anchor + '''    private Texture2D GetNativePortraitCompatibilitySheet()\n    {\n        this.EnsureTextures();\n        return this.RuntimePortraitSheet\n            ?? throw new InvalidOperationException("MiMi runtime portrait sheet was not initialized from mimi_portraits.png.");\n    }\n\n'''
if 'private Texture2D GetNativePortraitCompatibilitySheet()' not in mystery:
    mystery = replace_once(mystery, prepare_anchor, prepare_insert, 'native portrait compatibility helper')

mystery, count = method_pattern.subn(nearest_method + "\n", mystery, count=1)
if count != 1:
    raise RuntimeError("could not replace MimiMysteryTownService portrait scaler")
write(mystery_path, mystery)

# Story scenes use the exact same master-derived nearest-neighbour sheet.
story_path = CARDCHA / "Services" / "CardchaStoryService.cs"
story = read(story_path)
story, count = method_pattern.subn(nearest_method + "\n", story, count=1)
if count != 1:
    raise RuntimeError("could not replace CardchaStoryService portrait scaler")
write(story_path, story)

# Make MiMi's home movement use unquestionably open floor anchors, not the old upper-wall/window row.
home_path = CARDCHA / "Services" / "MimiHomeService.cs"
home = read(home_path)
replacements = {
    '    private static readonly Point DefaultHomeTile = new(10, 4);':
        '    private static readonly Point DefaultHomeTile = new(10, 6);',
    '    private static readonly Point SecretTvWatchTile = new(5, 10);':
        '    private static readonly Point SecretTvWatchTile = new(5, 9);',
    '    private static readonly Point[] HomeIdleTiles = { new(10, 4), new(9, 5), new(11, 5), new(10, 6) };':
        '    private static readonly Point[] HomeIdleTiles = { new(10, 6), new(9, 7), new(10, 7), new(11, 7), new(10, 8) };',
    '    private static readonly Point[] TvIdleTiles = { new(5, 10), new(4, 10), new(6, 10), new(5, 9) };':
        '    private static readonly Point[] TvIdleTiles = { new(5, 9), new(6, 9), new(6, 10), new(7, 9) };',
    '    private static readonly Point[] LateIdleTiles = { new(13, 7), new(13, 6), new(14, 7), new(12, 7) };':
        '    private static readonly Point[] LateIdleTiles = { new(13, 7), new(14, 7), new(13, 8), new(14, 8) };',
}
for old, new in replacements.items():
    if new not in home:
        home = replace_once(home, old, new, old)

# Never snap MiMi onto a blocked decorative tile if a future visual pass changes furniture.
anchor_block = '''        Point anchor = state switch\n        {\n            "tv" => SecretTvWatchTile,\n            "late" => SecretLateHomeTile,\n            _ => DefaultHomeTile\n        };\n        int anchorFacing = state == "tv" ? 0 : state == "late" ? 1 : 2;\n'''
anchor_replacement = '''        Point anchor = state switch\n        {\n            "tv" => SecretTvWatchTile,\n            "late" => SecretLateHomeTile,\n            _ => DefaultHomeTile\n        };\n        if (!IsTileClear(attic, anchor))\n            anchor = FindClearTileNear(attic, anchor);\n        int anchorFacing = state == "tv" ? 0 : state == "late" ? 1 : 2;\n'''
if 'if (!IsTileClear(attic, anchor))' not in home:
    home = replace_once(home, anchor_block, anchor_replacement, 'safe home routine anchor')

old_fallback = '        return pool[0];\n    }\n\n    private void ResetHomeWanderRuntime()'
new_fallback = '        return FindClearTileNear(attic, pool[0]);\n    }\n\n    private void ResetHomeWanderRuntime()'
if new_fallback not in home:
    home = replace_once(home, old_fallback, new_fallback, 'home wander fallback')

# Add useful live diagnostics to cardcha_story_status / Home.Describe without touching save data.
old_describe = '        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00 | DebugRoutine={this.DebugRoutineOverride ?? "auto"} | Actor={actorTile}";'
new_describe = '        Point wanderTile = new((int)(this.HomeWanderTarget.X / 64f), (int)(this.HomeWanderTarget.Y / 64f));\n        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00 | DebugRoutine={this.DebugRoutineOverride ?? "auto"} | RoutineState={this.ActiveHomeRoutineState ?? "<none>"} | WanderTarget={wanderTile.X},{wanderTile.Y} | Actor={actorTile}";'
if 'RoutineState=' not in home:
    home = replace_once(home, old_describe, new_describe, 'home routine diagnostics')

write(home_path, home)

print(f"Prepared Cardcha {NEW_VERSION}: one MiMi portrait source + crisp nearest-neighbour runtime + safer home wander.")
