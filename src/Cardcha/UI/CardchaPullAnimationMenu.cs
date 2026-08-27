using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// Pull ritual shown after results have already been persisted. The stationary machine keeps
/// its classic ritual, while the portable device gives ChaCha a dedicated "fetch the card"
/// animation so the handheld feels like its own piece of Cardcha tech.
/// </summary>
internal sealed class CardchaPullAnimationMenu : IClickableMenu
{
    private const int StationaryDurationMs = 2800;
    private const int PortableDurationMs = 3300;

    private readonly IReadOnlyList<PullResult> Results;
    private readonly CardRenderer Renderer;
    private readonly ControllerProfileService Controller;
    private readonly Action ReturnToMachine;
    private readonly int PullCount;
    private readonly CardchaMachineMode Mode;

    private Texture2D? MachineTexture;
    private Texture2D? ChaChaTexture;
    private Texture2D? OrbTexture;

    private int ElapsedMs;
    private bool Completed;
    private bool PlayedDiveSound;
    private bool PlayedMachineSound;
    private bool PlayedOrbSound;
    private bool LastInputWasController;

    public CardchaPullAnimationMenu(
        IReadOnlyList<PullResult> results,
        CardRenderer renderer,
        ControllerProfileService controller,
        Action returnToMachine,
        CardchaMachineMode mode = CardchaMachineMode.Stationary)
        : base(
            0,
            0,
            Game1.uiViewport.Width,
            Game1.uiViewport.Height,
            showUpperRightCloseButton: false)
    {
        this.Results = results;
        this.Renderer = renderer;
        this.Controller = controller;
        this.ReturnToMachine = returnToMachine;
        this.PullCount = Math.Max(1, results.Count);
        this.Mode = mode;

        this.LoadTextures();
        Game1.playSound("smallSelect");
    }

    private int TotalDurationMs
        => this.Mode == CardchaMachineMode.Portable
            ? PortableDurationMs
            : StationaryDurationMs;

    private CardRarity BestRarity
    {
        get
        {
            CardRarity best = CardRarity.Common;
            foreach (PullResult result in this.Results)
            {
                if ((int)result.Card.Rarity > (int)best)
                    best = result.Card.Rarity;
            }

            return best;
        }
    }

    public override void update(GameTime time)
    {
        base.update(time);

        if (this.Completed)
            return;

        this.ElapsedMs += (int)time.ElapsedGameTime.TotalMilliseconds;

        int diveAt = this.Mode == CardchaMachineMode.Portable ? 620 : 560;
        int machineAt = this.Mode == CardchaMachineMode.Portable ? 1350 : 1150;
        int rewardAt = this.Mode == CardchaMachineMode.Portable ? 2150 : 1850;

        if (!this.PlayedDiveSound && this.ElapsedMs >= diveAt)
        {
            this.PlayedDiveSound = true;
            Game1.playSound("wand");
        }

        if (!this.PlayedMachineSound && this.ElapsedMs >= machineAt)
        {
            this.PlayedMachineSound = true;
            Game1.playSound("coin");
        }

        if (!this.PlayedOrbSound && this.ElapsedMs >= rewardAt)
        {
            this.PlayedOrbSound = true;
            Game1.playSound(this.BestRarity >= CardRarity.Epic ? "discoverMineral" : "reward");
        }

        if (this.ElapsedMs >= this.TotalDurationMs)
            this.CompleteAnimation();
    }

    public override void receiveGamePadButton(Buttons b)
    {
        this.LastInputWasController = true;

        if (this.Controller.IsSkip(b))
        {
            this.SkipAnimation();
            return;
        }

        // Consume all other face-button semantics during the ritual. Only the profile's
        // confirm/south action may skip; favorite/deselect/exit cannot pop the menu.
        if (this.Controller.IsFavorite(b) || this.Controller.IsDeselect(b) || this.Controller.IsExit(b))
            return;

        base.receiveGamePadButton(b);
    }

    public override void receiveKeyPress(Keys key)
    {
        this.LastInputWasController = false;

        if (key is Keys.Enter or Keys.Space)
        {
            this.SkipAnimation();
            return;
        }

        // Consume Escape here instead of letting the base menu pop the ritual unexpectedly.
        if (key == Keys.Escape)
            return;

        base.receiveKeyPress(key);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        this.LastInputWasController = false;
        this.SkipAnimation();
    }

