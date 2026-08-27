using Cardcha.Models;
using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal sealed class CardchaRevealMenu : IClickableMenu
{
    private enum RevealPhase { Feed, Crank, Suspense, Reveal, Results }

    private readonly IReadOnlyList<PullResult> Results;
    private readonly CardRenderer Renderer;
    private readonly ControllerProfileService Controller;
    private readonly Action OnDone;
    private readonly ClickableComponent Skip;
    private readonly ClickableComponent Continue;
    private readonly ClickableComponent RevealAll;
    private readonly List<ClickableComponent> ResultButtons = new();

    private readonly bool[] Revealed;
    private RevealPhase Phase = RevealPhase.Feed;
    private double PhaseMs;
    private double ResultFlashMs;
    private int LastRevealedIndex = -1;

    public CardchaRevealMenu(IReadOnlyList<PullResult> results, CardRenderer renderer, ControllerProfileService controller, Action onDone)
        : base(
            Game1.uiViewport.Width / 2 - Math.Min(920, Game1.uiViewport.Width - 48) / 2,
            Game1.uiViewport.Height / 2 - Math.Min(620, Game1.uiViewport.Height - 48) / 2,
            Math.Min(920, Game1.uiViewport.Width - 48),
            Math.Min(620, Game1.uiViewport.Height - 48),
            showUpperRightCloseButton: false)
    {
        this.Results = results;
        this.Renderer = renderer;
        this.Controller = controller;
        this.OnDone = onDone;

        this.Revealed = new bool[results.Count];

        this.Skip = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + this.width - 205, this.yPositionOnScreen + 36, 150, 54),
            "skip"
        ) { myID = 100 };

        this.Continue = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + this.width / 2 - 120, this.yPositionOnScreen + this.height - 88, 240, 54),
            "continue"
        ) { myID = 200 };

        this.RevealAll = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + this.width / 2 - 285, this.yPositionOnScreen + this.height - 88, 145, 54),
            "reveal-all"
        ) { myID = 201 };

        for (int i = 0; i < this.Results.Count; i++)
        {
            this.ResultButtons.Add(
                new ClickableComponent(GetResultRect(i), $"result-{i}") { myID = 300 + i }
            );
        }

        this.ConfigureControllerComponents();

        if (Game1.options.SnappyMenus)
            this.snapToDefaultClickableComponent();
    }

    public override void update(GameTime time)
    {
        base.update(time);

        if (this.ResultFlashMs > 0)
            this.ResultFlashMs = Math.Max(0, this.ResultFlashMs - time.ElapsedGameTime.TotalMilliseconds);

        if (this.Phase == RevealPhase.Results)
            return;

        this.PhaseMs += time.ElapsedGameTime.TotalMilliseconds;

        double duration = this.Phase switch
        {
            RevealPhase.Feed => 420,
            RevealPhase.Crank => 650,
            RevealPhase.Suspense => 760,
            RevealPhase.Reveal => 720,
            _ => 0
        };

        if (this.PhaseMs < duration)
            return;

        this.PhaseMs = 0;
        this.Phase = (RevealPhase)((int)this.Phase + 1);

        if (this.Phase == RevealPhase.Reveal)
            Game1.playSound("discoverMineral");

        if (this.Phase == RevealPhase.Results && this.Results.Count == 1)
        {
            this.Revealed[0] = true;
            this.LastRevealedIndex = 0;
            this.ResultFlashMs = 700;
        }

        if (this.Phase == RevealPhase.Results)
        {
            this.ConfigureControllerComponents();

            if (Game1.options.SnappyMenus)
                this.snapToDefaultClickableComponent();
        }
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.Skip.containsPoint(x, y) && this.Phase != RevealPhase.Results)
        {
            this.Phase = RevealPhase.Results;
            this.PhaseMs = 0;

            if (this.Results.Count == 1)
                this.Revealed[0] = true;

            this.ConfigureControllerComponents();

            if (Game1.options.SnappyMenus)
                this.snapToDefaultClickableComponent();

            Game1.playSound("smallSelect");
            return;
        }

        if (this.Phase != RevealPhase.Results)
            return;

        if (this.Results.Count > 1)
        {
            for (int i = 0; i < this.ResultButtons.Count; i++)
            {
                if (this.ResultButtons[i].containsPoint(x, y))
                {
                    RevealResult(i);
                    return;
                }
            }

            if (this.RevealAll.containsPoint(x, y))
            {
                RevealEverything();
                return;
            }
        }

        if (this.Continue.containsPoint(x, y))
        {
            Game1.playSound("smallSelect");
            this.OnDone();
        }
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect, Game1.graphics.GraphicsDevice.Viewport.Bounds, Color.Black * 0.86f);
        Game1.drawDialogueBox(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height, false, true);

        string title = this.Results.Count > 1
            ? ModEntry.T("reveal.title.ten")
            : ModEntry.T("reveal.title.one");

        Vector2 titleSize = Game1.dialogueFont.MeasureString(title);
        Utility.drawTextWithShadow(
            b,
            title,
            Game1.dialogueFont,
            new Vector2(this.xPositionOnScreen + this.width / 2 - titleSize.X / 2, this.yPositionOnScreen + 38),
            CardchaUi.Gold
        );

        if (this.Phase != RevealPhase.Results)
        {
            this.DrawAnimationPhase(b);
            CardchaUi.DrawButton(b, this.Skip, ModEntry.T("reveal.skip"), Color.Gray);
        }
        else
        {
            this.DrawResults(b);

            if (this.Results.Count > 1)
                CardchaUi.DrawButton(
                    b,
                    this.RevealAll,
                    ModEntry.T("reveal.reveal-all"),
                    CardchaUi.PremiumPurple,
                    this.Revealed.Any(p => !p)
                );

            CardchaUi.DrawButton(
                b,
                this.Continue,
                ModEntry.T("reveal.back-machine"),
                CardchaUi.GoodGreen
            );
        }

        drawMouse(b);
    }

    private void ConfigureControllerComponents()
    {
        // This helper is also called directly during construction/phase changes.
        // allClickableComponents can still be null there, so initialize it lazily.
        if (this.allClickableComponents is null)
            base.populateClickableComponentList();

        if (this.allClickableComponents is null)
            return;

        this.allClickableComponents.Clear();

        if (this.Phase != RevealPhase.Results)
        {
            this.Skip.leftNeighborID = -1;
            this.Skip.rightNeighborID = -1;
            this.Skip.upNeighborID = -1;
            this.Skip.downNeighborID = -1;
            this.allClickableComponents.Add(this.Skip);
            return;
        }

        if (this.Results.Count > 1)
        {
            for (int i = 0; i < this.ResultButtons.Count; i++)
            {
                ClickableComponent c = this.ResultButtons[i];
                int col = i % 5;
                int row = i / 5;

                c.leftNeighborID = col > 0 ? 300 + i - 1 : -1;
                c.rightNeighborID = col < 4 && i + 1 < this.ResultButtons.Count
                    ? 300 + i + 1
                    : 200;

                c.upNeighborID = row > 0 ? 300 + i - 5 : -1;

                if (i + 5 < this.ResultButtons.Count)
                    c.downNeighborID = 300 + i + 5;
                else
                    c.downNeighborID = col <= 2 ? 201 : 200;

                this.allClickableComponents.Add(c);
            }

            this.RevealAll.upNeighborID = 300 + Math.Min(7, this.ResultButtons.Count - 1);
            this.RevealAll.rightNeighborID = 200;

            this.Continue.upNeighborID = 300 + Math.Min(9, this.ResultButtons.Count - 1);
            this.Continue.leftNeighborID = 201;

            this.allClickableComponents.Add(this.RevealAll);
        }

        this.allClickableComponents.Add(this.Continue);
    }

    public override void populateClickableComponentList()
    {
        // Ensure Stardew's clickable list exists before our controller graph is built.
        base.populateClickableComponentList();
        this.ConfigureControllerComponents();
    }

    public override void snapToDefaultClickableComponent()
    {
        if (this.Phase != RevealPhase.Results)
            this.currentlySnappedComponent = this.Skip;
        else if (this.Results.Count > 1)
            this.currentlySnappedComponent = this.ResultButtons.FirstOrDefault() ?? this.Continue;
        else
            this.currentlySnappedComponent = this.Continue;

        this.snapCursorToCurrentSnappedComponent();
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (this.Controller.IsExit(b))
        {
            // Reveal result is already persisted; exit returns to the machine callback safely.
            Game1.playSound("smallSelect");
            this.OnDone();
            return;
        }

        if (this.Controller.IsConfirm(b) && this.currentlySnappedComponent is not null)
        {
            Point center = this.currentlySnappedComponent.bounds.Center;
            this.receiveLeftClick(center.X, center.Y);
            return;
        }

        if (this.Controller.IsFavorite(b) || this.Controller.IsDeselect(b))
            return;

        base.receiveGamePadButton(b);
    }

    private void DrawAnimationPhase(SpriteBatch b)
    {
        string phaseText = this.Phase switch
        {
            RevealPhase.Feed => ModEntry.T("reveal.feed"),
            RevealPhase.Crank => ModEntry.T("reveal.crank"),
            RevealPhase.Suspense => ModEntry.T("reveal.suspense"),
            RevealPhase.Reveal => ModEntry.T("reveal.reveal"),
            _ => ""
        };

        Vector2 size = Game1.dialogueFont.MeasureString(phaseText);
        Utility.drawTextWithShadow(
            b,
            phaseText,
            Game1.dialogueFont,
            new Vector2(this.xPositionOnScreen + this.width / 2 - size.X / 2, this.yPositionOnScreen + 165),
            Color.Black
        );

        PullResult best = this.Results.OrderByDescending(p => p.Card.Rarity).First();
        this.DrawAnimatedMachine(b, best);

        Rectangle baseCard = new(
            this.xPositionOnScreen + this.width / 2 - 80,
            this.yPositionOnScreen + 300,
            160,
            210
        );

        if (this.Phase == RevealPhase.Reveal)
        {
            float revealProgress = (float)Math.Clamp(this.PhaseMs / 720.0, 0.0, 1.0);
            float punch = 1f + (float)Math.Sin(revealProgress * Math.PI) * 0.10f;

            int rw = (int)(baseCard.Width * punch);
            int rh = (int)(baseCard.Height * punch);
            Rectangle card = new(baseCard.Center.X - rw / 2, baseCard.Center.Y - rh / 2, rw, rh);

            Color rarity = CardchaUi.RarityColor(best.Card.Rarity);
            float pulse = 0.18f + 0.20f * (float)Math.Sin(revealProgress * Math.PI);

            Rectangle auraOuter = new(card.X - 24, card.Y - 24, card.Width + 48, card.Height + 48);
            Rectangle auraInner = new(card.X - 11, card.Y - 11, card.Width + 22, card.Height + 22);
            CardchaUi.DrawRoundedRect(b, auraOuter, rarity * pulse, 18);
            CardchaUi.DrawRoundedRect(b, auraInner, rarity * (pulse + 0.10f), 14);

            this.Renderer.DrawRevealCard(b, card, best.Card);

            this.DrawRevealSparkles(b, card, revealProgress, 1f);
        }
        else
        {
            this.Renderer.DrawCardBack(b, baseCard, this.Phase == RevealPhase.Suspense);
        }
    }

    private void DrawAnimatedMachine(SpriteBatch b, PullResult best)
    {
        try
        {
            Texture2D texture = Game1.content.Load<Texture2D>(ItemAssetService.MachineUiTextureAsset);

            int frame = this.Phase switch
            {
                RevealPhase.Feed => 2,
                RevealPhase.Crank => 1,
                RevealPhase.Suspense => 4,
                RevealPhase.Reveal when best.Card.Rarity == CardRarity.Mythic => 6,
                RevealPhase.Reveal when best.Card.Rarity == CardRarity.Legendary => 5,
                RevealPhase.Reveal when best.Card.Rarity >= CardRarity.Epic => 1,
                RevealPhase.Reveal => 0,
                _ => 0
            };

            Rectangle source = new(frame * 48, 0, 48, 96);

            float progress = this.Phase switch
            {
                RevealPhase.Feed => (float)Math.Clamp(this.PhaseMs / 420.0, 0.0, 1.0),
                RevealPhase.Crank => (float)Math.Clamp(this.PhaseMs / 650.0, 0.0, 1.0),
                RevealPhase.Suspense => (float)Math.Clamp(this.PhaseMs / 760.0, 0.0, 1.0),
                RevealPhase.Reveal => (float)Math.Clamp(this.PhaseMs / 720.0, 0.0, 1.0),
                _ => 0f
            };

            float rotation = 0f;
            float scale = 1.12f;
            float xJitter = 0f;
            float yJitter = 0f;

            if (this.Phase == RevealPhase.Crank)
            {
                rotation = (float)Math.Sin(progress * Math.PI * 8) * 0.035f;
                xJitter = (float)Math.Sin(progress * Math.PI * 12) * 3f;
            }
            else if (this.Phase == RevealPhase.Suspense)
            {
                xJitter = (float)Math.Sin(progress * Math.PI * 22) * 4f;
                yJitter = (float)Math.Cos(progress * Math.PI * 18) * 2f;
                scale = 1.12f + (float)Math.Sin(progress * Math.PI) * 0.04f;
            }
            else if (this.Phase == RevealPhase.Reveal)
            {
                scale = 1.12f + (float)Math.Sin(progress * Math.PI) * 0.08f;
            }

            Vector2 origin = new(24f, 48f);
            Vector2 center = new(
                this.xPositionOnScreen + 150 + xJitter,
                this.yPositionOnScreen + 335 + yJitter
            );

            b.Draw(
                texture,
                center,
                source,
                Color.White,
                rotation,
                origin,
                scale,
                SpriteEffects.None,
                1f
            );

            if (this.Phase == RevealPhase.Feed)
                DrawFeedParticles(b, progress, center);

            if (this.Phase == RevealPhase.Suspense)
            {
                float blink = 0.10f + 0.16f * (float)Math.Abs(Math.Sin(progress * Math.PI * 7));
                Rectangle pulse = new((int)center.X - 46, (int)center.Y - 58, 92, 116);
                b.Draw(Game1.staminaRect, pulse, CardchaUi.Gold * blink);
            }

            if (this.Phase == RevealPhase.Reveal)
            {
                Color rarity = CardchaUi.RarityColor(best.Card.Rarity);
                float wave = 0.5f + 0.5f * (float)Math.Sin(progress * Math.PI * 7f);
                float strength = best.Card.Rarity >= CardRarity.Epic ? 0.20f : 0.12f;
                Rectangle flash = new(
                    this.xPositionOnScreen + 26,
                    this.yPositionOnScreen + 112,
                    this.width - 52,
                    this.height - 160
                );
                CardchaUi.DrawRoundedRect(b, flash, rarity * (strength * wave), 14);
                CardchaUi.DrawRoundedPanel(b, flash, Color.Transparent, Color.White * (0.12f + 0.22f * wave), 3, 14);
            }

            string line = frame switch
            {
                6 => ModEntry.T("scrappy.mythic"),
                5 => ModEntry.T("scrappy.legendary"),
                4 => ModEntry.T("scrappy.suspense"),
                2 => ModEntry.T("scrappy.feed"),
                1 => ModEntry.T("scrappy.happy"),
                _ => ""
            };

            if (!string.IsNullOrWhiteSpace(line))
            {
                Rectangle reactionText = new(
                    this.xPositionOnScreen + 44,
                    this.yPositionOnScreen + 438,
                    205,
                    60
                );
                CardchaUi.DrawAutoFitWrappedText(
                    b,
                    Game1.smallFont,
                    line,
                    reactionText,
                    Color.DarkSlateGray,
                    maxLines: 3,
                    minScale: 0.42f
                );
            }
        }
        catch
        {
            // Reveal remains functional if the optional reaction art can't load.
        }
    }

    private static void DrawFeedParticles(SpriteBatch b, float progress, Vector2 machineCenter)
    {
        // Three tiny runtime cardboard scraps fly into the machine.
        for (int i = 0; i < 3; i++)
        {
            float local = Math.Clamp(progress * 1.25f - i * 0.18f, 0f, 1f);
            float ease = local * local * (3f - 2f * local);

            Vector2 from = new(machineCenter.X + 145 + i * 18, machineCenter.Y - 42 + i * 22);
            Vector2 to = new(machineCenter.X + 8, machineCenter.Y - 5);
            Vector2 pos = Vector2.Lerp(from, to, ease);

            Rectangle scrap = new((int)pos.X, (int)pos.Y, 12, 8);
            b.Draw(Game1.staminaRect, scrap, new Color(174, 116, 64));
            CardchaUi.DrawBorder(b, scrap, new Color(94, 61, 42), 2);
        }
    }

    private void DrawResults(SpriteBatch b)
    {
        if (this.Results.Count == 1)
        {
            Rectangle rect = GetResultRect(0);
            PullResult result = this.Results[0];

            if (this.Revealed[0])
            {
                DrawResultAura(b, rect, 0);
                string resultText = result.IsNew
                    ? ModEntry.T("reveal.new")
                    : ModEntry.T("reveal.duplicate");

                this.Renderer.DrawRevealCard(b, rect, result.Card, resultText);
            }
            else
            {
                this.Renderer.DrawCardBack(b, rect);
            }

            return;
        }

        for (int i = 0; i < this.Results.Count; i++)
        {
            Rectangle rect = GetResultRect(i);
            PullResult result = this.Results[i];

            if (!this.Revealed[i])
            {
                this.Renderer.DrawCardBack(b, rect, false);
                continue;
            }

            DrawResultAura(b, rect, i);

            string resultText = result.IsNew
                ? ModEntry.T("reveal.new")
                : ModEntry.T("reveal.duplicate");

            this.Renderer.DrawRevealCard(b, rect, result.Card, resultText);
        }

        foreach (ClickableComponent c in this.allClickableComponents)
        {
            if (this.currentlySnappedComponent?.myID == c.myID)
                CardchaUi.DrawFocus(b, c.bounds);
        }

        int revealedCount = this.Revealed.Count(p => p);
        string hint = revealedCount == this.Results.Count
            ? ModEntry.T("reveal.all-opened")
            : $"{ModEntry.T("reveal.tap-cards")} ({revealedCount}/{this.Results.Count})";

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            hint,
            new Rectangle(
                this.xPositionOnScreen + 180,
                this.yPositionOnScreen + 82,
                this.width - 320,
                38
            ),
            Color.DarkSlateGray,
            centerX: true,
            centerY: true,
            padding: 2
        );
    }

    private void DrawResultAura(SpriteBatch b, Rectangle rect, int index)
    {
        if (index != this.LastRevealedIndex || this.ResultFlashMs <= 0)
            return;

        PullResult result = this.Results[index];
        Color rarity = CardchaUi.RarityColor(result.Card.Rarity);
        float remaining = (float)Math.Clamp(this.ResultFlashMs / 700.0, 0.0, 1.0);
        float wave = 0.5f + 0.5f * (float)Math.Sin(this.ResultFlashMs * 0.045f);
        float alpha = (0.08f + 0.18f * wave) * remaining;

        Rectangle aura = new(rect.X - 10, rect.Y - 10, rect.Width + 20, rect.Height + 20);
        CardchaUi.DrawRoundedRect(b, aura, rarity * alpha, 16);
        CardchaUi.DrawRoundedRect(b, rect, Color.White * (0.05f + 0.13f * wave) * remaining, 12);
        this.DrawRevealSparkles(b, aura, 1f - remaining, remaining);
    }

    private void DrawRevealSparkles(SpriteBatch b, Rectangle rect, float progress, float intensity)
    {
        intensity = Math.Clamp(intensity, 0f, 1f);
        if (intensity <= 0.01f)
            return;

        Color[] colors =
        {
            Color.White,
            new Color(255, 231, 132),
            new Color(216, 190, 255)
        };

        for (int i = 0; i < 12; i++)
        {
            float angle = i / 12f * MathHelper.TwoPi + progress * 1.7f;
            float orbit = 0.56f + 0.10f * (float)Math.Sin(progress * 8f + i * 1.31f);
            float rx = rect.Width * orbit * 0.72f;
            float ry = rect.Height * orbit * 0.52f;
            int x = rect.Center.X + (int)(Math.Cos(angle) * rx);
            int y = rect.Center.Y + (int)(Math.Sin(angle) * ry);
            float blink = 0.35f + 0.65f * Math.Abs((float)Math.Sin(progress * 13f + i * 0.91f));
            int arm = 2 + (i % 3);
            Color color = colors[i % colors.Length] * (blink * intensity);

            b.Draw(Game1.staminaRect, new Rectangle(x - arm, y, arm * 2 + 1, 2), color);
            b.Draw(Game1.staminaRect, new Rectangle(x, y - arm, 2, arm * 2 + 1), color);
        }
    }

    private Rectangle GetResultRect(int index)
    {
        if (this.Results.Count == 1)
        {
            return new Rectangle(
                this.xPositionOnScreen + this.width / 2 - 110,
                this.yPositionOnScreen + 150,
                220,
                280
            );
        }

        int columns = 5;
        int cardW = 130;
        int cardH = 170;
        int gap = 14;
        int rows = 2;
        int totalW = columns * cardW + (columns - 1) * gap;
        int totalH = rows * cardH + gap;
        int startX = this.xPositionOnScreen + this.width / 2 - totalW / 2;
        int startY = this.yPositionOnScreen + 125 + Math.Max(0, (this.height - 245 - totalH) / 2);

        int col = index % columns;
        int row = index / columns;

        return new Rectangle(
            startX + col * (cardW + gap),
            startY + row * (cardH + gap),
            cardW,
            cardH
        );
    }

    private void RevealResult(int index)
    {
        if (index < 0 || index >= this.Results.Count || this.Revealed[index])
            return;

        this.Revealed[index] = true;
        this.LastRevealedIndex = index;
        this.ResultFlashMs = 700;

        CardRarity rarity = this.Results[index].Card.Rarity;
        Game1.playSound(rarity >= CardRarity.Epic ? "discoverMineral" : "smallSelect");
    }

    private void RevealEverything()
    {
        if (!this.Revealed.Any(p => !p))
            return;

        int bestIndex = -1;
        CardRarity bestRarity = CardRarity.Common;

        for (int i = 0; i < this.Revealed.Length; i++)
        {
            if (!this.Revealed[i])
            {
                this.Revealed[i] = true;

                if (bestIndex < 0 || this.Results[i].Card.Rarity > bestRarity)
                {
                    bestIndex = i;
                    bestRarity = this.Results[i].Card.Rarity;
                }
            }
        }

        this.LastRevealedIndex = bestIndex;
        this.ResultFlashMs = 800;
        Game1.playSound(bestRarity >= CardRarity.Epic ? "discoverMineral" : "coin");
    }
}
