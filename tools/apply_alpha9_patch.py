from pathlib import Path

ROOT = Path('src/Cardcha')


def replace(rel, old, new):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'alpha.9 pattern missing in {rel}: {old[:100]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


# Double MiMi + ChaCha shadow scale from the current alpha.8 values.
replace('Services/MimiMysteryTownService.cs', 'Scale = 0.72f', 'Scale = 1.44f')
replace('Services/MimiMysteryTownService.cs', 'Scale = 0.55f', 'Scale = 1.10f')

# Ground MiMi must behave like a solid normal NPC. While on the broom she may be pass-through.
replace('Services/WorldActorService.cs',
'''        actor.Scale = MimiNativeScale;
        actor.forceOneTileWide.Value = true;
        actor.farmerPassesThrough = false;
        actor.collidesWithOtherCharacters.Value = true;''',
'''        actor.Scale = MimiNativeScale;
        actor.forceOneTileWide.Value = true;
        actor.SimpleNonVillagerNPC = broom;
        actor.farmerPassesThrough = broom;
        actor.collidesWithOtherCharacters.Value = !broom;''')

# Make 17:00 departure robust even if UpdateTicked runs before TimeChanged.
replace('Services/MimiMysteryTownService.cs',
'''        if (Game1.timeOfDay >= MerchantEndTime)
        {
            this.HideNativeOffMap();
            this.MerchantDepartedToday = true;
            return;
        }
''',
'''        if (Game1.timeOfDay >= MerchantEndTime)
        {
            bool playerInTown = Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true;
            if (!IsHarshMerchantWeather() && playerInTown && !this.MerchantDepartedToday && this.Flight == FlightState.None)
            {
                this.StartMerchantDepartureFlight();
                return;
            }

            if (this.Flight == FlightState.None)
            {
                this.HideNativeOffMap();
                this.MerchantDepartedToday = true;
            }
            return;
        }
''')

# Merchant walking used to turn toward a waypoint and then freeze because intermediate sub-pixel
# positions were repeatedly rejected by tile collision sampling. Merchant waypoints are already
# screened before selection, so don't re-reject every tiny movement step.
replace('Services/MimiMysteryTownService.cs',
'''        if (IsTooCloseToOtherNpc(town, native, 220f))
            this.NextWanderDecisionAtMs = 0;''',
'''        if (!merchantMode && IsTooCloseToOtherNpc(town, native, 220f))
            this.NextWanderDecisionAtMs = 0;''')
replace('Services/MimiMysteryTownService.cs',
'''        bool safeNext = merchantMode
            ? IsTileClear(town, nextPosition + new Vector2(32f, 64f))
            : IsWorldPositionSafeForMiMi(town, nextPosition, native);''',
'''        bool safeNext = merchantMode
            ? true
            : IsWorldPositionSafeForMiMi(town, nextPosition, native);''')

# Draw buy/sell buttons directly in semantic colors so 0 money / 0 stock never makes the entry
# buttons appear disabled. Quantity confirmation still validates the actual available amount.
replace('UI/MimiScrapShopMenu.cs',
'''        CardchaUi.DrawButton(
            b,
            buyButton,
            ModEntry.T("mimi.shop.buy", new { price = buyPrice }),
            new Color(67, 150, 84),
            enabled: true
        );
        CardchaUi.DrawButton(
            b,
            sellButton,
            ModEntry.T("mimi.shop.sell", new { price = sellPrice }),
            new Color(174, 67, 61),
            enabled: true
        );''',
'''        this.DrawTradeButton(
            b,
            buyButton,
            ModEntry.T("mimi.shop.buy", new { price = buyPrice }),
            new Color(52, 166, 76)
        );
        this.DrawTradeButton(
            b,
            sellButton,
            ModEntry.T("mimi.shop.sell", new { price = sellPrice }),
            new Color(196, 62, 58)
        );''')

shop = ROOT / 'UI/MimiScrapShopMenu.cs'
shop_text = shop.read_text(encoding='utf-8')
marker = '''    private void DrawQuantityDialog(SpriteBatch b)\n    {\n'''
helper = '''    private void DrawTradeButton(SpriteBatch b, ClickableComponent button, string text, Color fill)\n    {\n        Point mouse = CardchaUi.GetUiMousePoint();\n        bool hovered = button.bounds.Contains(mouse.X, mouse.Y);\n        Color shown = hovered\n            ? new Color(\n                Math.Min(255, fill.R + 24),\n                Math.Min(255, fill.G + 24),\n                Math.Min(255, fill.B + 24)\n            )\n            : fill;\n\n        b.Draw(Game1.staminaRect, button.bounds, shown);\n        CardchaUi.DrawBorder(b, button.bounds, hovered ? CardchaUi.Gold : Color.Black * 0.58f, hovered ? 4 : 3);\n        CardchaUi.DrawScaledText(\n            b,\n            Game1.smallFont,\n            text,\n            button.bounds,\n            Color.White,\n            centerX: true,\n            centerY: true,\n            padding: 7,\n            maxScale: 1.08f\n        );\n    }\n\n'''
if marker not in shop_text:
    raise SystemExit('alpha.9 DrawQuantityDialog marker missing')
shop.write_text(shop_text.replace(marker, helper + marker, 1), encoding='utf-8')

# Typography pass requested by the player: raise the scale ceiling roughly 1.5x while retaining
# each rectangle's width/height fit, so labels become larger without overflowing their boxes.
replace('UI/CardchaUi.cs',
'''        float scale = Math.Min(
            Math.Max(0.25f, maxScale),
            Math.Min(maxWidth / Math.Max(1f, size.X), maxHeight / Math.Max(1f, size.Y))
        );''',
'''        float requestedScale = Math.Max(0.25f, maxScale * 1.50f);
        float scale = Math.Min(
            requestedScale,
            Math.Min(maxWidth / Math.Max(1f, size.X), maxHeight / Math.Max(1f, size.Y))
        );''')
replace('UI/CardchaUi.cs',
'''        float startScale = Math.Max(minScale, maxScale);''',
'''        float startScale = Math.Max(minScale, maxScale * 1.45f);''')

# One clean package version.
for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if '0.2.0-alpha.8' not in text:
        raise SystemExit(f'alpha.8 version missing in {rel}')
    path.write_text(text.replace('0.2.0-alpha.8', '0.2.0-alpha.9'), encoding='utf-8')

print('alpha.9: bigger text, doubled shadows, solid moving MiMi, reliable broom departure, explicit shop colors')
