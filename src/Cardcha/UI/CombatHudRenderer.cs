using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.UI;

/// <summary>
/// Compact top-center Cardcha combat HUD.
/// Alpha 11.41: circular horizontal slots, numeric countdowns, soft fade/slide,
/// max-three display, and hover/touch tooltips.
/// </summary>
internal sealed class CombatHudRenderer
{
    private const int FadeInMs = 180;
    private const int FadeOutMs = 240;
    private const int MaxVisibleSlots = 3;
    private const int CircleTextureSize = 64;
    // 0668B: temporary cleanup requested after in-game overlap report.
    private const bool ShowPersistentReadyIndicators = false;

    private readonly ModConfig Config;
    private readonly CombatService Combat;
    private readonly BossEnergyService BossEnergy;
    private readonly LoadoutService Loadout;
    private readonly SaveService Save;
    private readonly CardRegistry Cards;
    private readonly CardRenderer Renderer;
    private readonly Dictionary<string, HudVisualState> VisualStates = new(StringComparer.OrdinalIgnoreCase);

    private Texture2D? CircleTexture;
    private string HoveredKey = "";
    private long HoverExpiresAt;

    public CombatHudRenderer(
        ModConfig config,
        CombatService combat,
        BossEnergyService bossEnergy,
        LoadoutService loadout,
        SaveService save,
        CardRegistry cards,
        CardRenderer renderer
    )
    {
        this.Config = config;
        this.Combat = combat;
        this.BossEnergy = bossEnergy;
        this.Loadout = loadout;
        this.Save = save;
        this.Cards = cards;
        this.Renderer = renderer;
    }

    public void Draw(SpriteBatch b)
    {
        if (!Context.IsWorldReady
            || !this.Config.EnableCombatCards
            || !this.Config.EnableCombatHud
            || !this.Loadout.CardEffectsActive
            || Game1.activeClickableMenu is not null
            || Game1.player is null)
        {
            this.VisualStates.Clear();
            this.HoveredKey = "";
            this.HoverExpiresAt = 0;
            return;
        }

        EnsureCircleTexture();

        long now = Environment.TickCount64;
        List<HudEntry> liveEntries = BuildEntries()
            .OrderByDescending(p => KindPriority(p.Kind))
            .ThenByDescending(p => p.Priority)
            .Take(MaxVisibleSlots)
            .ToList();

        UpdateVisualStates(liveEntries, now);

        List<(HudVisualState State, float Alpha, float Slide)> visible = this.VisualStates.Values
            .Select(state =>
            {
                bool live = state.SeenThisFrame;
                float alpha;
                float slide;

                if (live)
                {
                    alpha = Math.Clamp((now - state.FirstSeenAt) / (float)FadeInMs, 0f, 1f);
                    slide = -12f * (1f - EaseOutCubic(alpha));
                }
                else
                {
                    float outT = Math.Clamp((now - state.LastSeenAt) / (float)FadeOutMs, 0f, 1f);
                    alpha = 1f - outT;
                    slide = -8f * EaseOutCubic(outT);
                }

                return (State: state, Alpha: alpha, Slide: slide);
            })
            .Where(p => p.Alpha > 0.01f)
            .OrderByDescending(p => p.State.SeenThisFrame)
            .ThenByDescending(p => KindPriority(p.State.Entry.Kind))
            .ThenByDescending(p => p.State.Entry.Priority)
            .Take(MaxVisibleSlots)
            .ToList();

        if (visible.Count == 0)
        {
            this.HoveredKey = "";
            this.HoverExpiresAt = 0;
            return;
        }

        float scale = (float)Math.Clamp(this.Config.CombatHudScale, 0.75, 1.5);
        int diameter = Math.Max(42, (int)(56 * scale));
        int gap = Math.Max(6, (int)(10 * scale));
        int groupW = visible.Count * diameter + Math.Max(0, visible.Count - 1) * gap;

        // 11.45: lift the circular HUD by roughly half of its previous top gap.
        // This keeps it top-center but closer to the screen edge, leaving more room below.
        int baseY = Math.Clamp((int)(Game1.uiViewport.Height * 0.040f), 18, 48);
        int baseX = (Game1.uiViewport.Width - groupW) / 2;

        int mouseX = Game1.getMouseX();
        int mouseY = Game1.getMouseY();
        HudEntry? hoveredEntry = null;

        for (int i = 0; i < visible.Count; i++)
        {
            (HudVisualState state, float alpha, float slide) = visible[i];
            int x = baseX + i * (diameter + gap);
            int y = baseY + (int)(slide * scale);
            Rectangle rect = new(x, y, diameter, diameter);

            DrawCircularEntry(b, rect, state.Entry, scale, alpha, now);

            if (PointInsideCircle(mouseX, mouseY, rect))
            {
                hoveredEntry = state.Entry;
                this.HoveredKey = state.Entry.Key;
                this.HoverExpiresAt = now + 900;
            }
        }

        if (hoveredEntry is null && !string.IsNullOrWhiteSpace(this.HoveredKey) && now <= this.HoverExpiresAt)
        {
            (HudVisualState State, float Alpha, float Slide) remembered = visible
                .FirstOrDefault(p => string.Equals(p.State.Entry.Key, this.HoveredKey, StringComparison.OrdinalIgnoreCase));

            if (remembered.State is not null)
            {
                // On touch devices the virtual pointer usually remains at the tapped point,
                // so this branch mostly keeps the selected tooltip stable across tiny frame jitter.
                hoveredEntry = remembered.State.Entry;
            }
            else
            {
                this.HoveredKey = "";
                this.HoverExpiresAt = 0;
            }
        }
        else if (hoveredEntry is null && now > this.HoverExpiresAt)
        {
            this.HoveredKey = "";
            this.HoverExpiresAt = 0;
        }

        if (hoveredEntry is not null)
        {
            int tooltipY = baseY + diameter + Math.Max(8, (int)(10 * scale));
            DrawTooltip(b, hoveredEntry, tooltipY, scale);
        }
    }

