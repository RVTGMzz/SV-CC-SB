using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// alpha.26.2 ChaCha Resonance foundation.
/// This menu intentionally contains no Resonance Energy meter. Energy/transform combat behavior
/// remains a later gameplay system; this pass establishes navigation, Mythic Echo placeholders,
/// Resonance Ability placeholders, and collection-driven support-progression presentation.
/// </summary>
internal sealed class ChaChaResonanceMenu : IClickableMenu
{
    private const int BackId = 100;
    private const int TabBaseId = 200;
    private const int EntryBaseId = 400;

    private readonly CardRegistry Cards;
    private readonly SaveService Save;
    private readonly ControllerProfileService Controller;
    private readonly IClickableMenu ParentMenu;

    private readonly Rectangle OuterPanel;
    private readonly Rectangle HeaderRect;
    private readonly Rectangle LeftPanel;
    private readonly Rectangle RightPanel;
    private readonly Rectangle ContentRect;

    private readonly ClickableComponent BackButton;
    private readonly List<(ResonanceTab Tab, ClickableComponent Button)> Tabs = new();
    private readonly List<ClickableComponent> EntryButtons = new();

    private ResonanceTab CurrentTab = ResonanceTab.MythicEchoes;
    private Texture2D? ChaChaTexture;
    private Texture2D? ChaChaPortraitTexture;
    private Texture2D? SkillIconTexture;
    private string Status = ModEntry.T("resonance.status.ready");
    private bool LastInputWasController;

    private enum ResonanceTab
    {
        MythicEchoes,
        Abilities,
        SupportProgress
    }

    public ChaChaResonanceMenu(
        CardRegistry cards,
        SaveService save,
        ControllerProfileService controller,
        IClickableMenu parentMenu)
        : base(
            0,
            0,
            Game1.uiViewport.Width,
            Game1.uiViewport.Height,
            showUpperRightCloseButton: false)
    {
        this.Cards = cards;
        this.Save = save;
        this.Controller = controller;
        this.ParentMenu = parentMenu;

        int viewportW = Game1.uiViewport.Width;
        int viewportH = Game1.uiViewport.Height;
        int panelW = Math.Min(1260, Math.Max(760, viewportW - 44));
        int panelH = Math.Min(780, Math.Max(520, viewportH - 44));
        int panelX = viewportW / 2 - panelW / 2;
        int panelY = viewportH / 2 - panelH / 2;

        this.OuterPanel = new Rectangle(panelX, panelY, panelW, panelH);
        this.HeaderRect = new Rectangle(panelX + 24, panelY + 18, panelW - 48, 62);

        int bodyY = this.HeaderRect.Bottom + 10;
        int bodyH = this.OuterPanel.Bottom - bodyY - 78;
        int leftW = Math.Clamp((int)(panelW * 0.32f), 250, 390);
        this.LeftPanel = new Rectangle(panelX + 24, bodyY, leftW, bodyH);
        this.RightPanel = new Rectangle(
            this.LeftPanel.Right + 18,
            bodyY,
            this.OuterPanel.Right - (this.LeftPanel.Right + 18) - 24,
            bodyH
        );

        this.BackButton = new ClickableComponent(
            new Rectangle(this.HeaderRect.X, this.HeaderRect.Y + 7, 108, 44),
            "resonance-back") { myID = BackId };

        int tabGap = 8;
        int tabW = Math.Max(128, (this.RightPanel.Width - tabGap * 2) / 3);
        int tabH = 50;
        ResonanceTab[] tabOrder =
        {
            ResonanceTab.MythicEchoes,
            ResonanceTab.Abilities,
            ResonanceTab.SupportProgress
        };

        for (int i = 0; i < tabOrder.Length; i++)
        {
            Rectangle r = new(
                this.RightPanel.X + i * (tabW + tabGap),
                this.RightPanel.Y,
                tabW,
                tabH
            );
            this.Tabs.Add((tabOrder[i], new ClickableComponent(r, $"resonance-tab-{tabOrder[i]}") { myID = TabBaseId + i }));
        }

        this.ContentRect = new Rectangle(
            this.RightPanel.X,
            this.RightPanel.Y + tabH + 12,
            this.RightPanel.Width,
            this.RightPanel.Height - tabH - 12
        );

        this.TryLoadChaChaTexture();
        this.RebuildEntries();
        this.RebuildClickableComponents();
        this.snapToDefaultClickableComponent();
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.Tabs.FirstOrDefault().Button ?? this.BackButton;
        this.snapCursorToCurrentSnappedComponent();
    }

