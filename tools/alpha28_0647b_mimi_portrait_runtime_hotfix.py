from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.1"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.2"
FORBIDDEN = (
    "mimi_portraits_runtime64.png",
    "mimi_npc_portraits.png",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# Version bump.
for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    p = CARDCHA / rel
    text = read(p)
    if NEW_VERSION not in text:
        if OLD_VERSION not in text:
            raise RuntimeError(f"missing version anchor in {rel}")
        text = text.replace(OLD_VERSION, NEW_VERSION)
        write(p, text)

# 0647A correctly moved the canonical Portrait asset loader into MimiMysteryTownService,
# but WorldActorService still registered an older competing LoadFromModFile handler first.
# Remove that obsolete handler entirely. WorldActorService may still request the logical
# Portraits/Ronvotri.Cardcha_MiMi asset through Game1.content; Mystery owns how it is supplied.
world_path = CARDCHA / "Services" / "WorldActorService.cs"
world = read(world_path)
world = world.replace(
    '    private const string MimiPortraitSheetPath = "assets/mimi_portraits_runtime64.png";\n',
    '',
)
old_loader = '''        if (e.Name.IsEquivalentTo(MimiPortraitAsset))\n        {\n            e.LoadFromModFile<Texture2D>(MimiPortraitSheetPath, AssetLoadPriority.Medium);\n            return;\n        }\n\n'''
world = world.replace(old_loader, '')
write(world_path, world)

# Source-level fail-closed audit. No compiled Cardcha C# may mention either obsolete portrait.
violations = []
for path in CARDCHA.rglob("*.cs"):
    text = read(path)
    for token in FORBIDDEN:
        if token in text:
            violations.append(f"{path.relative_to(ROOT)}: {token}")
if violations:
    raise RuntimeError("obsolete MiMi portrait references remain:\n" + "\n".join(violations))

# Keep exactly one canonical on-disk portrait master.
assets = CARDCHA / "assets"
if not (assets / "mimi_portraits.png").is_file():
    raise RuntimeError("canonical assets/mimi_portraits.png is missing")
for token in FORBIDDEN:
    obsolete = assets / token
    if obsolete.exists():
        obsolete.unlink()

print(f"Prepared Cardcha {NEW_VERSION}: removed competing WorldActor portrait loader; canonical portrait asset is single-owner.")