    private List<HudEntry> BuildEntries()
    {
        List<HudEntry> entries = new();


        string toast = this.Combat.CurrentHudToast;
        if (!string.IsNullOrWhiteSpace(toast))
        {
            entries.Add(new HudEntry(
                Key: "__activation",
                CardId: this.Combat.CurrentHudToastCardId,
                Label: toast,
                Value: "",
                RemainingSeconds: null,
                TotalSeconds: null,
                Timing: HudTiming.None,
                StackText: "",
                Kind: HudKind.Activated,
                Priority: 1000
            ));
        }

        if (ShowPersistentReadyIndicators && this.Loadout.IsEquipped("phoenix_heart") && this.Combat.IsPhoenixReady)
        {
            entries.Add(new HudEntry(
                Key: "phoenix_heart",
                CardId: "phoenix_heart",
                Label: ModEntry.T("hud.phoenix"),
                Value: ModEntry.T("hud.ready"),
                RemainingSeconds: null,
                TotalSeconds: null,
                Timing: HudTiming.None,
                StackText: "",
                Kind: HudKind.Ready,
                Priority: 100
            ));
        }

        if (this.Loadout.IsEquipped("last_stand") && this.Combat.IsLastStandActive)
        {
            entries.Add(new HudEntry(
                Key: "last_stand",
                CardId: "last_stand",
                Label: ModEntry.T("hud.last-stand"),
                Value: ModEntry.T("hud.active"),
                RemainingSeconds: null,
                TotalSeconds: null,
                Timing: HudTiming.None,
                StackText: "",
                Kind: HudKind.Buff,
                Priority: 40
            ));
        }

        if (this.Loadout.IsEquipped("swift_feet") && this.Combat.IsSwiftFeetActive)
        {
            entries.Add(new HudEntry(
                Key: "swift_feet",
                CardId: "swift_feet",
                Label: ModEntry.T("hud.swift-feet"),
                Value: "+1",
                RemainingSeconds: null,
                TotalSeconds: null,
                Timing: HudTiming.None,
                StackText: "",
                Kind: HudKind.Buff,
                Priority: 30
            ));
        }

        if (this.Loadout.IsEquipped("soul_eater"))
        {
            if (this.Combat.IsSoulEaterActive)
            {
                double seconds = this.Combat.CurrentSoulEaterSecondsRemaining;
                entries.Add(new HudEntry(
                    Key: "soul_eater",
                    CardId: "soul_eater",
                    Label: ModEntry.T("hud.soul-eater", new { damage = Math.Round(this.Combat.CurrentSoulEaterDamagePercent, 1) }),
                    Value: $"{seconds:0.0}s",
                    RemainingSeconds: seconds,
                    TotalSeconds: Math.Max(0.1, this.Combat.CurrentSoulEaterSecondsRemaining),
                    Timing: HudTiming.Duration,
                    StackText: "",
                    Kind: HudKind.Buff,
                    Priority: 35
                ));
            }
            else if (ShowPersistentReadyIndicators)
            {
                entries.Add(new HudEntry(
                    Key: "soul_eater_progress",
                    CardId: "soul_eater",
                    Label: ModEntry.T("card.soul_eater.name"),
                    Value: $"{this.Combat.CurrentSoulEaterKills}/{this.Combat.CurrentSoulEaterKillTarget}",
                    RemainingSeconds: null,
                    TotalSeconds: null,
                    Timing: HudTiming.None,
                    StackText: $"{this.Combat.CurrentSoulEaterKills}/{this.Combat.CurrentSoulEaterKillTarget}",
                    Kind: HudKind.Ready,
                    Priority: 25
                ));
            }
        }

        // 0668B: every player-facing timed proc should visibly confirm that the card fired.
        // Passive always-on cards stay quiet; duration/stack effects get a compact Cardcha slot.
        foreach (TimedCardHudState timed in this.Combat.CurrentTimedCardHudStates)
        {
            CardDefinition? timedCard = this.Cards.Get(timed.CardId);
            string label = timedCard?.Name ?? timed.CardId;
            entries.Add(new HudEntry(
                Key: "timed_" + timed.CardId,
                CardId: timed.CardId,
                Label: label,
                Value: $"{timed.RemainingSeconds:0.0}s",
                RemainingSeconds: timed.RemainingSeconds,
                TotalSeconds: timed.TotalSeconds,
                Timing: HudTiming.Duration,
                StackText: timed.StackText,
                Kind: HudKind.Buff,
                Priority: timed.Priority
            ));
        }

        if (this.Loadout.IsEquipped("chain_hunter"))
        {
            int stacks = this.Combat.CurrentChainHunterStacks;
            double seconds = this.Combat.CurrentChainSecondsRemaining;
            double total = Math.Max(0.1, this.Combat.CurrentChainDurationSeconds);

            if (stacks > 0)
            {
                entries.Add(new HudEntry(
                    Key: "chain_hunter",
                    CardId: "chain_hunter",
                    Label: ModEntry.T("hud.chain", new { stacks, max = this.Config.ChainHunterMaxStacks }),
                    Value: $"{seconds:0.0}s",
                    RemainingSeconds: Math.Max(0, seconds),
                    TotalSeconds: total,
                    Timing: HudTiming.Duration,
                    StackText: $"{stacks}/{this.Config.ChainHunterMaxStacks}",
                    Kind: HudKind.Buff,
                    Priority: 20
                ));
            }
        }

        if (this.Loadout.IsEquipped("blood_fang"))
        {
            double cooldown = this.Combat.BloodFangCooldownSecondsRemaining;
            double total = Math.Max(0.1, this.Combat.BloodFangCooldownTotalSeconds);
            if (cooldown > 0.05)
            {
                entries.Add(new HudEntry(
                    Key: "blood_fang",
                    CardId: "blood_fang",
                    Label: ModEntry.T("hud.blood-fang"),
                    Value: $"{cooldown:0.0}s",
                    RemainingSeconds: Math.Max(0, cooldown),
                    TotalSeconds: total,
                    Timing: HudTiming.Cooldown,
                    StackText: "",
                    Kind: HudKind.Buff,
                    Priority: 10
                ));
            }
        }

        return entries;
    }

