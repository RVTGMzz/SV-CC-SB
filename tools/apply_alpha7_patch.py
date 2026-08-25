from pathlib import Path

ROOT = Path('src/Cardcha')

def replace(rel, old, new):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'alpha.7 pattern missing in {rel}: {old[:80]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

# Center all dark/blue plaque text vertically as well as horizontally.
replace('UI/CardchaBinderMenuV2.cs',
'''        CardchaUi.DrawAutoFitWrappedText(b, Game1.dialogueFont, text, inner, new Color(244, 203, 117), maxLines: 1, minScale: 0.48f, centerX: true, maxScale: 0.92f);''',
'''        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            text,
            inner,
            new Color(244, 203, 117),
            centerX: true,
            centerY: true,
            padding: this.SW(4),
            maxScale: 0.92f
        );''')

# MiMi Shop: keep semantic green/red buttons visible and always open bulk quantity UI.
replace('UI/MimiScrapShopMenu.cs',
'''    private void OpenQuantityDialog(string resourceId, bool buying)
    {
        this.QuantityResourceId = resourceId;
        this.QuantityBuying = buying;
        this.QuantityAmount = 1;
        int max = this.GetQuantityMax();
        if (max <= 0)
        {
            this.Status = ModEntry.T(buying ? "mimi.shop.status.poor" : "mimi.shop.status.empty");
            Game1.playSound("cancel");
            return;
        }

        this.QuantityDialogOpen = true;
        this.QuantityAmount = Math.Min(this.QuantityAmount, max);
        Game1.playSound("smallSelect");
    }
''',
'''    private void OpenQuantityDialog(string resourceId, bool buying)
    {
        this.QuantityResourceId = resourceId;
        this.QuantityBuying = buying;
        int max = this.GetQuantityMax();
        this.QuantityAmount = max > 0 ? 1 : 0;
        this.QuantityDialogOpen = true;

        // Always open the selector, even with 0g / 0 scraps, so the player can see
        // the bulk-trade UI instead of a click appearing to do nothing.
        if (max <= 0)
            this.Status = ModEntry.T(buying ? "mimi.shop.status.poor" : "mimi.shop.status.empty");

        Game1.playSound("smallSelect");
    }
''')
replace('UI/MimiScrapShopMenu.cs',
'''    private void ChangeQuantity(int delta)
    {
        int max = this.GetQuantityMax();
        if (max <= 0)
        {
            this.CloseQuantityDialog();
            return;
        }

        int before = this.QuantityAmount;
        this.QuantityAmount = Math.Clamp(this.QuantityAmount + delta, 1, max);
        if (before != this.QuantityAmount)
            Game1.playSound("shiny4");
    }
''',
'''    private void ChangeQuantity(int delta)
    {
        int max = this.GetQuantityMax();
        if (max <= 0)
        {
            this.QuantityAmount = 0;
            Game1.playSound("cancel");
            return;
        }

        int before = this.QuantityAmount <= 0 ? 1 : this.QuantityAmount;
        this.QuantityAmount = Math.Clamp(before + delta, 1, max);
        if (before != this.QuantityAmount)
            Game1.playSound("shiny4");
    }
''')
replace('UI/MimiScrapShopMenu.cs',
'''    private void ConfirmQuantityTrade()
    {
        int max = this.GetQuantityMax();
        if (max <= 0)
        {
            this.CloseQuantityDialog();
            return;
        }

        int amount = Math.Clamp(this.QuantityAmount, 1, max);
        if (this.QuantityBuying)
            this.Buy(this.QuantityResourceId, amount);
        else
            this.Sell(this.QuantityResourceId, amount);

        this.QuantityDialogOpen = false;
        this.QuantityResourceId = "";
        this.QuantityAmount = 1;
    }
''',
'''    private void ConfirmQuantityTrade()
    {
        int max = this.GetQuantityMax();
        if (max <= 0 || this.QuantityAmount <= 0)
        {
            this.Status = ModEntry.T(this.QuantityBuying ? "mimi.shop.status.poor" : "mimi.shop.status.empty");
            Game1.playSound("cancel");
            return;
        }

        int amount = Math.Clamp(this.QuantityAmount, 1, max);
        if (this.QuantityBuying)
            this.Buy(this.QuantityResourceId, amount);
        else
            this.Sell(this.QuantityResourceId, amount);

        this.QuantityDialogOpen = false;
        this.QuantityResourceId = "";
        this.QuantityAmount = 1;
    }
''')
replace('UI/MimiScrapShopMenu.cs',
'''        bool canBuy = Game1.player.Money >= buyPrice;
        bool canSell = count > 0;
        CardchaUi.DrawButton(
            b,
            buyButton,
            ModEntry.T("mimi.shop.buy", new { price = buyPrice }),
            new Color(67, 150, 84),
            canBuy
        );
        CardchaUi.DrawButton(
            b,
            sellButton,
            ModEntry.T("mimi.shop.sell", new { price = sellPrice }),
            new Color(174, 67, 61),
            canSell
        );''',
'''        // Buy/Sell are entry points to the quantity selector, so keep their semantic
        // colors visible even when the current wallet/stock is zero. The confirmation
        // inside the popup is what validates the actual available quantity.
        CardchaUi.DrawButton(
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
        );''')