    public override void receiveGamePadButton(Buttons b)
    {
        this.LastInputWasController = true;

        if (this.Controller.IsExit(b))
        {
            this.ReturnToBinder();
            return;
        }

        if (b == Buttons.LeftShoulder)
        {
            this.ChangeTab(-1);
            return;
        }

        if (b == Buttons.RightShoulder)
        {
            this.ChangeTab(1);
            return;
        }

        // These semantic actions have no meaning in the Resonance foundation yet.
        // Consume them so they never leak into a parent menu or close this screen unexpectedly.
        if (this.Controller.IsFavorite(b) || this.Controller.IsDeselect(b))
        {
            Game1.playSound("cancel");
            return;
        }

        if (this.Controller.IsConfirm(b) && this.currentlySnappedComponent is not null)
        {
            this.ActivateFocusedComponent();
            return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveKeyPress(Keys key)
    {
        this.LastInputWasController = false;

        if (key == Keys.Escape)
        {
            this.ReturnToBinder();
            return;
        }

        if ((key is Keys.Enter or Keys.Space) && this.currentlySnappedComponent is not null)
        {
            this.ActivateFocusedComponent();
            return;
        }

        base.receiveKeyPress(key);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        this.LastInputWasController = false;

        if (this.BackButton.bounds.Contains(x, y))
        {
            this.ReturnToBinder();
            return;
        }

        foreach ((ResonanceTab tab, ClickableComponent button) in this.Tabs)
        {
            if (!button.bounds.Contains(x, y))
                continue;

            this.SetTab(tab);
            return;
        }

        for (int i = 0; i < this.EntryButtons.Count; i++)
        {
            if (!this.EntryButtons[i].bounds.Contains(x, y))
                continue;

            this.HandleEntryActivation(i);
            return;
        }

        base.receiveLeftClick(x, y, playSound);
    }

    private void ActivateFocusedComponent()
    {
        ClickableComponent? focused = this.currentlySnappedComponent;
        if (focused is null)
            return;

        if (focused.myID == BackId)
        {
            this.ReturnToBinder();
            return;
        }

        int tabIndex = focused.myID - TabBaseId;
        if (tabIndex >= 0 && tabIndex < this.Tabs.Count)
        {
            this.SetTab(this.Tabs[tabIndex].Tab);
            return;
        }

        int entryIndex = focused.myID - EntryBaseId;
        if (entryIndex >= 0 && entryIndex < this.EntryButtons.Count)
        {
            this.HandleEntryActivation(entryIndex);
            return;
        }
    }

    private void HandleEntryActivation(int index)
    {
        if (this.CurrentTab == ResonanceTab.MythicEchoes)
        {
            int milestone = new[] { 20, 40, 60, 80 }[Math.Clamp(index, 0, 3)];
            this.Status = this.DiscoveredCount >= milestone
                ? ModEntry.T("resonance.echo.status.awaiting", new { milestone })
                : ModEntry.T("resonance.echo.status.locked", new { milestone });
            Game1.playSound("cancel");
            return;
        }

        if (this.CurrentTab == ResonanceTab.Abilities)
        {
            ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;
            string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(index);
            if (skills is not null && skills.HasSkill(skillId))
            {
                skills.SetActive(skillId);
                this.Status = ModEntry.T("resonance.ability.equipped", new { name = ModEntry.T($"chacha.skill.{skillId}.name") });
                return;
            }

            this.Status = ModEntry.T("resonance.ability.find-region", new { region = index + 1 });
            Game1.playSound("cancel");
            return;
        }

        this.Status = ModEntry.T("resonance.support.status.foundation");
        Game1.playSound("smallSelect");
    }

    private void ChangeTab(int direction)
    {
        ResonanceTab[] order =
        {
            ResonanceTab.MythicEchoes,
            ResonanceTab.Abilities,
            ResonanceTab.SupportProgress
        };
        int current = Array.IndexOf(order, this.CurrentTab);
        int next = (current + direction + order.Length) % order.Length;
        this.SetTab(order[next]);
    }

    private void SetTab(ResonanceTab tab)
    {
        if (this.CurrentTab == tab)
            return;

        this.CurrentTab = tab;
        this.Status = ModEntry.T("resonance.status.ready");
        Game1.playSound("shwip");
        this.RebuildEntries();
        this.RebuildClickableComponents();

        ClickableComponent? selectedTab = this.Tabs.FirstOrDefault(p => p.Tab == tab).Button;
        this.currentlySnappedComponent = selectedTab ?? this.BackButton;
        if (Game1.options.SnappyMenus)
            this.snapCursorToCurrentSnappedComponent();
    }

    private int DiscoveredCount
        => CardRegistry.CountActiveOwned(this.Save.Data.OwnedCards);

    private void RebuildEntries()
    {
        this.EntryButtons.Clear();

        if (this.CurrentTab == ResonanceTab.SupportProgress)
        {
            // Three large information panels remain focusable so controller users can read status/help.
            int gap = 12;
            int h = Math.Max(110, (this.ContentRect.Height - gap * 2) / 3);
            for (int i = 0; i < 3; i++)
            {
                Rectangle r = new(
                    this.ContentRect.X,
                    this.ContentRect.Y + i * (h + gap),
                    this.ContentRect.Width,
                    Math.Min(h, this.ContentRect.Bottom - (this.ContentRect.Y + i * (h + gap)))
                );
                this.EntryButtons.Add(new ClickableComponent(r, $"support-{i}") { myID = EntryBaseId + i });
            }
            return;
        }

        int cellGap = 14;
        int cellW = (this.ContentRect.Width - cellGap) / 2;
        int cellH = (this.ContentRect.Height - cellGap) / 2;
        for (int i = 0; i < 4; i++)
        {
            int col = i % 2;
            int row = i / 2;
            Rectangle r = new(
                this.ContentRect.X + col * (cellW + cellGap),
                this.ContentRect.Y + row * (cellH + cellGap),
                cellW,
                cellH
            );
            this.EntryButtons.Add(new ClickableComponent(r, $"entry-{i}") { myID = EntryBaseId + i });
        }
    }

    private void RebuildClickableComponents()
    {
        // Stardew initializes allClickableComponents in the base implementation.
        // ChaCha Resonance rebuilds its graph during construction, so initialize the
        // base list first before clearing/replacing it with our custom components.
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        this.allClickableComponents.Add(this.BackButton);
        foreach ((_, ClickableComponent button) in this.Tabs)
            this.allClickableComponents.Add(button);
        this.allClickableComponents.AddRange(this.EntryButtons);

        this.BackButton.rightNeighborID = TabBaseId;
        this.BackButton.downNeighborID = this.EntryButtons.Count > 0 ? EntryBaseId : TabBaseId;

        for (int i = 0; i < this.Tabs.Count; i++)
        {
            ClickableComponent tab = this.Tabs[i].Button;
            tab.leftNeighborID = i == 0 ? BackId : TabBaseId + i - 1;
            tab.rightNeighborID = i == this.Tabs.Count - 1 ? -1 : TabBaseId + i + 1;
            tab.downNeighborID = this.EntryButtons.Count > 0 ? EntryBaseId : -1;
        }

        if (this.CurrentTab == ResonanceTab.SupportProgress)
        {
            for (int i = 0; i < this.EntryButtons.Count; i++)
            {
                ClickableComponent entry = this.EntryButtons[i];
                entry.upNeighborID = i == 0 ? TabBaseId + 2 : EntryBaseId + i - 1;
                entry.downNeighborID = i == this.EntryButtons.Count - 1 ? -1 : EntryBaseId + i + 1;
            }
        }
        else
        {
            for (int i = 0; i < this.EntryButtons.Count; i++)
            {
                ClickableComponent entry = this.EntryButtons[i];
                int col = i % 2;
                int row = i / 2;
                entry.leftNeighborID = col == 0 ? -1 : EntryBaseId + i - 1;
                entry.rightNeighborID = col == 1 ? -1 : EntryBaseId + i + 1;
                entry.upNeighborID = row == 0 ? TabBaseId + (int)this.CurrentTab : EntryBaseId + i - 2;
                entry.downNeighborID = row == 1 ? -1 : EntryBaseId + i + 2;
            }
        }
    }

    private void ReturnToBinder()
    {
        Game1.playSound("bigDeSelect");
        Game1.activeClickableMenu = this.ParentMenu;
    }

    public override void draw(SpriteBatch b)
    {
        int viewportW = Game1.uiViewport.Width;
        int viewportH = Game1.uiViewport.Height;
        b.Draw(Game1.fadeToBlackRect, new Rectangle(0, 0, viewportW, viewportH), Color.Black * 0.84f);

        Color frame = new(229, 166, 62);
        Color deep = new(35, 25, 43);
        Color panel = new(54, 38, 61);
        Color pink = new(238, 105, 181);

        CardchaUi.DrawRoundedPanel(b, this.OuterPanel, deep, frame, thickness: 4, radius: 18);
        CardchaUi.DrawCornerOrnaments(b, this.OuterPanel, frame * 0.72f);

        CardchaUi.DrawButton(b, this.BackButton, ModEntry.T("resonance.back"), new Color(85, 61, 86), enabled: true, textScale: 1.0f);
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("resonance.title"),
            this.HeaderRect,
            new Color(255, 224, 165),
            centerX: true,
            centerY: true,
            padding: 114,
            maxScale: 1.08f
        );

        CardchaUi.DrawRoundedPanel(b, this.LeftPanel, new Color(46, 34, 53), pink * 0.82f, thickness: 3, radius: 14);
        this.DrawChaChaPanel(b, pink);

        foreach ((ResonanceTab tab, ClickableComponent button) in this.Tabs)
        {
            bool active = tab == this.CurrentTab;
            Color fill = active ? new Color(118, 65, 117) : panel;
            CardchaUi.DrawButton(b, button, this.GetTabLabel(tab), fill, enabled: true, textScale: 0.93f, textPadding: 7);
            if (active)
                CardchaUi.DrawBorder(b, button.bounds, pink * 0.92f, 2);
        }

        switch (this.CurrentTab)
        {
            case ResonanceTab.MythicEchoes:
                this.DrawMythicEchoes(b, pink);
                break;
            case ResonanceTab.Abilities:
                this.DrawAbilities(b, pink);
                break;
            case ResonanceTab.SupportProgress:
                this.DrawSupportProgress(b, pink);
                break;
        }

        // alpha.26.2: two full-width footer rows stay outside the content panels so
        // text isn't crushed against the lower edge on Cinderbox/mobile UI scales.
        Rectangle statusRect = new(
            this.OuterPanel.X + 32,
            this.OuterPanel.Bottom - 66,
            this.OuterPanel.Width - 64,
            28
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            this.Status,
            statusRect,
            new Color(211, 196, 219),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 1.08f
        );

        string hint = this.LastInputWasController
            ? ModEntry.T("resonance.hint.controller", new { confirm = this.Controller.GetLabel(ControllerAction.Confirm), exit = this.Controller.GetLabel(ControllerAction.Exit) })
            : ModEntry.T("resonance.hint.keyboard");
        Rectangle hintRect = new(this.OuterPanel.X + 32, this.OuterPanel.Bottom - 36, this.OuterPanel.Width - 64, 24);
        CardchaUi.DrawScaledText(b, Game1.smallFont, hint, hintRect, Color.White * 0.76f, centerX: true, centerY: true, padding: 1, maxScale: 1.00f);

        drawMouse(b);
    }

    private void DrawChaChaPanel(SpriteBatch b, Color pink)
    {
        Rectangle title = new(this.LeftPanel.X + 16, this.LeftPanel.Y + 14, this.LeftPanel.Width - 32, 36);
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("resonance.chacha"),
            title,
            new Color(255, 190, 224),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.90f
        );

        // alpha.26.3+: the upper area is a real ChaCha portrait instead of an oversized
        // 32px world sprite. Keep enough room below for a small living animation strip.
        int portraitSize = Math.Clamp(
            Math.Min(this.LeftPanel.Width - 64, this.LeftPanel.Height - 230),
            96,
            220
        );
        Rectangle portrait = new(
            this.LeftPanel.Center.X - portraitSize / 2,
            title.Bottom + 8,
            portraitSize,
            portraitSize
        );
        CardchaUi.DrawRoundedPanel(b, portrait, new Color(31, 25, 39), pink * 0.48f, thickness: 2, radius: 18);

        double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;
        float portraitPulse = 0.5f + 0.5f * (float)Math.Sin(seconds * 1.8);
        Rectangle portraitAura = new(portrait.X + 12, portrait.Y + 12, portrait.Width - 24, portrait.Height - 24);
        CardchaUi.DrawRoundedRect(b, portraitAura, pink * (0.025f + portraitPulse * 0.025f), radius: 30);

        if (this.ChaChaPortraitTexture is not null)
        {
            int inset = Math.Max(4, portrait.Width / 28);
            Rectangle portraitDest = new(
                portrait.X + inset,
                portrait.Y + inset,
                portrait.Width - inset * 2,
                portrait.Height - inset * 2
            );
            b.Draw(this.ChaChaPortraitTexture, portraitDest, this.ChaChaPortraitTexture.Bounds, Color.White);
        }
        else if (this.ChaChaTexture is not null)
        {
            // Safe fallback if an old install is missing the portrait asset.
            int frame = (int)(seconds * 3.0) % 4;
            Rectangle source = new(frame * 32, 0, 32, 32);
            float scale = Math.Max(2.4f, Math.Min(4.0f, portrait.Width / 48f));
            b.Draw(
                this.ChaChaTexture,
                new Vector2(portrait.Center.X, portrait.Center.Y),
                source,
                Color.White,
                0f,
                new Vector2(16f, 16f),
                scale,
                SpriteEffects.None,
                1f
            );
        }

        Rectangle formLabel = new(this.LeftPanel.X + 18, portrait.Bottom + 7, this.LeftPanel.Width - 36, 24);
        CardchaUi.DrawScaledText(b, Game1.smallFont, ModEntry.T("resonance.current-echo"), formLabel, new Color(226, 202, 229), centerX: true, centerY: true, padding: 2, maxScale: 0.96f);

        Rectangle formValue = new(this.LeftPanel.X + 18, formLabel.Bottom + 1, this.LeftPanel.Width - 36, 30);
        CardchaUi.DrawScaledText(b, Game1.dialogueFont, ModEntry.T("resonance.current-echo.none"), formValue, pink, centerX: true, centerY: true, padding: 2, maxScale: 0.72f);

        Rectangle dustInfo = new(this.LeftPanel.X + 18, formValue.Bottom + 2, this.LeftPanel.Width - 36, 25);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("resonance.card-dust", new { amount = Math.Max(0, this.Save.Data.SuspiciousDust) }),
            dustInfo,
            new Color(222, 187, 255),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.94f
        );