    private void UpdateVisualStates(IReadOnlyList<HudEntry> liveEntries, long now)
    {
        foreach (HudVisualState state in this.VisualStates.Values)
            state.SeenThisFrame = false;

        foreach (HudEntry entry in liveEntries)
        {
            if (!this.VisualStates.TryGetValue(entry.Key, out HudVisualState? state))
            {
                state = new HudVisualState(entry, now);
                this.VisualStates[entry.Key] = state;
            }
            else
            {
                if (entry.Kind == HudKind.Activated
                    && !string.Equals(state.Entry.Label, entry.Label, StringComparison.Ordinal))
                {
                    state.FirstSeenAt = now;
                }

                state.Entry = entry;
            }

            state.LastSeenAt = now;
            state.SeenThisFrame = true;
        }

        foreach (string key in this.VisualStates
            .Where(pair => !pair.Value.SeenThisFrame && now - pair.Value.LastSeenAt > FadeOutMs)
            .Select(pair => pair.Key)
            .ToList())
        {
            this.VisualStates.Remove(key);
        }
    }

    private void DrawCircularEntry(SpriteBatch b, Rectangle rect, HudEntry entry, float scale, float alpha, long now)
    {
        if (this.CircleTexture is null)
            return;

        (Color accent, Color bg) = entry.Kind switch
        {
            HudKind.Ready => (new Color(103, 190, 119), new Color(31, 57, 48)),
            HudKind.Activated => (CardchaUi.PremiumPurple, new Color(55, 39, 69)),
            _ => (CardchaUi.Gold, new Color(42, 47, 57))
        };

        float pulse = entry.Kind == HudKind.Activated
            ? 1f + 0.06f * (float)Math.Sin(now / 95.0)
            : 1f;

        Rectangle pulseRect = ScaleRectFromCenter(rect, pulse);

        // Round slot: colored outer ring + soft dark inner disc.
        b.Draw(this.CircleTexture, pulseRect, accent * (0.82f * alpha));
        int inset = Math.Max(3, (int)(4 * scale));
        Rectangle inner = new(
            pulseRect.X + inset,
            pulseRect.Y + inset,
            Math.Max(1, pulseRect.Width - inset * 2),
            Math.Max(1, pulseRect.Height - inset * 2)
        );
        b.Draw(this.CircleTexture, inner, bg * (0.72f * alpha));

        // Depleting circular timer ring, represented by small perimeter dots.
        if (entry.RemainingSeconds is double remaining && entry.TotalSeconds is double total && total > 0.001)
        {
            double progress = Math.Clamp(remaining / total, 0, 1);
            DrawProgressDots(b, pulseRect, accent, progress, alpha, scale);
        }

        int iconInset = Math.Max(9, (int)(12 * scale));
        Rectangle iconRect = new(
            pulseRect.X + iconInset,
            pulseRect.Y + iconInset,
            Math.Max(1, pulseRect.Width - iconInset * 2),
            Math.Max(1, pulseRect.Height - iconInset * 2)
        );

        if (!string.IsNullOrWhiteSpace(entry.CardId))
        {
            CardDefinition? card = this.Cards.Get(entry.CardId);
            if (card is not null && alpha > 0.08f)
                this.Renderer.DrawIcon(b, iconRect, card, alpha);
        }

        // Compact state marker: ring color carries the category, while these glyphs make
        // READY / ACTIVATED unmistakable without restoring wide text bars.
        if (entry.Kind != HudKind.Buff)
        {
            string glyph = entry.Kind == HudKind.Ready ? "✓" : "!";
            int markerSize = Math.Max(16, (int)(18 * scale));
            Rectangle marker = new(
                pulseRect.Right - markerSize,
                pulseRect.Y,
                markerSize,
                markerSize
            );
            b.Draw(this.CircleTexture, marker, accent * (0.96f * alpha));
            DrawCenteredText(b, glyph, marker, Color.White * alpha, scale * 0.62f);
        }

        if (!string.IsNullOrWhiteSpace(entry.StackText))
        {
            int badgeW = Math.Max(23, (int)(28 * scale));
            int badgeH = Math.Max(15, (int)(17 * scale));
            Rectangle stackRect = new(
                pulseRect.X - (int)(2 * scale),
                pulseRect.Bottom - badgeH + (int)(1 * scale),
                badgeW,
                badgeH
            );
            b.Draw(Game1.staminaRect, stackRect, Color.Black * (0.62f * alpha));
            CardchaUi.DrawBorder(b, stackRect, accent * (0.78f * alpha), 1);
            DrawCenteredText(b, entry.StackText, stackRect, Color.White * alpha, scale * 0.46f);
        }

        if (entry.RemainingSeconds is double seconds && seconds > 0.01)
        {
            int shown = Math.Max(1, (int)Math.Ceiling(seconds));
            string timer = shown.ToString();
            int timerSize = Math.Max(24, (int)(28 * scale));
            Rectangle timerRect = new(
                pulseRect.Center.X - timerSize / 2,
                pulseRect.Center.Y - timerSize / 2,
                timerSize,
                timerSize
            );

            // Dark center disc makes 5→4→3→2→1 readable without hiding the whole card art.
            b.Draw(this.CircleTexture, timerRect, Color.Black * (0.58f * alpha));
            DrawCenteredText(b, timer, timerRect, Color.White * alpha, scale * 0.78f);
        }
    }

