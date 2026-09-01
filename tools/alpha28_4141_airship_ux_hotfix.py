from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.1"


def replace_required(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Required marker not found in {path}: {old[:180]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def patch_version() -> None:
    manifest = MOD / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["Version"] = VERSION
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csproj = MOD / "Cardcha.csproj"
    text = csproj.read_text(encoding="utf-8")
    text = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", text, count=1)
    csproj.write_text(text, encoding="utf-8")

    entry = MOD / "ModEntry.cs"
    text = entry.read_text(encoding="utf-8")
    text = re.sub(
        r"Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14(?:\.\d+)? [A-Z0-9 +_-]+ TEST with",
        f"Cardcha! v{VERSION} AIRSHIP UX HOTFIX TEST with",
        text,
        count=1,
    )
    text = re.sub(
        r'"Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14(?:\.\d+)? [A-Z0-9 +_-]+ TEST"',
        f'"Cardcha! v{VERSION} AIRSHIP UX HOTFIX TEST"',
        text,
        count=1,
    )
    entry.write_text(text, encoding="utf-8")


def patch_upgrade_menu() -> None:
    path = MOD / "UI" / "AirshipUpgradeMenu.cs"
    text = path.read_text(encoding="utf-8")

    text = text.replace("    private const int RowBaseId = 100;\n", "    private const int RowBaseId = 100;\n    private const long NavigationDebounceMs = 140L;\n", 1) if "NavigationDebounceMs" not in text else text
    text = text.replace("    private string Status;\n", "    private string Status;\n    private long LastNavigationAtMs;\n", 1) if "LastNavigationAtMs" not in text else text

    text = text.replace("Math.Min(920, Game1.uiViewport.Width - 24)", "Math.Min(1080, Game1.uiViewport.Width - 24)")
    text = text.replace("        int rowY = this.yPositionOnScreen + 148;\n        int rowH = 94;\n        int gap = 8;",
                        "        int rowY = this.yPositionOnScreen + 136;\n        int rowH = 100;\n        int gap = 6;")

    old_populate = '''        this.allClickableComponents.AddRange(this.Rows);\n        this.allClickableComponents.Add(this.UpgradeButton);\n        this.allClickableComponents.Add(this.CloseButton);'''
    new_populate = '''        // Controller focus is intentionally row-only. Footer buttons remain mouse-clickable,\n        // while controller Confirm upgrades the highlighted row and Cancel closes the menu.\n        // This prevents Stardew's spatial snappy-menu resolver from disagreeing with Selected.\n        this.allClickableComponents.AddRange(this.Rows);'''
    if new_populate not in text:
        if old_populate not in text:
            raise RuntimeError("AirshipUpgradeMenu clickable list marker missing")
        text = text.replace(old_populate, new_populate, 1)

    start = text.index("    public override void receiveKeyPress(Keys key)\n")
    end = text.index("    private void Select(AirshipUpgradeSystem system, bool playSound)\n", start)
    replacement = '''    public override void receiveKeyPress(Keys key)\n    {\n        if (key == Keys.Escape)\n        {\n            this.CloseMenu();\n            return;\n        }\n\n        if (key == Keys.Up)\n        {\n            this.TryMoveSelection(-1);\n            return;\n        }\n\n        if (key == Keys.Down)\n        {\n            this.TryMoveSelection(1);\n            return;\n        }\n\n        // This is a strictly vertical list. Horizontal input is consumed instead of\n        // accidentally cycling rows or letting base snappy navigation choose a distant row.\n        if (key is Keys.Left or Keys.Right)\n            return;\n\n        if (key is Keys.Enter or Keys.Space)\n        {\n            this.TryUpgradeSelected();\n            return;\n        }\n\n        base.receiveKeyPress(key);\n    }\n\n    public override void receiveGamePadButton(Buttons b)\n    {\n        if (this.Controller.IsExit(b) || this.Controller.IsDeselect(b))\n        {\n            this.CloseMenu();\n            return;\n        }\n\n        if (b is Buttons.DPadUp or Buttons.LeftThumbstickUp)\n        {\n            this.TryMoveSelection(-1);\n            return;\n        }\n\n        if (b is Buttons.DPadDown or Buttons.LeftThumbstickDown)\n        {\n            this.TryMoveSelection(1);\n            return;\n        }\n\n        if (b is Buttons.DPadLeft or Buttons.DPadRight or Buttons.LeftThumbstickLeft or Buttons.LeftThumbstickRight)\n            return;\n\n        if (this.Controller.IsConfirm(b))\n        {\n            this.TryUpgradeSelected();\n            return;\n        }\n\n        if (this.Controller.IsFavorite(b))\n            return;\n\n        base.receiveGamePadButton(b);\n    }\n\n    private void TryMoveSelection(int delta)\n    {\n        long now = Environment.TickCount64;\n        if (now - this.LastNavigationAtMs < NavigationDebounceMs)\n            return;\n\n        this.LastNavigationAtMs = now;\n        int next = Math.Clamp((int)this.Selected + Math.Sign(delta), 0, this.Rows.Length - 1);\n        if (next == (int)this.Selected)\n            return;\n\n        this.Select((AirshipUpgradeSystem)next, playSound: true);\n    }\n\n'''
    text = text[:start] + replacement + text[end:]

    # Readability pass: give descriptions more width and forbid tiny emergency scaling.
    text = text.replace("new Rectangle(row.X + 94, row.Y + 8, row.Width - 350, 30)",
                        "new Rectangle(row.X + 94, row.Y + 8, row.Width - 310, 32)")
    text = text.replace("            maxScale: 1.20f\n        );\n        CardchaUi.DrawAutoFitWrappedText(\n            b,\n            Game1.smallFont,\n            ModEntry.T($\"airship.upgrade.system.{token}.desc\"),",
                        "            maxScale: 1.30f\n        );\n        CardchaUi.DrawAutoFitWrappedText(\n            b,\n            Game1.smallFont,\n            ModEntry.T($\"airship.upgrade.system.{token}.desc\"),", 1)
    text = text.replace("new Rectangle(row.X + 94, row.Y + 40, row.Width - 350, 42)",
                        "new Rectangle(row.X + 94, row.Y + 40, row.Width - 310, 48)")
    text = text.replace("            minScale: 0.70f,\n            centerX: false,\n            maxScale: 0.96f,\n            centerY: true\n        );",
                        "            minScale: 0.82f,\n            centerX: false,\n            maxScale: 1.06f,\n            centerY: true\n        );", 1)
    text = text.replace("            maxScale: 0.92f\n        );", "            maxScale: 1.02f\n        );", 1)
    text = text.replace("            maxScale: 0.90f\n        );", "            maxScale: 1.00f\n        );", 1)

    path.write_text(text, encoding="utf-8")


def patch_airship_service() -> None:
    path = MOD / "Services" / "AirshipFoundationService.cs"
    text = path.read_text(encoding="utf-8")

    old_update = '''        if (this.PendingDepartureUntilMs > 0 && now > this.PendingDepartureUntilMs)\n            this.PendingDepartureUntilMs = 0;\n\n        if (this.FlybyActive)'''
    new_update = '''        if (this.PendingDepartureUntilMs > 0 && now > this.PendingDepartureUntilMs)\n            this.PendingDepartureUntilMs = 0;\n\n        // Cardcha-owned portal lanes behave like real exits: walk onto the endpoint and transition.\n        // The Forest gate deliberately stays action-driven for maximum map-overhaul compatibility.\n        if (now >= this.WarpGraceUntilMs && this.TryHandleAutoTransition())\n            return;\n\n        if (this.FlybyActive)'''
    if new_update not in text:
        if old_update not in text:
            raise RuntimeError("Airship OnUpdate auto-transition marker missing")
        text = text.replace(old_update, new_update, 1)

    marker = "    private bool WarpToAirshipBridge()\n"
    helper = '''    private bool TryHandleAutoTransition()\n    {\n        if (Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp || this.FlightCutsceneActive)\n            return false;\n\n        GameLocation? location = Game1.currentLocation;\n        if (location is null)\n            return false;\n\n        Point playerTile = new(\n            (int)(Game1.player.Position.X / 64f),\n            (int)(Game1.player.Position.Y / 64f)\n        );\n\n        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            Point bay = ResolveSkyDockInteriorBayTile(location);\n            Point exit = ResolveSkyDockInteriorExitTile(location);\n            if (playerTile == bay)\n                return this.WarpToAirshipBridge();\n\n            if (playerTile == exit)\n            {\n                this.ReturnToSkyDockExterior();\n                return true;\n            }\n\n            return false;\n        }\n\n        if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            Point exit = ResolveDeckExitTile(location);\n            if (playerTile == exit)\n                return this.WarpToSkyDockInterior();\n        }\n\n        return false;\n    }\n\n'''
    if helper.strip() not in text:
        if marker not in text:
            raise RuntimeError("Airship WarpToAirshipBridge marker missing")
        text = text.replace(marker, helper + marker, 1)

    old_footprint = '''        Point[] footprint =\n        {\n            anchor,\n            new(anchor.X - 1, anchor.Y),\n            new(anchor.X + 1, anchor.Y),\n            new(anchor.X - 1, anchor.Y + 1),\n            new(anchor.X, anchor.Y + 1),\n            new(anchor.X + 1, anchor.Y + 1)\n        };'''
    new_footprint = '''        // Reserve visual breathing room in front of the overlay too. We do not delete or\n        // alter Forest foliage; instead the dynamic anchor simply rejects a bushy footprint.\n        Point[] footprint =\n        {\n            new(anchor.X - 1, anchor.Y),\n            anchor,\n            new(anchor.X + 1, anchor.Y),\n            new(anchor.X - 1, anchor.Y + 1),\n            new(anchor.X, anchor.Y + 1),\n            new(anchor.X + 1, anchor.Y + 1),\n            new(anchor.X - 1, anchor.Y + 2),\n            new(anchor.X, anchor.Y + 2),\n            new(anchor.X + 1, anchor.Y + 2)\n        };'''
    if new_footprint not in text:
        if old_footprint not in text:
            raise RuntimeError("Airship safe dock footprint marker missing")
        text = text.replace(old_footprint, new_footprint, 1)

    old_blocked = '''                Vector2 tile = new(p.X, p.Y);\n                if (location.IsTileBlockedBy(tile) || location.Objects.ContainsKey(tile))\n                    return false;'''
    new_blocked = '''                Vector2 tile = new(p.X, p.Y);\n                if (location.IsTileBlockedBy(tile)\n                    || location.Objects.ContainsKey(tile)\n                    || location.terrainFeatures.ContainsKey(tile))\n                {\n                    return false;\n                }\n\n                Rectangle tileBounds = new(p.X * 64, p.Y * 64, 64, 64);\n                foreach (var feature in location.largeTerrainFeatures)\n                {\n                    if (feature.getBoundingBox().Intersects(tileBounds))\n                        return false;\n                }'''
    if new_blocked not in text:
        if old_blocked not in text:
            raise RuntimeError("Airship safe dock blocking marker missing")
        text = text.replace(old_blocked, new_blocked, 1)

    path.write_text(text, encoding="utf-8")


def patch_scavenger_copy() -> None:
    values = {
        "default.json": {
            "card.scavenger.desc": "Passive on monster defeat: a small chance to gain +1 Cardboard Scrap. No buff icon is shown because the effect rolls only when a monster is defeated.",
            "card.scavenger.star.1": "Passive: +3% chance for +1 Cardboard Scrap on monster defeat.",
            "card.scavenger.star.2": "Passive: +4% chance for +1 Cardboard Scrap on monster defeat.",
            "card.scavenger.star.3": "Passive: +5% chance for +1 Cardboard Scrap on monster defeat.",
            "card.scavenger.star.4": "Passive: +6% chance for +1 Cardboard Scrap on monster defeat.",
            "card.scavenger.star.5": "Passive: +7% chance for +1 Cardboard Scrap on monster defeat.",
        },
        "vi.json": {
            "card.scavenger.desc": "Nội tại khi hạ quái: có cơ hội nhận thêm 1 Mảnh Bìa Cardcha. Không hiện biểu tượng buff vì hiệu ứng chỉ roll lúc quái bị hạ.",
            "card.scavenger.star.1": "Nội tại: +3% cơ hội nhận thêm 1 Mảnh Bìa Cardcha khi hạ quái.",
            "card.scavenger.star.2": "Nội tại: +4% cơ hội nhận thêm 1 Mảnh Bìa Cardcha khi hạ quái.",
            "card.scavenger.star.3": "Nội tại: +5% cơ hội nhận thêm 1 Mảnh Bìa Cardcha khi hạ quái.",
            "card.scavenger.star.4": "Nội tại: +6% cơ hội nhận thêm 1 Mảnh Bìa Cardcha khi hạ quái.",
            "card.scavenger.star.5": "Nội tại: +7% cơ hội nhận thêm 1 Mảnh Bìa Cardcha khi hạ quái.",
        },
    }
    for name, updates in values.items():
        path = MOD / "i18n" / name
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(updates)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify() -> None:
    menu = (MOD / "UI" / "AirshipUpgradeMenu.cs").read_text(encoding="utf-8")
    service = (MOD / "Services" / "AirshipFoundationService.cs").read_text(encoding="utf-8")
    drop = (MOD / "Services" / "DropService.cs").read_text(encoding="utf-8")
    assert "NavigationDebounceMs = 140L" in menu
    assert "Math.Clamp((int)this.Selected + Math.Sign(delta), 0, this.Rows.Length - 1)" in menu
    assert "this.allClickableComponents.AddRange(this.Rows);" in menu
    assert "this.allClickableComponents.Add(this.UpgradeButton);" not in menu
    assert "TryHandleAutoTransition" in service
    assert "location.terrainFeatures.ContainsKey(tile)" in service
    assert "location.largeTerrainFeatures" in service
    assert "new(anchor.X, anchor.Y + 2)" in service
    assert "CollisionEdits=NONE" in service
    assert 'this.Loadout.IsEquipped("scavenger")' in drop
    assert 'this.LevelPercent("scavenger", 0.03, 0.04, 0.05, 0.06, 0.07)' in drop
    en = json.loads((MOD / "i18n" / "default.json").read_text(encoding="utf-8"))
    vi = json.loads((MOD / "i18n" / "vi.json").read_text(encoding="utf-8"))
    assert "+1 Cardboard Scrap" in en["card.scavenger.desc"]
    assert "1 Mảnh Bìa Cardcha" in vi["card.scavenger.desc"]
    assert json.loads((MOD / "manifest.json").read_text(encoding="utf-8"))["Version"] == VERSION
    print(f"alpha28.0.4.14.1 Airship UX hotfix finalizer PASS ({VERSION})")


def main() -> None:
    patch_version()
    patch_upgrade_menu()
    patch_airship_service()
    patch_scavenger_copy()
    verify()


if __name__ == "__main__":
    main()
