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


def main() -> None:
    patch_versions()
    patch_magic_dust_localization()
    patch_reveal_labels()
    patch_airship_rotors()
    patch_code_language()
    print(f"Cardcha {VERSION} finalize patch applied")


if __name__ == "__main__":
    main()