    private void DrawTooltip(SpriteBatch b, HudEntry entry, int y, float scale)
    {
        string cardName = GetCardLocalizedText(entry.CardId, "name", entry.Label);
        string description = GetCardLocalizedText(entry.CardId, "desc", entry.Label);
        string state = entry.Kind switch
        {
            HudKind.Ready => ModEntry.T("hud.badge.ready"),
            HudKind.Activated => ModEntry.T("hud.badge.activated"),
            _ => ModEntry.T("hud.badge.buff")
        };

        List<string> lines = new()
        {
            cardName,
            ModEntry.T("hud.tooltip.state", new { state }),
            description
        };

        if (entry.Kind == HudKind.Activated && !string.IsNullOrWhiteSpace(entry.Label))
            lines.Add(entry.Label);

        if (entry.RemainingSeconds is double remaining && entry.TotalSeconds is double total)
        {
            string key = entry.Timing == HudTiming.Cooldown
                ? "hud.tooltip.cooldown"
                : "hud.tooltip.remaining";
            lines.Add(ModEntry.T(key, new
            {
                remaining = Math.Max(0, remaining).ToString("0.0"),
                total = Math.Max(0, total).ToString("0.0")
            }));
        }

        if (!string.IsNullOrWhiteSpace(entry.StackText))
            lines.Add(ModEntry.T("hud.tooltip.stacks", new { stacks = entry.StackText }));

        int maxW = Math.Clamp((int)(390 * scale), 300, Math.Max(300, Game1.uiViewport.Width - 40));
        int padding = Math.Max(12, (int)(14 * scale));
        int textW = maxW - padding * 2;

        string title = Game1.parseText(lines[0], Game1.dialogueFont, textW);
        string body = string.Join("\n", lines.Skip(1).Select(line => Game1.parseText(line, Game1.smallFont, textW)));

        Vector2 titleSize = Game1.dialogueFont.MeasureString(title);
        Vector2 bodySize = Game1.smallFont.MeasureString(body);
        int width = Math.Min(maxW, Math.Max(220, (int)Math.Ceiling(Math.Max(titleSize.X * 0.72f, bodySize.X * 0.82f)) + padding * 2));
        int height = Math.Max(76, (int)Math.Ceiling(titleSize.Y * 0.72f + bodySize.Y * 0.82f) + padding * 2 + 4);

        int x = (Game1.uiViewport.Width - width) / 2;
        Rectangle panel = new(x, y, width, height);

        b.Draw(Game1.staminaRect, panel, new Color(31, 34, 42) * 0.86f);
        CardchaUi.DrawBorder(b, panel, CardchaUi.Gold * 0.80f, 2);

        Vector2 titlePos = new(panel.X + padding, panel.Y + padding - 2);
        b.DrawString(
            Game1.dialogueFont,
            title,
            titlePos,
            Color.White,
            0f,
            Vector2.Zero,
            0.72f,
            SpriteEffects.None,
            1f
        );

        Vector2 bodyPos = new(panel.X + padding, titlePos.Y + titleSize.Y * 0.72f + 2);
        b.DrawString(
            Game1.smallFont,
            body,
            bodyPos,
            new Color(232, 232, 232),
            0f,
            Vector2.Zero,
            0.82f,
            SpriteEffects.None,
            1f
        );
    }