    public override void receiveRightClick(int x, int y, bool playSound = true)
    {
        this.LastInputWasController = false;
        this.SkipAnimation();
    }

    public override void draw(SpriteBatch b)
    {
        int w = Game1.uiViewport.Width;
        int h = Game1.uiViewport.Height;
        Rectangle screen = new(0, 0, w, h);

        b.Draw(Game1.fadeToBlackRect, screen, Color.Black * 0.82f);

        int panelW = Math.Min(880, w - 42);
        int panelH = Math.Min(600, h - 42);
        Rectangle panel = new(
            w / 2 - panelW / 2,
            h / 2 - panelH / 2,
            panelW,
            panelH
        );

        Color panelColor = this.Mode == CardchaMachineMode.Portable
            ? new Color(34, 48, 87)
            : new Color(42, 29, 58);
        CardchaUi.DrawRoundedPanel(b, panel, panelColor, CardchaUi.Gold, thickness: 5, radius: 16);
        CardchaUi.DrawCornerOrnaments(b, panel, CardchaUi.Gold * 0.85f);

        Rectangle titleRect = new(panel.X + 34, panel.Y + 20, panel.Width - 68, 52);
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            this.Mode == CardchaMachineMode.Portable
                ? ModEntry.T("portable.pullanim.title")
                : ModEntry.T("pullanim.title"),
            titleRect,
            new Color(255, 227, 146),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );

        if (this.Mode == CardchaMachineMode.Portable)
            this.DrawPortableRitual(b, panel);
        else
            this.DrawStationaryRitual(b, panel);