replace('UI/MimiScrapShopMenu.cs',
'''        int unit = this.QuantityBuying ? GetBuyPrice(this.QuantityResourceId) : GetSellPrice(this.QuantityResourceId);
        int total = checked(unit * Math.Max(1, this.QuantityAmount));
        string trade = ModEntry.T(this.QuantityBuying ? "mimi.shop.quantity.buy" : "mimi.shop.quantity.sell", new { count = this.QuantityAmount, total });''',
'''        int unit = this.QuantityBuying ? GetBuyPrice(this.QuantityResourceId) : GetSellPrice(this.QuantityResourceId);
        int safeAmount = Math.Max(0, this.QuantityAmount);
        int total = checked(unit * safeAmount);
        string trade = ModEntry.T(this.QuantityBuying ? "mimi.shop.quantity.buy" : "mimi.shop.quantity.sell", new { count = safeAmount, total });''')
replace('UI/MimiScrapShopMenu.cs',
'''        CardchaUi.DrawButton(b, this.QuantityMinusButton, "−", new Color(109, 87, 71), enabled: this.QuantityAmount > 1);
        CardchaUi.DrawButton(b, this.QuantityPlusButton, "+", new Color(109, 87, 71), enabled: this.QuantityAmount < this.GetQuantityMax());
        CardchaUi.DrawButton(b, this.QuantityConfirmButton, ModEntry.T("mimi.shop.quantity.confirm"), this.QuantityBuying ? new Color(67, 150, 84) : new Color(174, 67, 61), enabled: true);''',
'''        int quantityMax = this.GetQuantityMax();
        CardchaUi.DrawButton(b, this.QuantityMinusButton, "−", new Color(109, 87, 71), enabled: this.QuantityAmount > 1);
        CardchaUi.DrawButton(b, this.QuantityPlusButton, "+", new Color(109, 87, 71), enabled: quantityMax > 0 && this.QuantityAmount < quantityMax);
        CardchaUi.DrawButton(b, this.QuantityConfirmButton, ModEntry.T("mimi.shop.quantity.confirm"), this.QuantityBuying ? new Color(67, 150, 84) : new Color(174, 67, 61), enabled: quantityMax > 0);''')

# MiMi merchant: stronger native shadow, visible pacing, strict instant 17:00 despawn.
replace('Services/MimiMysteryTownService.cs', 'private const float WanderSpeedPixelsPerSecond = 58f;', 'private const float WanderSpeedPixelsPerSecond = 72f;')
replace('Services/MimiMysteryTownService.cs', 'private const int WanderPauseMinMs = 1400;', 'private const int WanderPauseMinMs = 850;')
replace('Services/MimiMysteryTownService.cs', 'private const int WanderPauseMaxMs = 3200;', 'private const int WanderPauseMaxMs = 1900;')
replace('Services/MimiMysteryTownService.cs',
'''                    Offset = new Point(0, -6),
                    Scale = 0.38f''',
'''                    Offset = new Point(0, -2),
                    Scale = 0.72f''')