    private string GetCardLocalizedText(string cardId, string suffix, string fallback)
    {
        if (string.IsNullOrWhiteSpace(cardId))
            return fallback;

        string key = $"card.{cardId}.{suffix}";
        string value = ModEntry.T(key);
        return string.IsNullOrWhiteSpace(value) || string.Equals(value, key, StringComparison.OrdinalIgnoreCase)
            ? fallback
            : value;
    }

    private void DrawProgressDots(SpriteBatch b, Rectangle rect, Color color, double progress, float alpha, float scale)
    {
        const int segments = 28;
        int active = (int)Math.Ceiling(Math.Clamp(progress, 0, 1) * segments);
        if (active <= 0)
            return;

        float radius = rect.Width * 0.48f;
        float cx = rect.Center.X;
        float cy = rect.Center.Y;
        int dot = Math.Max(2, (int)(3 * scale));

        for (int i = 0; i < active; i++)
        {
            // Starts at 12 o'clock and depletes clockwise as remaining time falls.
            double angle = -Math.PI / 2.0 + (Math.PI * 2.0 * i / segments);
            int x = (int)Math.Round(cx + Math.Cos(angle) * radius) - dot / 2;
            int y = (int)Math.Round(cy + Math.Sin(angle) * radius) - dot / 2;
            b.Draw(Game1.staminaRect, new Rectangle(x, y, dot, dot), color * (0.95f * alpha));
        }
    }

