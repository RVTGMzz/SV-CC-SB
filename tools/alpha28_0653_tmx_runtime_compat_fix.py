from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.19"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.20"

TARGET_TMX = [
    CARDCHA / "assets/region1_rooms/room_1_verdant_clearing.tmx",
    CARDCHA / "assets/region1_rooms/room_2_moss_creek.tmx",
    CARDCHA / "assets/region1_rooms/room_3_old_ruins.tmx",
    CARDCHA / "assets/region1_rooms/room_4_briar_thicket.tmx",
    CARDCHA / "assets/region1_rooms/room_5_hollow_grove.tmx",
    CARDCHA / "assets/region1_rooms/room_6_card_shrine.tmx",
    CARDCHA / "assets/verdant_guardian_arena.tmx",
]


def set_version() -> None:
    manifest = CARDCHA / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["Version"] = NEW_VERSION
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rel in ["Cardcha.csproj", "Directory.Build.targets"]:
        path = CARDCHA / rel
        text = path.read_text(encoding="utf-8")
        if OLD_VERSION not in text:
            raise RuntimeError(f"0653 version anchor missing in {rel}")
        path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")


def repair_tmx_csv(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r'(<data\s+encoding="csv">\s*)(.*?)(\s*</data>)', re.S)
    repaired = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal repaired
        prefix, body, suffix = match.groups()
        trimmed = body.rstrip()
        trailing_ws = body[len(trimmed):]
        if trimmed.endswith(","):
            trimmed = trimmed[:-1]
            repaired += 1
        return prefix + trimmed + trailing_ws + suffix

    updated = pattern.sub(replace, text)
    path.write_text(updated, encoding="utf-8")
    return repaired


def validate_tmx(path: Path) -> None:
    root = ET.parse(path).getroot()
    for layer in root.findall("layer"):
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "csv":
            continue
        body = data.text or ""
        raw_tokens = body.split(",")
        # Emulate the strict TMXTile decode path that failed in the user's SMAPI log:
        # every comma-delimited token must parse as UInt32, including the final token.
        values = []
        for index, token in enumerate(raw_tokens):
            value = token.strip()
            if not value:
                raise RuntimeError(f"{path}: empty CSV token in layer {layer.attrib.get('name')} at index {index}")
            parsed = int(value)
            if parsed < 0 or parsed > 0xFFFFFFFF:
                raise RuntimeError(f"{path}: UInt32 overflow in layer {layer.attrib.get('name')}: {value}")
            values.append(parsed)

        width = int(layer.attrib["width"])
        height = int(layer.attrib["height"])
        expected = width * height
        if len(values) != expected:
            raise RuntimeError(
                f"{path}: layer {layer.attrib.get('name')} has {len(values)} CSV tiles; expected {expected}"
            )


def write_handoff(repaired_blocks: int) -> None:
    handoff = ROOT / "handoff" / "ALPHA28_0653_TMX_RUNTIME_COMPAT_FIX.md"
    handoff.write_text(
        f"""# Alpha28 0653 - TMX runtime compatibility fix\n\n"
        f"Branch: `cardcha-alpha28-0653-tmx-runtime-compat-fix`\n\n"
        f"Build target: `{NEW_VERSION}`\n\n"
        f"## Why this patch exists\n"
        f"In-game SMAPI testing exposed `TMXTile.TMXData.decode -> UInt32.Parse` failures when loading all six Region I Hunt Run rooms and the Verdant Guardian arena. The generated CSV layers ended with a comma immediately before `</data>`, producing an empty final token. XML/Tiled parsing tolerated the files, but Stardew/SMAPI's TMXTile runtime parser did not.\n\n"
        f"The `.vi` suffix visible in SMAPI asset names is locale resolution and was not the cause.\n\n"
        f"## Fix\n"
        f"- Removed only the final trailing comma from each CSV `<data>` block in the 7 affected TMX maps.\n"
        f"- Repaired CSV blocks: {repaired_blocks}.\n"
        f"- Added a strict regression validator that emulates the failing parser contract: every comma-separated token must be a non-empty UInt32 and each layer must contain exactly width x height tiles.\n"
        f"- No map layout, collision, Hunt Run route logic, Boss I AI, rewards, save schema, card balance, MiMi, Airship, or visual animation timing changed.\n\n"
        f"## Acceptance\n"
        f"CI/static/compile/package acceptance only until a fresh in-game SMAPI test confirms both Hunt Run room loading and `Cardcha_VerdantGuardianArena` loading without ContentLoadException.\n",
        encoding="utf-8",
    )

    latest = ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md"
    latest.write_text(
        f"""# Latest Cardcha handoff\n\n"
        f"Current development branch:\n`cardcha-alpha28-0653-tmx-runtime-compat-fix`\n\n"
        f"Current build target:\n`{NEW_VERSION}`\n\n"
        f"Read first:\n"
        f"- `handoff/ALPHA28_0653_TMX_RUNTIME_COMPAT_FIX.md`\n"
        f"- `handoff/ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md`\n"
        f"- `handoff/VERDANT_GUARDIAN_ANIMATION_HOOK_SPEC.md`\n"
        f"- `handoff/ALPHA28_0650_VERDANT_GUARDIAN_BOSS1.md`\n"
        f"- `handoff/BOSS_CONCEPT_CANON.md`\n\n"
        f"## Current acceptance state\n"
        f"- 0653 repairs the TMX CSV runtime-format bug found by real SMAPI testing; fresh in-game acceptance pending.\n"
        f"- Verdant Guardian gameplay + first custom visual overlay remain implemented; visual acceptance pending.\n"
        f"- Region I Hunt Run remains exactly 4 unique rooms selected from a pool of 6 before the 20-card Boss Gate.\n"
        f"- 0648J MiMi Gift/Profile 50% + Wizard stair remains pending; do not silently mark accepted.\n\n"
        f"## Locked regression guard\n"
        f"Save schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate/collision; Airship route/visual; MiMi HOME/TV/LATE; card canon.\n",
        encoding="utf-8",
    )


set_version()
repaired_blocks = 0
for target in TARGET_TMX:
    if not target.exists():
        raise RuntimeError(f"0653 expected TMX missing: {target}")
    repaired_blocks += repair_tmx_csv(target)

if repaired_blocks != 21:
    raise RuntimeError(f"0653 expected exactly 21 malformed CSV blocks across 7 maps; repaired {repaired_blocks}")

# Validate the fixed targets and every other shipped TMX so this parser bug cannot hide elsewhere.
for tmx in sorted((CARDCHA / "assets").rglob("*.tmx")):
    validate_tmx(tmx)

write_handoff(repaired_blocks)
print(f"0653 TMX runtime compatibility fix complete: repaired {repaired_blocks} CSV block(s)")
print(NEW_VERSION)