replace('Services/MimiMysteryTownService.cs',
'''            if (e.NewTime >= MerchantEndTime)
            {
                if (!harsh && playerInTown && !this.MerchantDepartedToday && this.Flight == FlightState.None)
                    this.StartMerchantDepartureFlight();
                else if (this.Flight == FlightState.None)
                {
                    this.HideNativeOffMap();
                    this.MerchantDepartedToday = true;
                }
                return;
            }
''',
'''            if (e.NewTime >= MerchantEndTime)
            {
                // Merchant hours are strict: at 17:00 MiMi disappears immediately.
                this.Flight = FlightState.None;
                this.MerchantFlight = false;
                this.HideNativeOffMap();
                this.MerchantDepartedToday = true;
                return;
            }
''')
replace('Services/MimiMysteryTownService.cs',
'''        if (native.currentLocation != town || native.isInvisible.Value)
        {
            MoveNative(native, town, TownAnchor, 2);
            this.WanderTarget = TownAnchor;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 1800;
            this.LastWanderUpdateAtMs = CurrentGameMs();
        }
        SetNpcDisplayName(native, "MiMi");''',
'''        if (native.currentLocation != town || native.isInvisible.Value)
        {
            MoveNative(native, town, TownAnchor, 2);
            this.WanderTarget = TownAnchor;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 900;
            this.LastWanderUpdateAtMs = CurrentGameMs();
        }

        // Restore normal ground rendering every tick without teleporting or halting her.
        this.WorldActors.ConfigureMimiActor(native, broom: false, visible: true);
        native.hideShadow.Value = false;
        SetNpcDisplayName(native, "MiMi");''')
replace('Services/MimiMysteryTownService.cs',
'''    private static bool IsTooCloseToOtherNpc(GameLocation location, NPC self, float distance)
''',
'''    private Vector2 ChooseSafeMerchantWanderTarget(GameLocation town, NPC native)
    {
        // Merchant MiMi should visibly pace around the plaza. The story actor keeps stricter
        // collision rules, but the merchant only needs a clear foot tile so nearby villagers
        // cannot permanently pin her in place.
        for (int attempt = 0; attempt < WanderOffsets.Length; attempt++)
        {
            this.WanderTargetIndex = (this.WanderTargetIndex + 1) % WanderOffsets.Length;
            Vector2 candidate = TownAnchor + WanderOffsets[this.WanderTargetIndex];
            if (IsTileClear(town, candidate + new Vector2(32f, 64f)))
                return candidate;
        }

        return native.Position;
    }

    private static bool IsTooCloseToOtherNpc(GameLocation location, NPC self, float distance)
''')
replace('Services/MimiMysteryTownService.cs',
'''                this.WanderTarget = ChooseSafeWanderTarget(town, native, now);''',
'''                this.WanderTarget = merchantMode
                    ? ChooseSafeMerchantWanderTarget(town, native)
                    : ChooseSafeWanderTarget(town, native, now);''')
replace('Services/MimiMysteryTownService.cs',
'''        if (!IsWorldPositionSafeForMiMi(town, nextPosition, native))
        {
            this.WanderTarget = native.Position;
            this.NextWanderDecisionAtMs = now + 900;
            SetNativeWalkFrame(native, this.WanderFacing, 0);
            return;
        }
        native.Position = nextPosition;''',
'''        bool safeNext = merchantMode
            ? IsTileClear(town, nextPosition + new Vector2(32f, 64f))
            : IsWorldPositionSafeForMiMi(town, nextPosition, native);
        if (!safeNext)
        {
            this.WanderTarget = native.Position;
            this.NextWanderDecisionAtMs = now + (merchantMode ? 350 : 900);
            SetNativeWalkFrame(native, this.WanderFacing, 0);
            return;
        }
        native.Position = nextPosition;''')

# One clean package version.
for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if '0.2.0-alpha.6' not in text:
        raise SystemExit(f'alpha.6 version missing in {rel}')
    path.write_text(text.replace('0.2.0-alpha.6', '0.2.0-alpha.7'), encoding='utf-8')

print('alpha.7: centered plaques, reliable MiMi Shop quantity dialog, visible MiMi shadow/patrol, strict 17:00 despawn')