    private void EnsureCircleTexture()
    {
        if (this.CircleTexture is not null)
            return;

        Texture2D texture = new(Game1.graphics.GraphicsDevice, CircleTextureSize, CircleTextureSize);
        Color[] pixels = new Color[CircleTextureSize * CircleTextureSize];
        float center = (CircleTextureSize - 1) / 2f;
        float radius = CircleTextureSize / 2f - 1f;

        for (int y = 0; y < CircleTextureSize; y++)
        {
            for (int x = 0; x < CircleTextureSize; x++)
            {
                float dx = x - center;
                float dy = y - center;
                float distance = MathF.Sqrt(dx * dx + dy * dy);
                float edge = Math.Clamp(radius - distance + 1f, 0f, 1f);
                pixels[y * CircleTextureSize + x] = Color.White * edge;
            }
        }

        texture.SetData(pixels);
        this.CircleTexture = texture;
    }

    private static Rectangle ScaleRectFromCenter(Rectangle rect, float scale)
    {
        if (Math.Abs(scale - 1f) < 0.001f)
            return rect;

        int width = Math.Max(1, (int)Math.Round(rect.Width * scale));
        int height = Math.Max(1, (int)Math.Round(rect.Height * scale));
        return new Rectangle(rect.Center.X - width / 2, rect.Center.Y - height / 2, width, height);
    }

    private static bool PointInsideCircle(int x, int y, Rectangle rect)
    {
        float dx = x - rect.Center.X;
        float dy = y - rect.Center.Y;
        float radius = rect.Width / 2f;
        return dx * dx + dy * dy <= radius * radius;
    }

    private static void DrawCenteredText(SpriteBatch b, string text, Rectangle rect, Color color, float maxScale)
    {
        Vector2 size = Game1.smallFont.MeasureString(text);
        float scale = Math.Min(maxScale, (rect.Width - 4) / Math.Max(1f, size.X));
        scale = Math.Max(0.34f, scale);
        Vector2 pos = new(
            rect.Center.X - size.X * scale / 2f,
            rect.Center.Y - size.Y * scale / 2f
        );

        b.DrawString(Game1.smallFont, text, pos + new Vector2(1f, 1f), Color.Black * (0.70f * color.A / 255f), 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
        b.DrawString(Game1.smallFont, text, pos, color, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }

    private static float EaseOutCubic(float t)
    {
        t = Math.Clamp(t, 0f, 1f);
        float inv = 1f - t;
        return 1f - inv * inv * inv;
    }

    private static int KindPriority(HudKind kind)
        => kind switch
        {
            HudKind.Activated => 3,
            HudKind.Ready => 2,
            _ => 1
        };

    private enum HudKind
    {
        Buff,
        Ready,
        Activated
    }

    private enum HudTiming
    {
        None,
        Duration,
        Cooldown
    }

    private sealed record HudEntry(
        string Key,
        string CardId,
        string Label,
        string Value,
        double? RemainingSeconds,
        double? TotalSeconds,
        HudTiming Timing,
        string StackText,
        HudKind Kind,
        int Priority
    );

    private sealed class HudVisualState
    {
        public HudEntry Entry;
        public long FirstSeenAt;
        public long LastSeenAt;
        public bool SeenThisFrame;

        public HudVisualState(HudEntry entry, long now)
        {
            this.Entry = entry;
            this.FirstSeenAt = now;
            this.LastSeenAt = now;
            this.SeenThisFrame = true;
        }
    }
}