        Rectangle statusRect = new(panel.X + 44, panel.Bottom - 74, panel.Width - 88, 32);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            this.GetStatusText(),
            statusRect,
            Color.White * 0.92f,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );

        Rectangle skipRect = new(panel.Right - 330, panel.Bottom - 45, 290, 27);
        string skipHint = this.LastInputWasController
            ? ModEntry.T("pullanim.skip.controller.dynamic", new { button = this.Controller.GetLabel(ControllerAction.Skip) })
            : ModEntry.T("pullanim.skip.keyboard");
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            skipHint,
            skipRect,
            new Color(205, 187, 215),
            centerX: true,
            centerY: true,
            padding: 1,
            maxScale: 0.96f
        );

        if (this.PullCount > 1)
        {
            Rectangle countRect = new(panel.X + 30, panel.Bottom - 45, 150, 28);
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                $"×{this.PullCount}",
                countRect,
                CardchaUi.Gold,
                centerX: false,
                centerY: true,
                padding: 1,
                maxScale: 1.15f
            );
        }

        drawMouse(b);
    }

    private void DrawStationaryRitual(SpriteBatch b, Rectangle panel)
    {
        if (this.MachineTexture is null || this.ChaChaTexture is null || this.OrbTexture is null)
            return;

        int centerX = panel.Center.X;
        int machineTop = panel.Y + 98;
        int machineW = 210;
        int machineH = 420;

        float machineShake = 0f;
        if (this.ElapsedMs >= 980 && this.ElapsedMs <= 1820)
            machineShake = (float)Math.Sin(this.ElapsedMs * 0.12) * 3.5f;

        int frame = this.GetMachineFrame();
        Rectangle machineSource = new(frame * 48, 0, 48, 96);
        Rectangle machineDest = new(
            centerX - machineW / 2 + (int)machineShake,
            machineTop,
            machineW,
            machineH
        );

        Rectangle shadowRect = new(machineDest.X + 24, machineDest.Bottom - 18, machineDest.Width - 48, 18);
        b.Draw(Game1.fadeToBlackRect, shadowRect, Color.Black * 0.28f);

        b.Draw(this.MachineTexture, machineDest, machineSource, Color.White);
        this.DrawStationaryChaCha(b, panel, machineDest);
        this.DrawOrb(b, panel, machineDest);
        this.DrawFlash(b, panel, 980, 2720, 1840f);
    }

    private void DrawStationaryChaCha(SpriteBatch b, Rectangle panel, Rectangle machineDest)
    {
        if (this.ChaChaTexture is null)
            return;

        float scale = 2.55f;
        float alpha = 1f;
        float rotation = 0f;
        Vector2 pos;
        int row;
        int frame;

        Vector2 start = new(panel.X + 82f, panel.Center.Y - 58f);
        Vector2 entry = new(machineDest.Center.X - 42f, machineDest.Y + 138f);
        Vector2 inside = new(machineDest.Center.X - 16f, machineDest.Y + 166f);
        Vector2 exit = new(machineDest.Center.X + 54f, machineDest.Bottom - 132f);
        Vector2 finish = new(panel.Right - 118f, panel.Center.Y - 52f);

        if (this.ElapsedMs < 700)
        {
            float phase = this.ElapsedMs / 700f;
            float t = Ease(phase);
            pos = Vector2.Lerp(start, entry, t);
            pos.Y += (float)Math.Sin(this.ElapsedMs * 0.020) * 8f;
            rotation = (float)Math.Sin(phase * Math.PI * 2f) * 0.035f;
            row = 0;
            frame = Math.Clamp((int)(phase * 6f), 0, 5);
        }
        else if (this.ElapsedMs < 1020)
        {
            float phase = (this.ElapsedMs - 700f) / 320f;
            float t = Ease(phase);
            pos = Vector2.Lerp(entry, inside, t);
            alpha = 1f - t * 0.78f;
            rotation = MathHelper.Lerp(0f, 0.20f, t);
            row = 1;
            frame = Math.Clamp((int)(phase * 6f), 0, 5);
        }
        else if (this.ElapsedMs < 1560)
        {
            return;
        }
        else if (this.ElapsedMs < 1980)
        {
            float phase = (this.ElapsedMs - 1560f) / 420f;
            float t = Ease(phase);
            pos = Vector2.Lerp(inside, exit, t);
            alpha = MathHelper.Lerp(0.40f, 1f, t);
            rotation = MathHelper.Lerp(-0.18f, 0f, t);
            row = 2;
            frame = Math.Clamp((int)(phase * 6f), 0, 5);
        }
        else
        {
            float phase = Math.Clamp((this.ElapsedMs - 1980f) / 620f, 0f, 1f);
            float t = Ease(phase);
            pos = Vector2.Lerp(exit, finish, t);
            pos.Y += (float)Math.Sin(this.ElapsedMs * 0.018) * 6f;
            rotation = (float)Math.Sin(phase * Math.PI * 2f) * 0.03f;
            row = 0;
            frame = 5 - Math.Clamp((int)(phase * 6f), 0, 5);
        }

        this.DrawChaChaFrame(b, pos, row, frame, scale, alpha, rotation);
    }

    private void DrawPortableRitual(SpriteBatch b, Rectangle panel)
    {
        if (this.MachineTexture is null || this.ChaChaTexture is null)
            return;

        Vector2 machineCenter = new(panel.Center.X, panel.Y + 328f);
        float machineBob = (float)Math.Sin(this.ElapsedMs * 0.0085f) * 3f;
        float machineShake = 0f;
        if (this.ElapsedMs >= 1080 && this.ElapsedMs <= 1900)
            machineShake = (float)Math.Sin(this.ElapsedMs * 0.16f) * 4f;

        Rectangle machineDest = new(
            (int)machineCenter.X - 66 + (int)machineShake,
            (int)(machineCenter.Y - 132 + machineBob),
            132,
            264
        );

        Rectangle shadow = new(machineDest.X + 18, machineDest.Bottom - 8, machineDest.Width - 36, 13);
        b.Draw(Game1.fadeToBlackRect, shadow, Color.Black * 0.24f);
        b.Draw(this.MachineTexture, machineDest, this.MachineTexture.Bounds, Color.White);

        this.DrawPortableCard(b, panel, machineDest);
        this.DrawPortableChaCha(b, panel, machineDest);
        this.DrawPortableSparkles(b, panel, machineDest);
        this.DrawFlash(b, panel, 1180, 3260, 2220f);
    }

    private void DrawPortableChaCha(SpriteBatch b, Rectangle panel, Rectangle machineDest)
    {
        if (this.ChaChaTexture is null)
            return;

        Vector2 start = new(panel.X + 92f, panel.Y + 244f);
        Vector2 hover = new(machineDest.Left - 48f, machineDest.Y + 86f);
        Vector2 slot = new(machineDest.Center.X, machineDest.Bottom - 52f);
        Vector2 fetch = new(machineDest.Center.X + 10f, machineDest.Bottom - 18f);
        Vector2 present = new(panel.Center.X + 126f, panel.Y + 190f);

        Vector2 pos;
        float rotation = 0f;
        float alpha = 1f;
        float scale = 2.45f;
        int row = 0;
        int frame = 0;

        if (this.ElapsedMs < 650)
        {
            float phase = this.ElapsedMs / 650f;
            float t = Ease(phase);
            pos = Vector2.Lerp(start, hover, t);
            pos.Y += (float)Math.Sin(this.ElapsedMs * 0.024f) * 8f;
            rotation = (float)Math.Sin(phase * Math.PI * 2f) * 0.045f;
            row = 0;
            frame = Math.Clamp((int)(phase * 6f), 0, 5);
        }
        else if (this.ElapsedMs < 1120)
        {
            float phase = (this.ElapsedMs - 650f) / 470f;
            pos = hover + new Vector2(
                (float)Math.Sin(phase * Math.PI * 2f) * 18f,
                (float)Math.Sin(phase * Math.PI * 4f) * 8f
            );
            rotation = (float)Math.Sin(phase * Math.PI * 2f) * 0.06f;
            row = 0;
            frame = 2 + Math.Clamp((int)(phase * 4f), 0, 3);
        }
        else if (this.ElapsedMs < 1620)
        {
            float phase = (this.ElapsedMs - 1120f) / 500f;
            float t = Ease(phase);
            pos = Vector2.Lerp(hover, slot, t);
            pos.Y -= (float)Math.Sin(t * Math.PI) * 38f;
            rotation = MathHelper.Lerp(-0.06f, 0.18f, t);
            row = 1;
            frame = Math.Clamp((int)(phase * 6f), 0, 5);
        }
        else if (this.ElapsedMs < 1900)
        {
            float phase = (this.ElapsedMs - 1620f) / 280f;
            pos = Vector2.Lerp(slot, fetch, Ease(phase));
            alpha = MathHelper.Lerp(1f, 0.58f, phase);
            row = 1;
            frame = 5;
        }
        else if (this.ElapsedMs < 2350)
        {
            float phase = (this.ElapsedMs - 1900f) / 450f;
            float t = Ease(phase);
            pos = Vector2.Lerp(fetch, new Vector2(machineDest.Center.X + 70f, machineDest.Y + 24f), t);
            pos.Y -= (float)Math.Sin(t * Math.PI) * 34f;
            alpha = MathHelper.Lerp(0.62f, 1f, t);
            rotation = MathHelper.Lerp(0.14f, -0.04f, t);
            row = 2;
            frame = Math.Clamp((int)(phase * 6f), 0, 5);
        }
        else
        {
            float phase = Math.Clamp((this.ElapsedMs - 2350f) / 650f, 0f, 1f);
            float t = Ease(phase);
            pos = Vector2.Lerp(new Vector2(machineDest.Center.X + 70f, machineDest.Y + 24f), present, t);
            pos.Y += (float)Math.Sin(this.ElapsedMs * 0.018f) * 5f;
            rotation = (float)Math.Sin(phase * Math.PI * 2f) * 0.035f;
            row = 0;
            frame = 5 - Math.Clamp((int)(phase * 6f), 0, 5);
        }

        this.DrawChaChaFrame(b, pos, row, frame, scale, alpha, rotation);
    }

    private void DrawPortableCard(SpriteBatch b, Rectangle panel, Rectangle machineDest)
    {
        if (this.ElapsedMs < 1760)
            return;

        Vector2 start = new(machineDest.Center.X, machineDest.Bottom - 40f);
        Vector2 lift = new(machineDest.Center.X, machineDest.Y + 20f);
        Vector2 reveal = new(panel.Center.X - 76f, panel.Y + 192f);

        Vector2 pos;
        float rotation;
        float scale;
        float alpha = 1f;

        if (this.ElapsedMs < 2320)
        {
            float phase = (this.ElapsedMs - 1760f) / 560f;
            float t = Ease(phase);
            pos = Vector2.Lerp(start, lift, t);
            pos.Y -= (float)Math.Sin(t * Math.PI) * 44f;
            rotation = MathHelper.Lerp(-0.10f, 0.08f, t);
            scale = MathHelper.Lerp(0.72f, 1.06f, t);
        }
        else
        {
            float phase = Math.Clamp((this.ElapsedMs - 2320f) / 660f, 0f, 1f);
            float t = Ease(phase);
            pos = Vector2.Lerp(lift, reveal, t);
            pos.Y -= (float)Math.Sin(t * Math.PI) * 52f;
            rotation = MathHelper.Lerp(0.08f, 0f, t);
            scale = MathHelper.Lerp(1.06f, 1.34f, t);
        }

        int cardW = (int)(58 * scale);
        int cardH = (int)(82 * scale);
        Rectangle card = new((int)pos.X - cardW / 2, (int)pos.Y - cardH / 2, cardW, cardH);
        Color rarity = CardchaUi.RarityColor(this.BestRarity);

        if (this.PullCount > 1)
        {
            for (int i = Math.Min(3, this.PullCount - 1); i >= 1; i--)
            {
                Rectangle back = new(card.X + i * 5, card.Y - i * 3, card.Width, card.Height);
                b.Draw(Game1.staminaRect, back, new Color(48, 38, 78) * alpha);
                CardchaUi.DrawBorder(b, back, CardchaUi.Gold * 0.72f, 2);
            }
        }

        Rectangle glow = new(card.X - 12, card.Y - 12, card.Width + 24, card.Height + 24);
        float glowAlpha = this.BestRarity >= CardRarity.Epic ? 0.24f : 0.12f;
        b.Draw(Game1.staminaRect, glow, rarity * glowAlpha);

        b.Draw(Game1.staminaRect, card, new Color(54, 39, 88) * alpha);
        CardchaUi.DrawBorder(b, card, CardchaUi.Gold, 3);

        Rectangle inner = new(card.X + 7, card.Y + 7, card.Width - 14, card.Height - 14);
        b.Draw(Game1.staminaRect, inner, new Color(78, 106, 184) * alpha);
        CardchaUi.DrawBorder(b, inner, rarity * 0.85f, 2);

        int star = Math.Max(6, card.Width / 7);
        Rectangle starH = new(card.Center.X - star, card.Center.Y - 2, star * 2, 4);
        Rectangle starV = new(card.Center.X - 2, card.Center.Y - star, 4, star * 2);
        b.Draw(Game1.staminaRect, starH, new Color(255, 224, 93) * alpha);
        b.Draw(Game1.staminaRect, starV, new Color(255, 224, 93) * alpha);

        // Alpha.11: pulse the entire card cell instead of only a tiny highlight/text-sized area.
        // This makes the gacha flash readable on controller/TV setups and at reduced UI scale.
        if (this.ElapsedMs >= 2240f)
        {
            float wave = 0.5f + 0.5f * (float)Math.Sin((this.ElapsedMs - 2240f) * 0.030f);
            float envelope = Math.Clamp((this.ElapsedMs - 2240f) / 420f, 0f, 1f);
            float cellFlash = (0.10f + wave * 0.22f) * envelope;
            b.Draw(Game1.staminaRect, card, Color.White * cellFlash);
            CardchaUi.DrawBorder(b, card, rarity * (0.68f + wave * 0.32f), 3);
        }
    }

    private void DrawPortableSparkles(SpriteBatch b, Rectangle panel, Rectangle machineDest)
    {
        if (this.ElapsedMs < 2050)
            return;

        Color rarity = CardchaUi.RarityColor(this.BestRarity);
        int count = this.BestRarity >= CardRarity.Epic ? 11 : 6;
        float time = this.ElapsedMs / 1000f;
        Vector2 center = this.ElapsedMs < 2450
            ? new Vector2(machineDest.Center.X, machineDest.Y + 32f)
            : new Vector2(panel.Center.X - 76f, panel.Y + 192f);

        for (int i = 0; i < count; i++)
        {
            float angle = time * 1.7f + i * MathHelper.TwoPi / count;
            float radius = 48f + (i % 3) * 14f + (float)Math.Sin(time * 3f + i) * 5f;
            Vector2 p = center + new Vector2((float)Math.Cos(angle), (float)Math.Sin(angle)) * radius;
            int size = 3 + (i % 2) * 2;
            Rectangle h = new((int)p.X - size, (int)p.Y - 1, size * 2, 3);
            Rectangle v = new((int)p.X - 1, (int)p.Y - size, 3, size * 2);
            Color c = (i % 2 == 0 ? rarity : new Color(255, 230, 118)) * 0.86f;
            b.Draw(Game1.staminaRect, h, c);
            b.Draw(Game1.staminaRect, v, c);
        }
    }

    private void DrawChaChaFrame(
        SpriteBatch b,
        Vector2 pos,
        int row,
        int frame,
        float scale,
        float alpha,
        float rotation)
    {
        if (this.ChaChaTexture is null)
            return;

        row = Math.Clamp(row, 0, 2);
        frame = Math.Clamp(frame, 0, 5);
        Rectangle source = new(frame * 32, row * 32, 32, 32);
        b.Draw(
            this.ChaChaTexture,
            pos,
            source,
            Color.White * Math.Clamp(alpha, 0f, 1f),
            rotation,
            new Vector2(16f, 16f),
            scale,
            SpriteEffects.None,
            0.95f
        );
    }

    private void DrawOrb(SpriteBatch b, Rectangle panel, Rectangle machineDest)
    {
        if (this.OrbTexture is null || this.ElapsedMs < 1820)
            return;

        Vector2 from = new(machineDest.Center.X + 42f, machineDest.Bottom - 120f);
        Vector2 to = new(panel.Center.X, panel.Y + 150f);
        float t = Ease(Math.Clamp((this.ElapsedMs - 1820f) / 720f, 0f, 1f));
        Vector2 pos = Vector2.Lerp(from, to, t);
        pos.Y -= (float)Math.Sin(t * Math.PI) * 64f;

        float scale = MathHelper.Lerp(1.0f, 2.55f, t);
        float rotation = (float)(this.ElapsedMs * 0.0012);

        b.Draw(
            this.OrbTexture,
            pos,
            null,
            Color.White,
            rotation,
            new Vector2(this.OrbTexture.Width / 2f, this.OrbTexture.Height / 2f),
            scale,
            SpriteEffects.None,
            0.98f
        );

        int core = Math.Max(4, (int)(6 * scale));
        Rectangle coreRect = new((int)pos.X - core / 2, (int)pos.Y - core / 2, core, core);
        b.Draw(Game1.staminaRect, coreRect, new Color(255, 244, 179) * 0.92f);
    }

    private void DrawFlash(SpriteBatch b, Rectangle panel, int startMs, int endMs, float centerMs)
    {
        if (this.ElapsedMs < startMs || this.ElapsedMs > endMs)
            return;

        float half = Math.Max(1f, (endMs - startMs) / 2f);
        float envelope = 1f - Math.Abs(this.ElapsedMs - centerMs) / half;
        envelope = Math.Clamp(envelope, 0f, 1f);

        // alpha.25: flash is a full-panel FILTER inside the ritual frame.
        // The outer frame/border itself must stay visually stable; only the content area
        // receives the rarity + white light pulse. This avoids the entire gold frame
        // changing brightness during each resonance cycle.
        float wave = 0.5f + 0.5f * (float)Math.Sin((this.ElapsedMs - startMs) * 0.030f);
        Color rarity = CardchaUi.RarityColor(this.BestRarity);
        float whiteAlpha = envelope * (0.05f + wave * 0.16f);
        float rarityAlpha = envelope * (0.025f + wave * 0.10f);

        // Stay just inside the frame thickness so the border never gets overdrawn.
        Rectangle flashArea = new(
            panel.X + 8,
            panel.Y + 8,
            Math.Max(1, panel.Width - 16),
            Math.Max(1, panel.Height - 16)
        );
        CardchaUi.DrawRoundedRect(b, flashArea, rarity * rarityAlpha, 11);
        CardchaUi.DrawRoundedRect(b, flashArea, Color.White * whiteAlpha, 11);
    }

    private int GetMachineFrame()
    {
        if (this.ElapsedMs < 620) return 0;
        if (this.ElapsedMs < 820) return 1;
        if (this.ElapsedMs < 1020) return 2;
        if (this.ElapsedMs < 1190) return 3;
        if (this.ElapsedMs < 1360) return 4;
        if (this.ElapsedMs < 1540) return 5;
        if (this.ElapsedMs < 1760) return 6;
        if (this.ElapsedMs < 2050) return 7;
        if (this.ElapsedMs < 2380) return 8;
        return 9;
    }

    private string GetStatusText()
    {
        if (this.Mode == CardchaMachineMode.Portable)
        {
            if (this.ElapsedMs < 650)
                return ModEntry.T("portable.pullanim.status.approach");
            if (this.ElapsedMs < 1120)
                return ModEntry.T("portable.pullanim.status.hover");
            if (this.ElapsedMs < 1760)
                return ModEntry.T("portable.pullanim.status.dive");
            if (this.ElapsedMs < 2350)
                return ModEntry.T("portable.pullanim.status.fetch");
            if (this.ElapsedMs < 2920)
                return ModEntry.T("portable.pullanim.status.present");
            return ModEntry.T("portable.pullanim.status.reveal");
        }

        if (this.ElapsedMs < 700)
            return ModEntry.T("pullanim.status.approach");
        if (this.ElapsedMs < 1020)
            return ModEntry.T("pullanim.status.dive");
        if (this.ElapsedMs < 1820)
            return ModEntry.T("pullanim.status.charge");
        if (this.ElapsedMs < 2380)
            return ModEntry.T("pullanim.status.orb");
        return ModEntry.T("pullanim.status.reveal");
    }

    private void SkipAnimation()
    {
        if (this.Completed)
            return;

        Game1.playSound("smallSelect");
        this.ElapsedMs = this.TotalDurationMs;
        this.CompleteAnimation();
    }

    private void CompleteAnimation()
    {
        if (this.Completed)
            return;

        this.Completed = true;
        this.OrbTexture?.Dispose();
        this.OrbTexture = null;

        Game1.activeClickableMenu = new CardchaRevealMenu(
            this.Results.ToList(),
            this.Renderer,
            this.Controller,
            this.ReturnToMachine
        );
    }

    private void LoadTextures()
    {
        if (ModEntry.StaticHelper is null)
            return;

        this.MachineTexture = this.Mode == CardchaMachineMode.Portable
            ? ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/portable_machine_ui.png")
            : ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/machine_anim.png");
        this.ChaChaTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_machine.png");

        if (this.Mode == CardchaMachineMode.Stationary)
            this.OrbTexture = CreateTransparentOrbTexture(Game1.graphics.GraphicsDevice, 24);
    }

    private static Texture2D CreateTransparentOrbTexture(GraphicsDevice device, int size)
    {
        Texture2D texture = new(device, size, size);
        Color[] pixels = new Color[size * size];
        float cx = (size - 1) / 2f;
        float cy = (size - 1) / 2f;
        float radius = size * 0.42f;

        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                float dx = x - cx;
                float dy = y - cy;
                float dist = MathF.Sqrt(dx * dx + dy * dy);
                Color c = Color.Transparent;

                if (dist <= radius)
                {
                    float edge = Math.Abs(dist - radius);
                    if (edge <= 1.4f)
                    {
                        c = new Color((byte)190, (byte)231, (byte)255, (byte)175);
                    }
                    else
                    {
                        float glass = 1f - dist / radius;
                        byte alpha = (byte)Math.Clamp(24 + (int)(glass * 26), 0, 255);
                        c = new Color((byte)128, (byte)177, (byte)229, alpha);
                    }
                }

                if ((x == 7 && y >= 5 && y <= 8)
                    || (y == 6 && x >= 6 && x <= 8))
                {
                    c = new Color((byte)255, (byte)255, (byte)255, (byte)155);
                }

                pixels[y * size + x] = c;
            }
        }

        texture.SetData(pixels);
        return texture;
    }

    private static float Ease(float t)
    {
        t = Math.Clamp(t, 0f, 1f);
        return t * t * (3f - 2f * t);
    }
}
