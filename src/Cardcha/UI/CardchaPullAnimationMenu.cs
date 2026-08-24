using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// v0.1.17-alpha.11.2 — full animation pass for ChaCha + machine ritual.
/// The pull result is already persisted before this menu opens, so skipping or
/// closing the animation can never reroll the card or lose deterministic state.
/// </summary>
internal sealed class CardchaPullAnimationMenu : IClickableMenu
{
    private const int TotalDurationMs = 2800;

    private readonly IReadOnlyList<PullResult> Results;
    private readonly CardRenderer Renderer;
    private readonly Action ReturnToMachine;
    private readonly int PullCount;

    private Texture2D? MachineTexture;
    private Texture2D? ChaChaTexture;
    private Texture2D? OrbTexture;

    private int ElapsedMs;
    private bool Completed;
    private bool PlayedDiveSound;
    private bool PlayedMachineSound;
    private bool PlayedOrbSound;

    public CardchaPullAnimationMenu(
        IReadOnlyList<PullResult> results,
        CardRenderer renderer,
        Action returnToMachine)
        : base(
            0,
            0,
            Game1.uiViewport.Width,
            Game1.uiViewport.Height,
            showUpperRightCloseButton: false)
    {
        this.Results = results;
        this.Renderer = renderer;
        this.ReturnToMachine = returnToMachine;
        this.PullCount = Math.Max(1, results.Count);

        this.LoadTextures();
        Game1.playSound("smallSelect");
    }

    public override void update(GameTime time)
    {
        base.update(time);

        if (this.Completed)
            return;

        this.ElapsedMs += (int)time.ElapsedGameTime.TotalMilliseconds;

        if (!this.PlayedDiveSound && this.ElapsedMs >= 560)
        {
            this.PlayedDiveSound = true;
            Game1.playSound("wand");
        }

        if (!this.PlayedMachineSound && this.ElapsedMs >= 1150)
        {
            this.PlayedMachineSound = true;
            Game1.playSound("coin");
        }

        if (!this.PlayedOrbSound && this.ElapsedMs >= 1850)
        {
            this.PlayedOrbSound = true;
            Game1.playSound("reward");
        }

        if (this.ElapsedMs >= TotalDurationMs)
            this.CompleteAnimation();
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (b is Buttons.A or Buttons.B or Buttons.X or Buttons.Y)
        {
            this.SkipAnimation();
            return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
        => this.SkipAnimation();

    public override void receiveRightClick(int x, int y, bool playSound = true)
        => this.SkipAnimation();

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

        b.Draw(Game1.staminaRect, panel, new Color(42, 29, 58));
        CardchaUi.DrawBorder(b, panel, CardchaUi.Gold, 5);
        CardchaUi.DrawCornerOrnaments(b, panel, CardchaUi.Gold * 0.85f);

        Rectangle titleRect = new(panel.X + 34, panel.Y + 20, panel.Width - 68, 52);
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("pullanim.title"),
            titleRect,
            new Color(255, 227, 146),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.05f
        );

        this.DrawMachineAndChaCha(b, panel);

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

        Rectangle skipRect = new(panel.Right - 260, panel.Bottom - 43, 220, 25);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("pullanim.skip"),
            skipRect,
            new Color(205, 187, 215),
            centerX: true,
            centerY: true,
            padding: 1,
            maxScale: 0.92f
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

    private void DrawMachineAndChaCha(SpriteBatch b, Rectangle panel)
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

        if (this.ElapsedMs >= 860 && this.ElapsedMs <= 2120)
        {
            float pulse = 0.35f + (float)(Math.Sin(this.ElapsedMs * 0.012) + 1.0) * 0.13f;
            Rectangle glow = new(
                machineDest.X - 34,
                machineDest.Y + 20,
                machineDest.Width + 68,
                machineDest.Height - 40
            );
            b.Draw(Game1.fadeToBlackRect, glow, new Color(126, 87, 220) * pulse);
        }

        b.Draw(
            this.MachineTexture,
            machineDest,
            machineSource,
            Color.White
        );

        this.DrawChaCha(b, panel, machineDest);
        this.DrawOrb(b, panel, machineDest);
        this.DrawFlash(b, panel);
    }

    private void DrawChaCha(SpriteBatch b, Rectangle panel, Rectangle machineDest)
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

        Rectangle source = new(frame * 32, row * 32, 32, 32);
        Vector2 origin = new(16f, 16f);

        b.Draw(
            this.ChaChaTexture,
            pos,
            source,
            Color.White * alpha,
            rotation,
            origin,
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
        Rectangle coreRect = new(
            (int)pos.X - core / 2,
            (int)pos.Y - core / 2,
            core,
            core
        );
        b.Draw(Game1.staminaRect, coreRect, new Color(255, 244, 179) * 0.92f);
    }

    private void DrawFlash(SpriteBatch b, Rectangle panel)
    {
        if (this.ElapsedMs < 2380 || this.ElapsedMs > 2700)
            return;

        float center = 2520f;
        float alpha = 1f - Math.Abs(this.ElapsedMs - center) / 180f;
        alpha = Math.Clamp(alpha, 0f, 1f);
        b.Draw(Game1.fadeToBlackRect, panel, Color.White * (alpha * 0.62f));
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
        this.ElapsedMs = TotalDurationMs;
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
            this.ReturnToMachine
        );
    }

    private void LoadTextures()
    {
        if (ModEntry.StaticHelper is null)
            return;

        this.MachineTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/machine_anim.png");
        this.ChaChaTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_machine.png");
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