        // The lower strip is intentionally roomy, but ChaCha no longer hovers at one fixed
        // center point. A pair of slow non-matching waves creates a soft pseudo-random drift
        // across the box without frantic movement or edge collisions.
        int animY = dustInfo.Bottom + 6;
        int animBottom = this.LeftPanel.Bottom - 14;
        if (animBottom - animY >= 54)
        {
            Rectangle anim = new(this.LeftPanel.X + 14, animY, this.LeftPanel.Width - 28, animBottom - animY);
            CardchaUi.DrawRoundedPanel(b, anim, new Color(28, 24, 36), pink * 0.26f, thickness: 1, radius: 12);

            if (this.ChaChaTexture is not null)
            {
                int frame = (int)(seconds * 2.6) % 4;
                Rectangle source = new(frame * 32, 0, 32, 32);
                float scale = Math.Clamp(anim.Height / 56f, 1.45f, 2.15f) * 1.25f; // alpha.26.4: refreshed ChaCha art +25%.
                float spriteSize = 32f * scale;
                float rangeX = Math.Max(0f, (anim.Width - spriteSize) * 0.5f - 10f);
                float rangeY = Math.Max(0f, (anim.Height - spriteSize) * 0.5f - 6f);

                float wanderX = ((float)Math.Sin(seconds * 0.53) + 0.46f * (float)Math.Sin(seconds * 0.21 + 1.7)) / 1.46f;
                float wanderY = ((float)Math.Sin(seconds * 0.41 + 0.8) + 0.42f * (float)Math.Sin(seconds * 0.17 + 2.4)) / 1.42f;
                Vector2 center = new(
                    anim.Center.X + wanderX * rangeX * 0.72f,
                    anim.Center.Y + wanderY * rangeY * 0.55f + (float)Math.Sin(seconds * 2.1) * 1.8f
                );

                b.Draw(
                    this.ChaChaTexture,
                    center,
                    source,
                    Color.White,
                    (float)Math.Sin(seconds * 0.63) * 0.015f,
                    new Vector2(16f, 16f),
                    scale,
                    SpriteEffects.None,
                    1f
                );

                // A very light sparkle trail keeps the box alive without filling it with noise.
                for (int i = 0; i < 3; i++)
                {
                    float phase = (float)(seconds * 0.9 + i * 2.1);
                    int sx = (int)(center.X - 16f * scale + Math.Sin(phase) * 9f - i * 5f);
                    int sy = (int)(center.Y + 10f * scale + Math.Cos(phase * 1.3f) * 5f + i * 2f);
                    float alpha = 0.28f + 0.18f * (float)Math.Abs(Math.Sin(phase));
                    b.Draw(Game1.staminaRect, new Rectangle(sx, sy, 3, 3), new Color(255, 231, 132) * alpha);
                }
            }
        }
    }

    private void DrawMythicEchoes(SpriteBatch b, Color pink)
    {
        int[] milestones = { 20, 40, 60, 80 };
        for (int i = 0; i < this.EntryButtons.Count && i < milestones.Length; i++)
        {
            Rectangle r = this.EntryButtons[i].bounds;
            int milestone = milestones[i];
            bool reached = this.DiscoveredCount >= milestone;
            bool focused = this.currentlySnappedComponent?.myID == this.EntryButtons[i].myID;

            Color border = focused ? Color.White : reached ? CardchaUi.Gold : new Color(105, 83, 112);
            CardchaUi.DrawRoundedPanel(b, r, new Color(49, 36, 58), border, thickness: focused ? 4 : 3, radius: 14);

            Rectangle milestoneRect = new(r.X + 14, r.Y + 12, r.Width - 28, 28);
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                ModEntry.T("resonance.echo.milestone", new { milestone }),
                milestoneRect,
                reached ? new Color(255, 218, 139) : Color.White * 0.58f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.95f
            );

            int iconSize = Math.Min(88, Math.Max(58, r.Height / 3));
            Rectangle icon = new(r.Center.X - iconSize / 2, r.Y + 52, iconSize, iconSize);
            CardchaUi.DrawRoundedPanel(b, icon, new Color(27, 23, 34), pink * (reached ? 0.55f : 0.25f), thickness: 2, radius: 18);
            CardchaUi.DrawScaledText(b, Game1.dialogueFont, "???", icon, reached ? pink : Color.White * 0.38f, centerX: true, centerY: true, padding: 8, maxScale: 0.72f);

            Rectangle nameRect = new(r.X + 16, icon.Bottom + 10, r.Width - 32, 32);
            CardchaUi.DrawScaledText(b, Game1.dialogueFont, ModEntry.T("resonance.echo.unknown"), nameRect, Color.White * 0.88f, centerX: true, centerY: true, padding: 3, maxScale: 0.75f);

            Rectangle stateRect = new(r.X + 16, r.Bottom - 46, r.Width - 32, 32);
            string state = reached
                ? ModEntry.T("resonance.echo.awaiting")
                : ModEntry.T("resonance.echo.locked");
            CardchaUi.DrawScaledText(b, Game1.smallFont, state, stateRect, reached ? CardchaUi.Gold : Color.White * 0.48f, centerX: true, centerY: true, padding: 3, maxScale: 0.88f);
        }
    }

    private void DrawAbilities(SpriteBatch b, Color pink)
    {
        ChaChaSkillService? skills = ModEntry.StaticChaChaSkills;

        for (int i = 0; i < this.EntryButtons.Count && i < 4; i++)
        {
            Rectangle r = this.EntryButtons[i].bounds;
            string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(i);
            bool found = skills?.HasSkill(skillId) == true;
            bool active = skills?.IsActive(skillId) == true;
            int level = skills?.GetLevel(skillId) ?? 0;
            bool focused = this.currentlySnappedComponent?.myID == this.EntryButtons[i].myID;
            Color accent = i switch
            {
                0 => new Color(124, 238, 178),
                1 => new Color(131, 187, 255),
                2 => new Color(106, 223, 249),
                _ => new Color(255, 204, 91)
            };

            CardchaUi.DrawRoundedPanel(
                b,
                r,
                new Color(47, 35, 55),
                focused ? Color.White : found ? accent : new Color(111, 83, 117),
                thickness: focused ? 4 : 3,
                radius: 10
            );

            Rectangle sourceRect = new(r.X + 16, r.Y + 12, r.Width - 32, 34);
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                ModEntry.T("resonance.ability.region-source", new { region = i + 1, range = GetAbilityLevelRange(i) }),
                sourceRect,
                accent * (found ? 0.94f : 0.55f),
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.86f
            );

            int emblemSize = Math.Min(82, Math.Max(58, r.Height / 3));
            Rectangle emblem = new(r.Center.X - emblemSize / 2, r.Y + 53, emblemSize, emblemSize);
            CardchaUi.DrawRoundedPanel(b, emblem, new Color(28, 24, 35), accent * (found ? 0.65f : 0.28f), thickness: 2, radius: 22);
            if (this.SkillIconTexture is not null)
            {
                Rectangle source = new(i * 32, 0, 32, 32);
                b.Draw(this.SkillIconTexture, Inflate(emblem, -5), source, found ? Color.White : Color.White * 0.30f);
            }
            else
            {
                CardchaUi.DrawScaledText(b, Game1.dialogueFont, "?", emblem, accent * (found ? 1f : 0.45f), centerX: true, centerY: true, padding: 7, maxScale: 0.8f);
            }

            Rectangle nameRect = new(r.X + 14, emblem.Bottom + 7, r.Width - 28, 31);
            CardchaUi.DrawScaledText(
                b,
                Game1.dialogueFont,
                ModEntry.T($"chacha.skill.{skillId}.name"),
                nameRect,
                found ? Color.White : Color.White * 0.64f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.70f
            );

            Rectangle infoRect = new(r.X + 17, nameRect.Bottom + 2, r.Width - 34, 28);
            string info = found
                ? ModEntry.T("resonance.ability.level", new { level, max = ChaChaSkillService.MaxSkillLevel })
                : ModEntry.T("resonance.ability.find-region", new { region = i + 1 });
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                info,
                infoRect,
                found ? accent : Color.White * 0.48f,
                centerX: true,
                centerY: true,
                padding: 2,
                maxScale: 0.80f
            );

            Rectangle bottomRect = new(r.X + 18, r.Bottom - 48, r.Width - 36, 36);
            string bottom = found
                ? active ? ModEntry.T("resonance.ability.active") : ModEntry.T("resonance.ability.select")
                : ModEntry.T("resonance.ability.normal-form");
            CardchaUi.DrawScaledText(
                b,
                Game1.smallFont,
                bottom,
                bottomRect,
                active ? CardchaUi.Gold : Color.White * 0.56f,
                centerX: true,
                centerY: true,
                padding: 3,
                maxScale: 0.76f
            );
        }
    }

    private static string GetAbilityLevelRange(int index)
        => index switch
        {
            0 => "0–20",
            1 => "21–40",
            2 => "41–60",
            _ => "61–80"
        };

    private void DrawSupportProgress(SpriteBatch b, Color pink)
    {
        if (this.EntryButtons.Count < 3)
            return;

        int discovered = this.DiscoveredCount;
        int total = CardRegistry.TargetBaseSetCount;
        (int hit, int hurt) = GetSupportProcRates(discovered);
        int recovery = 10 + Math.Clamp(discovered / 10, 0, 8);
        int nextSupport = GetNextMilestone(discovered, new[] { 20, 40, 60, 80 });
        int nextRecovery = GetNextMilestone(discovered, new[] { 10, 20, 30, 40, 50, 60, 70, 80 });

        this.DrawSupportBlock(
            b,
            this.EntryButtons[0],
            ModEntry.T("resonance.support.collection.title"),
            ModEntry.T("resonance.support.collection.body", new
            {
                current = discovered,
                total,
                next = nextSupport < 0 ? ModEntry.T("resonance.complete") : nextSupport.ToString()
            }),
            new Color(111, 81, 130),
            pink
        );

        this.DrawSupportBlock(
            b,
            this.EntryButtons[1],
            ModEntry.T("resonance.support.trigger.title"),
            ModEntry.T("resonance.support.trigger.body", new { hit, hurt }),
            new Color(89, 81, 125),
            pink
        );

        string recoveryNext = nextRecovery < 0 ? ModEntry.T("resonance.complete") : nextRecovery.ToString();
        this.DrawSupportBlock(
            b,
            this.EntryButtons[2],
            ModEntry.T("resonance.support.recovery.title"),
            ModEntry.T("resonance.support.recovery.body", new { recovery, next = recoveryNext }),
            new Color(99, 73, 112),
            pink
        );
    }

    private void DrawSupportBlock(
        SpriteBatch b,
        ClickableComponent component,
        string title,
        string body,
        Color fill,
        Color accent)
    {
        bool focused = this.currentlySnappedComponent?.myID == component.myID;
        CardchaUi.DrawRoundedPanel(b, component.bounds, fill, focused ? Color.White : accent * 0.58f, thickness: focused ? 4 : 2, radius: 13);

        Rectangle titleRect = new(component.bounds.X + 18, component.bounds.Y + 12, component.bounds.Width - 36, 32);
        CardchaUi.DrawScaledText(b, Game1.dialogueFont, title, titleRect, new Color(255, 222, 170), centerX: false, centerY: true, padding: 2, maxScale: 0.72f);

        Rectangle bodyRect = new(component.bounds.X + 20, titleRect.Bottom + 4, component.bounds.Width - 40, component.bounds.Bottom - titleRect.Bottom - 16);
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            body,
            bodyRect,
            Color.White * 0.88f,
            maxLines: 4,
            minScale: 0.62f,
            maxScale: 0.95f
        );
    }

    private static (int Hit, int Hurt) GetSupportProcRates(int discovered)
    {
        if (discovered >= 80) return (10, 5);
        if (discovered >= 60) return (8, 4);
        if (discovered >= 40) return (6, 3);
        if (discovered >= 20) return (4, 2);
        return (2, 1);
    }

    private static int GetNextMilestone(int discovered, IEnumerable<int> milestones)
    {
        foreach (int milestone in milestones)
        {
            if (discovered < milestone)
                return milestone;
        }
        return -1;
    }

    private string GetTabLabel(ResonanceTab tab)
        => tab switch
        {
            ResonanceTab.MythicEchoes => ModEntry.T("resonance.tab.echoes"),
            ResonanceTab.Abilities => ModEntry.T("resonance.tab.abilities"),
            ResonanceTab.SupportProgress => ModEntry.T("resonance.tab.support"),
            _ => string.Empty
        };

    private void TryLoadChaChaTexture()
    {
        if (ModEntry.StaticHelper is null)
            return;

        try
        {
            this.ChaChaTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_follow.png");
        }
        catch
        {
            this.ChaChaTexture = null;
        }

        try
        {
            this.ChaChaPortraitTexture = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_portrait.png");
        }
        catch
        {
            this.ChaChaPortraitTexture = null;
        }

        try
        {
            this.SkillIconTexture = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillIconsTextureAsset);
        }
        catch
        {
            this.SkillIconTexture = null;
        }
    }
}
