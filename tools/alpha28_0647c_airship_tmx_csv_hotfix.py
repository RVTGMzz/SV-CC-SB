from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.2"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.3"
MAPS = (
    CARDCHA / "assets" / "airship_deck.tmx",
    CARDCHA / "assets" / "sky_dock_interior.tmx",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# Version bump.
for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    path = CARDCHA / rel
    text = read(path)
    if NEW_VERSION not in text:
        if OLD_VERSION not in text:
            raise RuntimeError(f"missing version anchor in {rel}")
        write(path, text.replace(OLD_VERSION, NEW_VERSION))

# Fix the original 0647 room generator so the bug cannot return when it is rerun.
# TMXTile's CSV decoder splits on commas and UInt32.Parse()s every token. A terminal
# comma therefore creates one final empty token and crashes Stardew's map loader.
architecture_generator = ROOT / "tools" / "alpha28_0647_airship_room_architecture.py"
architecture = read(architecture_generator)
old_csv = "def csv_layer(rows):\n    return '\\n'.join(','.join(str(v) for v in row) + ',' for row in rows)\n"
new_csv = "def csv_layer(rows):\n    # Keep commas between rows, but never emit a terminal comma: TMXTile parses every split token as UInt32.\n    return ',\\n'.join(','.join(str(v) for v in row) for row in rows)\n"
if old_csv in architecture:
    architecture = architecture.replace(old_csv, new_csv, 1)
elif new_csv not in architecture:
    raise RuntimeError("0647 architecture csv_layer anchor changed unexpectedly")
write(architecture_generator, architecture)

# Repair already-materialized maps. Only remove a comma when it is the final delimiter
# immediately before </data>; all interior commas remain untouched.
for path in MAPS:
    text = read(path)
    fixed, count = re.subn(r",(?=\s*</data>)", "", text)
    if count == 0 and ",\n  </data>" in text:
        raise RuntimeError(f"failed to normalize terminal CSV comma in {path}")
    write(path, fixed)


def validate_map(path: Path) -> None:
    root = ET.parse(path).getroot()
    layers = root.findall("layer")
    if not layers:
        raise RuntimeError(f"{path}: no tile layers")

    for layer in layers:
        width = int(layer.attrib["width"])
        height = int(layer.attrib["height"])
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "csv":
            raise RuntimeError(f"{path}: layer {layer.attrib.get('name')} is not CSV")
        body = (data.text or "").strip()
        if not body:
            raise RuntimeError(f"{path}: empty CSV layer {layer.attrib.get('name')}")
        if body.endswith(","):
            raise RuntimeError(f"{path}: terminal CSV comma survives in {layer.attrib.get('name')}")

        tokens = [token.strip() for token in body.split(",")]
        empty = [i for i, token in enumerate(tokens) if token == ""]
        if empty:
            raise RuntimeError(f"{path}: empty CSV token(s) in {layer.attrib.get('name')}: {empty[:8]}")
        if len(tokens) != width * height:
            raise RuntimeError(
                f"{path}: {layer.attrib.get('name')} has {len(tokens)} tokens; expected {width * height}"
            )
        for token in tokens:
            value = int(token, 10)
            if value < 0 or value > 0xFFFFFFFF:
                raise RuntimeError(f"{path}: tile value outside UInt32 range: {value}")


for path in MAPS:
    validate_map(path)

print(f"Prepared Cardcha {NEW_VERSION}: Airship/Sky Dock TMX CSV is UInt32-safe with no terminal empty token.")
