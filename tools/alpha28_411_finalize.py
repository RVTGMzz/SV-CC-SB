from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.11"


def replace_required(path: Path, old: str, new: str, minimum: int = 1) -> int:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count < minimum and new not in text:
        raise RuntimeError(f"Expected marker not found in {path}: {old[:120]!r}")
    if count:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    return count


def patch_versions() -> None:
    manifest = MOD / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["Version"] = VERSION
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csproj = MOD / "Cardcha.csproj"
    text = csproj.read_text(encoding="utf-8")
    import re
    text = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", text, count=1)
    csproj.write_text(text, encoding="utf-8")

    modentry = MOD / "ModEntry.cs"
    text = modentry.read_text(encoding="utf-8")
    text = text.replace("v0.3.0-alpha.28.0.4.9 AIRSHIP FINAL DESIGN ANIMATION TEST", f"v{VERSION} MAGIC DUST + UI + AIRSHIP POLISH TEST")
    modentry.write_text(text, encoding="utf-8")


def patch_magic_dust_localization() -> None:
    default_path = MOD / "i18n" / "default.json"
    vi_path = MOD / "i18n" / "vi.json"

    en = json.loads(default_path.read_text(encoding="utf-8"))
    vi = json.loads(vi_path.read_text(encoding="utf-8"))

    def normalize_en(value: str) -> str:
        return (
            value.replace("Suspicious Dust", "Magic Dust")
                 .replace("Card Dust", "Magic Dust")
                 .replace("Dust Collector", "Magic Dust Collector")
                 .replace(" +{{amount}} Dust", " +{{amount}} Magic Dust")
                 .replace("({{cost}} Dust)", "({{cost}} Magic Dust)")
                 .replace("{{cost}} Dust.", "{{cost}} Magic Dust.")
                 .replace("Not enough Dust", "Not enough Magic Dust")
                 .replace("Slot Dust:", "Magic Dust:")
        )

    def normalize_vi(value: str) -> str:
        return (
            value.replace("Bụi Đáng Ngờ", "Bụi Ma Thuật")
                 .replace("Bụi đáng ngờ", "Bụi Ma Thuật")
                 .replace("Bụi Bài", "Bụi Ma Thuật")
                 .replace("Bụi bài", "Bụi Ma Thuật")
                 .replace("Kẻ Gom Bụi", "Kẻ Gom Bụi Ma Thuật")
                 .replace("+{{amount}} Bụi", "+{{amount}} Bụi Ma Thuật")
                 .replace("({{cost}} Bụi)", "({{cost}} Bụi Ma Thuật)")
                 .replace("{{cost}} Bụi.", "{{cost}} Bụi Ma Thuật.")
                 .replace("Không đủ Bụi", "Không đủ Bụi Ma Thuật")
                 .replace("Bụi mở ô:", "Bụi Ma Thuật:")
        )

    en = {key: normalize_en(value) if isinstance(value, str) else value for key, value in en.items()}
    vi = {key: normalize_vi(value) if isinstance(value, str) else value for key, value in vi.items()}

    en["item.dust.name"] = "Magic Dust"
    en["item.dust.desc"] = "Arcane residue condensed from duplicate cards that have already reached their maximum level. ChaCha can use it now; MiMi has plans for the Airship later."
    en["reveal.max-dust"] = "+{{dust}} Magic Dust"
    en["reveal.level-copy"] = "Duplicate copy +1"

    vi["item.dust.name"] = "Bụi Ma Thuật"
    vi["item.dust.desc"] = "Dư lượng ma lực cô đặc từ những lá bài trùng đã đạt cấp tối đa. Hiện ChaCha có thể dùng nó, còn MiMi thì đã nhắm tới việc nâng cấp Tàu Bay sau này."
    vi["reveal.max-dust"] = "+{{dust}} Bụi Ma Thuật"
    vi["reveal.level-copy"] = "Bản sao +1"

    default_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    vi_path.write_text(json.dumps(vi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_reveal_labels() -> None:
    path = MOD / "UI" / "CardchaRevealMenu.cs"
    old = '''string resultText = result.IsNew
                    ? ModEntry.T("reveal.new")
                    : ModEntry.T("reveal.duplicate");'''
    new = '''string resultText = this.GetResultLabel(result);'''
    replace_required(path, old, new, minimum=1)

    old2 = '''string resultText = result.IsNew
                ? ModEntry.T("reveal.new")
                : ModEntry.T("reveal.duplicate");'''
    text = path.read_text(encoding="utf-8")
    if old2 in text:
        text = text.replace(old2, new)
        path.write_text(text, encoding="utf-8")

    helper = '''    private string GetResultLabel(PullResult result)
    {
        if (result.IsNew)
            return ModEntry.T("reveal.new");
        if (result.DustAwarded > 0)
            return ModEntry.T("reveal.duplicate-dust", new { amount = result.DustAwarded });
        if (result.DuplicateCopiesAwarded > 0)
            return ModEntry.T("reveal.duplicate-copy", new { amount = result.DuplicateCopiesAwarded });
        return ModEntry.T("reveal.duplicate");
    }

'''
    marker = "    private static string RarityLabel(CardRarity rarity)"
    text = path.read_text(encoding="utf-8")
    if "private string GetResultLabel(PullResult result)" not in text:
        if marker not in text:
            raise RuntimeError("Reveal label insertion marker missing")
        text = text.replace(marker, helper + marker, 1)
        path.write_text(text, encoding="utf-8")


def patch_airship_rotors() -> None:
    path = MOD / "Services" / "AirshipFoundationService.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("new Vector2(-88f * scale, 79f * scale)", "new Vector2(-89f * scale, 66f * scale)")
    text = text.replace("new Vector2(88f * scale, 79f * scale)", "new Vector2(90f * scale, 66f * scale)")
    text = text.replace("float length = 17f * scale;", "float length = 18f * scale;")
    text = text.replace("private const float PropellerSpinRadiansPerSecond = 20f;", "private const float PropellerSpinRadiansPerSecond = 22f;")
    path.write_text(text, encoding="utf-8")


def patch_code_language() -> None:
    path = MOD / "Services" / "GachaService.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("Card Dust", "Magic Dust")
    path.write_text(text, encoding="utf-8")


def patch_wizard_meetup_door() -> None:
    story_path = MOD / "Services" / "CardchaStoryService.cs"
    story = story_path.read_text(encoding="utf-8")

    method = '''    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || !this.Progression.ShouldStartMimiMeetup())
        {
            return;
        }

        GameLocation? location = Game1.currentLocation;
        if (location is null
            || location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        Point actionTile = GetFacingActionTile();
        string doorAction = location.doesTileHaveProperty(actionTile.X, actionTile.Y, "Action", "Buildings") ?? "";
        if (!doorAction.Contains("WizardHouse", StringComparison.OrdinalIgnoreCase))
            return;

        // Cardcha owns this door interaction only while MiMi's appointment is actually pending.
        // Before 13:00, replace the vanilla locked-door text with the appointment reminder.
        // After 17:00, leave the base game/modded map completely authoritative again.
        if (Game1.timeOfDay < 1300)
        {
            this.Helper.Input.Suppress(e.Button);
            Game1.drawObjectDialogue(ModEntry.T("story.mimi.meetup-too-early"));
            return;
        }

        if (Game1.timeOfDay > 1700)
            return;

        Point arrival = ResolveWizardHouseDoorArrival(doorAction);
        this.Helper.Input.Suppress(e.Button);
        Game1.playSound("doorClose");
        Game1.warpFarmer("WizardHouse", arrival.X, arrival.Y, 2);

        this.Monitor.Log(
            $"Cardcha Chapter 1: pending MiMi appointment temporarily bypassed Wizard Tower lock at {Game1.timeOfDay}; destination={arrival.X},{arrival.Y}.",
            LogLevel.Info
        );
    }

    private static Point GetFacingActionTile()
    {
        Point player = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        return Game1.player.FacingDirection switch
        {
            0 => new Point(player.X, player.Y - 1),
            1 => new Point(player.X + 1, player.Y),
            2 => new Point(player.X, player.Y + 1),
            3 => new Point(player.X - 1, player.Y),
            _ => player
        };
    }

    private static Point ResolveWizardHouseDoorArrival(string doorAction)
    {
        string[] tokens = doorAction.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        for (int i = 0; i < tokens.Length; i++)
        {
            if (!tokens[i].Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
                continue;

            if (i >= 2
                && int.TryParse(tokens[i - 2], out int beforeX)
                && int.TryParse(tokens[i - 1], out int beforeY))
            {
                return new Point(beforeX, beforeY);
            }

            if (i + 2 < tokens.Length
                && int.TryParse(tokens[i + 1], out int afterX)
                && int.TryParse(tokens[i + 2], out int afterY))
            {
                return new Point(afterX, afterY);
            }
        }

        // Vanilla WizardHouse doorway fallback. Only used when a map mod keeps the target name
        // but wraps the action string in an unfamiliar format.
        return new Point(3, 17);
    }

'''
    marker = "    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)"
    if "pending MiMi appointment temporarily bypassed Wizard Tower lock" not in story:
        if marker not in story:
            raise RuntimeError("Wizard meetup door insertion marker missing")
        story = story.replace(marker, method + marker, 1)
        story_path.write_text(story, encoding="utf-8")

    modentry_path = MOD / "ModEntry.cs"
    modentry = modentry_path.read_text(encoding="utf-8")
    subscription = "        helper.Events.Input.ButtonPressed += this.Story.OnButtonPressed;\n"
    marker2 = "        helper.Events.Input.ButtonPressed += this.BookTab.OnButtonPressed;"
    if subscription.strip() not in modentry:
        if marker2 not in modentry:
            raise RuntimeError("Story input subscription marker missing")
        modentry = modentry.replace(marker2, subscription + marker2, 1)
        modentry_path.write_text(modentry, encoding="utf-8")


def main() -> None:
    patch_versions()
    patch_magic_dust_localization()
    patch_reveal_labels()
    patch_airship_rotors()
    patch_code_language()
    patch_wizard_meetup_door()
    print(f"Cardcha {VERSION} finalize patch applied")


if __name__ == "__main__":
    main()
