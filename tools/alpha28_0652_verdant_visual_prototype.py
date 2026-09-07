from pathlib import Path
import base64
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
TEMPLATES = ROOT / "tools" / "0652_templates"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.19"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"0652 expected anchor missing: {label}")
    return text.replace(old, new, 1)


def set_version() -> None:
    manifest = CARDCHA / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["Version"] = VERSION
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for rel in ["Cardcha.csproj", "Directory.Build.targets"]:
        path = CARDCHA / rel
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.18", VERSION, text)
        path.write_text(text, encoding="utf-8")


def expose_visual_snapshot() -> None:
    path = CARDCHA / "Services" / "VerdantGuardianBossService.cs"
    text = path.read_text(encoding="utf-8")
    anchor = (
        "    public bool IsInArena => Context.IsWorldReady\n"
        "        && Game1.currentLocation?.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase) == true;\n"
    )
    insert = anchor + (
        "\n"
        "    // 0652 visual layer: read-only snapshot. Combat state remains owned exclusively by this service.\n"
        "    internal VerdantGuardianState VisualState => this.State;\n"
        "    internal int VisualPhase => this.Phase;\n"
        "    internal long VisualStateStartedAtMs => this.StateStartedAtMs;\n"
        "    internal Monster? VisualBoss => this.ResolveBoss();\n"
    )
    if "internal VerdantGuardianState VisualState" not in text:
        text = replace_once(text, anchor, insert, "Verdant visual snapshot")

    old_summary = (
        "/// Boss I functional vertical slice. The body intentionally uses a vanilla GreenSlime proxy until\n"
        "/// approved custom art is authored; routing, telegraphs, phases, damage, save flags and rewards are real."
    )
    new_summary = (
        "/// Boss I functional vertical slice. A vanilla GreenSlime remains the gameplay/collision proxy;\n"
        "/// 0652 overlays Cardcha-owned custom art while routing, telegraphs, phases, damage, save flags and rewards remain authoritative here."
    )
    text = text.replace(old_summary, new_summary)
    path.write_text(text, encoding="utf-8")


def add_visual_service() -> None:
    source = TEMPLATES / "VerdantGuardianVisualService.cs.txt"
    target = CARDCHA / "Services" / "VerdantGuardianVisualService.cs"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def wire_mod_entry() -> None:
    path = CARDCHA / "ModEntry.cs"
    text = path.read_text(encoding="utf-8")

    if "private VerdantGuardianVisualService VerdantGuardianVisual" not in text:
        text = replace_once(
            text,
            "    private VerdantGuardianBossService VerdantGuardian = null!;\n",
            "    private VerdantGuardianBossService VerdantGuardian = null!;\n"
            "    private VerdantGuardianVisualService VerdantGuardianVisual = null!;\n",
            "visual field",
        )

    if "new VerdantGuardianVisualService" not in text:
        text = replace_once(
            text,
            "        this.VerdantGuardian = new VerdantGuardianBossService(helper, this.Monitor, this.Save, this.PortableMachine);\n",
            "        this.VerdantGuardian = new VerdantGuardianBossService(helper, this.Monitor, this.Save, this.PortableMachine);\n"
            "        this.VerdantGuardianVisual = new VerdantGuardianVisualService(helper, this.Monitor, this.VerdantGuardian);\n",
            "visual construction",
        )

    if "this.VerdantGuardianVisual.OnReturnedToTitle" not in text:
        text = replace_once(
            text,
            "        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardian.OnReturnedToTitle;\n",
            "        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardian.OnReturnedToTitle;\n"
            "        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardianVisual.OnReturnedToTitle;\n",
            "visual title reset",
        )

    if "this.VerdantGuardianVisual.OnRenderedWorld" not in text:
        text = replace_once(
            text,
            "        helper.Events.Display.RenderedWorld += this.VerdantGuardian.OnRenderedWorld;\n",
            "        helper.Events.Display.RenderedWorld += this.VerdantGuardian.OnRenderedWorld;\n"
            "        helper.Events.Display.RenderedWorld += this.VerdantGuardianVisual.OnRenderedWorld;\n",
            "visual render",
        )

    if "cardcha_boss1_visual_status" not in text:
        text = replace_once(
            text,
            "        helper.ConsoleCommands.Add(\"cardcha_boss1_status\", \"Show Verdant Guardian runtime/save state.\", (_, _) => this.Monitor.Log(this.VerdantGuardian.Describe(), LogLevel.Alert));\n",
            "        helper.ConsoleCommands.Add(\"cardcha_boss1_status\", \"Show Verdant Guardian runtime/save state.\", (_, _) => this.Monitor.Log(this.VerdantGuardian.Describe(), LogLevel.Alert));\n"
            "        helper.ConsoleCommands.Add(\"cardcha_boss1_visual_status\", \"Show Verdant Guardian visual animation state.\", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe(), LogLevel.Alert));\n",
            "visual status command",
        )

    text = text.replace(
        "Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.18 VERDANT GUARDIAN BOSS I TEST",
        f"Cardcha! {VERSION} VERDANT GUARDIAN VISUAL PROTOTYPE TEST",
    )
    path.write_text(text, encoding="utf-8")


def write_assets() -> None:
    source_dir = TEMPLATES / "assets"
    target_dir = CARDCHA / "assets" / "bosses" / "verdant_guardian"
    target_dir.mkdir(parents=True, exist_ok=True)

    for source in source_dir.glob("*.png.b64"):
        name = source.name[:-4]
        target = target_dir / name
        target.write_bytes(base64.b64decode(source.read_text(encoding="utf-8").strip()))


def write_handoff() -> None:
    handoff_dir = ROOT / "handoff"
    source = TEMPLATES / "ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md"
    (handoff_dir / "ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md").write_text(
        source.read_text(encoding="utf-8"), encoding="utf-8"
    )

    latest = f"""# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0652-verdant-visual-prototype`

Current build target:
`{VERSION}`

Read first:
- `handoff/ALPHA28_0652_VERDANT_VISUAL_PROTOTYPE.md`
- `handoff/VERDANT_GUARDIAN_ANIMATION_HOOK_SPEC.md`
- `handoff/ALPHA28_0650_VERDANT_GUARDIAN_BOSS1.md`
- `handoff/BOSS_CONCEPT_CANON.md`

## Current acceptance state
- Verdant Guardian gameplay prototype remains implemented; in-game acceptance pending.
- 0652 adds first Cardcha-owned visual sheets + read-only animation overlay; in-game visual acceptance pending.
- Region I Hunt Run 4-of-6 remains the route into the 20-card Boss Gate.
- 0648J MiMi Gift/Profile 50% + Wizard stair remains pending; do not silently mark accepted.

## Locked regression guard
Save schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate/collision; Airship route/visual; MiMi HOME/TV/LATE; card canon.
"""
    (handoff_dir / "LATEST_CARDCHA_HANDOFF.md").write_text(latest, encoding="utf-8")


set_version()
expose_visual_snapshot()
add_visual_service()
wire_mod_entry()
write_assets()
write_handoff()
print("0652 generator complete", VERSION)
