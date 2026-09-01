using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal enum AirshipUpgradeSystem
{
    Engine = 0,
    Navigation = 1,
    Hull = 2,
    Reactor = 3,
}

/// <summary>
/// Alpha.28.0.4.14 Airship infrastructure foundation.
/// Costs are intentionally provisional TEST values. This pass validates interaction,
/// Magic Dust spending, save persistence, and visible socket state before gameplay bonuses are balanced.
/// </summary>
internal sealed class AirshipUpgradeMenu : IClickableMenu
{
    internal const int MaxLevel = 3;

    private const int UpgradeButtonId = 200;
    private const int CloseButtonId = 201;
    private const int RowBaseId = 100;
    private const long NavigationDebounceMs = 140L;

    private readonly SaveService Save;
    private readonly ControllerProfileService Controller;
    private readonly ClickableComponent[] Rows = new ClickableComponent[4];
    private readonly ClickableComponent UpgradeButton;
    private readonly ClickableComponent CloseButton;

    private AirshipUpgradeSystem Selected;
    private string Status;
    private long LastNavigationAtMs;

    public AirshipUpgradeMenu(
        SaveService save,
        ControllerProfileService controller,
        AirshipUpgradeSystem initialSelection)
        : base(
            Game1.uiViewport.Width / 2 - Math.Min(1080, Game1.uiViewport.Width - 24) / 2,
            Game1.uiViewport.Height / 2 - Math.Min(700, Game1.uiViewport.Height - 24) / 2,
            Math.Min(1080, Game1.uiViewport.Width - 24),
            Math.Min(700, Game1.uiViewport.Height - 24),
            showUpperRightCloseButton: false)
    {
        this.Save = save;
        this.Controller = controller;
        this.Selected = initialSelection;
        this.Status = ModEntry.T("airship.upgrade.status.ready");

        int rowX = this.xPositionOnScreen + 44;
        int rowW = this.width - 88;
        int rowY = this.yPositionOnScreen + 136;
        int rowH = 100;
        int gap = 6;

        for (int i = 0; i < this.Rows.Length; i++)
        {
            this.Rows[i] = new ClickableComponent(
                new Rectangle(rowX, rowY + i * (rowH + gap), rowW, rowH),
                ((AirshipUpgradeSystem)i).ToString())
            {
                myID = RowBaseId + i,
                upNeighborID = i == 0 ? -1 : RowBaseId + i - 1,
                downNeighborID = i == this.Rows.Length - 1 ? UpgradeButtonId : RowBaseId + i + 1,
            };
        }

        this.UpgradeButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + this.width - 360, this.yPositionOnScreen + this.height - 78, 190, 48),
            "upgrade")
        {
            myID = UpgradeButtonId,
            upNeighborID = RowBaseId + this.Rows.Length - 1,
            leftNeighborID = CloseButtonId,
        };

        this.CloseButton = new ClickableComponent(
            new Rectangle(this.xPositionOnScreen + 42, this.yPositionOnScreen + this.height - 78, 150, 48),
            "close")
        {
            myID = CloseButtonId,
            upNeighborID = RowBaseId + this.Rows.Length - 1,
            rightNeighborID = UpgradeButtonId,
        };

        this.Rows[^1].downNeighborID = UpgradeButtonId;
        this.populateClickableComponentList();
        this.currentlySnappedComponent = this.Rows[(int)this.Selected];
        if (Game1.options.SnappyMenus)
            this.snapCursorToCurrentSnappedComponent();
    }

    internal static int GetTestCostForCurrentLevel(int currentLevel)
        => currentLevel switch
        {
            0 => 5,
            1 => 10,
            2 => 20,
            _ => 0,
        };

    public override void populateClickableComponentList()
    {
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        // Controller focus is intentionally row-only. Footer buttons remain mouse-clickable,
        // while controller Confirm upgrades the highlighted row and Cancel closes the menu.
        // This prevents Stardew's spatial snappy-menu resolver from disagreeing with Selected.
        this.allClickableComponents.AddRange(this.Rows);
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.Rows[(int)this.Selected];
        this.snapCursorToCurrentSnappedComponent();
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        for (int i = 0; i < this.Rows.Length; i++)
        {
            if (!this.Rows[i].containsPoint(x, y))
                continue;

            this.Select((AirshipUpgradeSystem)i, playSound: true);
            return;
        }

        if (this.UpgradeButton.containsPoint(x, y))
        {
            this.TryUpgradeSelected();
            return;
        }

        if (this.CloseButton.containsPoint(x, y))
            this.CloseMenu();
    }

    public override void receiveKeyPress(Keys key)
    {
        if (key == Keys.Escape)
        {
            this.CloseMenu();
            return;
        }

        if (key == Keys.Up)
        {
            this.TryMoveSelection(-1);
            return;
        }

        if (key == Keys.Down)
        {
            this.TryMoveSelection(1);
            return;
        }

        // This is a strictly vertical list. Horizontal input is consumed instead of
        // accidentally cycling rows or letting base snappy navigation choose a distant row.
        if (key is Keys.Left or Keys.Right)
            return;

        if (key is Keys.Enter or Keys.Space)
        {
            this.TryUpgradeSelected();
            return;
        }

        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if (this.Controller.IsExit(b) || this.Controller.IsDeselect(b))
        {
            this.CloseMenu();
            return;
        }

        if (b is Buttons.DPadUp or Buttons.LeftThumbstickUp)
        {
            this.TryMoveSelection(-1);
            return;
        }

        if (b is Buttons.DPadDown or Buttons.LeftThumbstickDown)
        {
            this.TryMoveSelection(1);
            return;
        }

        if (b is Buttons.DPadLeft or Buttons.DPadRight or Buttons.LeftThumbstickLeft or Buttons.LeftThumbstickRight)
            return;

        if (this.Controller.IsConfirm(b))
        {
            this.TryUpgradeSelected();
            return;
        }

        if (this.Controller.IsFavorite(b))
            return;

        base.receiveGamePadButton(b);
    }

    private void TryMoveSelection(int delta)
    {
        long now = Environment.TickCount64;
        if (now - this.LastNavigationAtMs < NavigationDebounceMs)
            return;

        this.LastNavigationAtMs = now;
        int next = Math.Clamp((int)this.Selected + Math.Sign(delta), 0, this.Rows.Length - 1);
        if (next == (int)this.Selected)
            return;

        this.Select((AirshipUpgradeSystem)next, playSound: true);
    }

    private void Select(AirshipUpgradeSystem system, bool playSound)
    {
        this.Selected = system;
        this.Status = ModEntry.T("airship.upgrade.status.ready");
        this.currentlySnappedComponent = this.Rows[(int)system];
        if (Game1.options.SnappyMenus)
            this.snapCursorToCurrentSnappedComponent();
        if (playSound)
            Game1.playSound("shiny4");
    }

    private void TryUpgradeSelected()
    {
        int level = this.GetLevel(this.Selected);
        if (level >= MaxLevel)
        {
            this.Status = ModEntry.T("airship.upgrade.status.max");
            Game1.playSound("cancel");
            return;
        }

        int cost = GetTestCostForCurrentLevel(level);
        if (this.Save.Data.SuspiciousDust < cost)
        {
            this.Status = ModEntry.T(
                "airship.upgrade.status.not_enough",
                new { cost, dust = this.Save.Data.SuspiciousDust }
            );
            Game1.playSound("cancel");
            return;
        }

        this.Save.Data.SuspiciousDust -= cost;
        this.SetLevel(this.Selected, level + 1);
        this.Save.Save();
        this.Status = ModEntry.T(
            "airship.upgrade.status.success",
            new
            {
                system = this.GetSystemName(this.Selected),
                level = level + 1,
                cost,
            }
        );
        Game1.playSound("discoverMineral");
    }

    private int GetLevel(AirshipUpgradeSystem system)
        => system switch
        {
            AirshipUpgradeSystem.Engine => this.Save.Data.AirshipEngineLevel,
            AirshipUpgradeSystem.Navigation => this.Save.Data.AirshipNavigationLevel,
            AirshipUpgradeSystem.Hull => this.Save.Data.AirshipHullLevel,
            AirshipUpgradeSystem.Reactor => this.Save.Data.AirshipReactorLevel,
            _ => 0,
        };

    private void SetLevel(AirshipUpgradeSystem system, int level)
    {
        level = Math.Clamp(level, 0, MaxLevel);
        switch (system)
        {
            case AirshipUpgradeSystem.Engine:
                this.Save.Data.AirshipEngineLevel = level;
                break;
            case AirshipUpgradeSystem.Navigation:
                this.Save.Data.AirshipNavigationLevel = level;
                break;
            case AirshipUpgradeSystem.Hull:
                this.Save.Data.AirshipHullLevel = level;
                break;
            case AirshipUpgradeSystem.Reactor:
                this.Save.Data.AirshipReactorLevel = level;
                break;
        }
    }

    private string GetSystemName(AirshipUpgradeSystem system)
        => ModEntry.T($"airship.upgrade.system.{GetSystemToken(system)}.name");

    private static string GetSystemToken(AirshipUpgradeSystem system)
        => system switch
        {
            AirshipUpgradeSystem.Engine => "engine",
            AirshipUpgradeSystem.Navigation => "navigation",
            AirshipUpgradeSystem.Hull => "hull",
            AirshipUpgradeSystem.Reactor => "reactor",
            _ => "engine",
        };

    private void CloseMenu()
    {
        Game1.playSound("bigDeSelect");
        Game1.exitActiveMenu();
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(
            Game1.fadeToBlackRect,
            Game1.graphics.GraphicsDevice.Viewport.Bounds,
            Color.Black * 0.74f
        );

        Rectangle panel = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);
        CardchaUi.DrawInsetPanel(
            b,
            panel,
            new Color(43, 35, 62),
            new Color(155, 111, 188),
            5,
            8
        );

        Rectangle inner = new(panel.X + 22, panel.Y + 22, panel.Width - 44, panel.Height - 44);
        CardchaUi.DrawInsetPanel(
            b,
            inner,
            new Color(231, 220, 241),
            new Color(120, 86, 142),
            3,
            5
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("airship.upgrade.title"),
            new Rectangle(inner.X + 28, inner.Y + 12, inner.Width - 56, 44),
            new Color(61, 44, 76),
            centerX: true,
            centerY: true,
            maxScale: 1.10f
        );

        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("airship.upgrade.dust", new { amount = this.Save.Data.SuspiciousDust }),
            new Rectangle(inner.X + 34, inner.Y + 62, inner.Width / 2 - 40, 34),
            new Color(82, 58, 101),
            centerY: true,
            maxScale: 1.20f
        );

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            ModEntry.T("airship.upgrade.test_notice"),
            new Rectangle(inner.Center.X - 12, inner.Y + 58, inner.Width / 2 - 28, 44),
            new Color(122, 74, 83),
            maxLines: 2,
            minScale: 0.70f,
            centerX: false,
            maxScale: 1.00f,
            centerY: true
        );

        for (int i = 0; i < this.Rows.Length; i++)
            this.DrawSystemRow(b, (AirshipUpgradeSystem)i, this.Rows[i], this.Selected == (AirshipUpgradeSystem)i);

        int selectedLevel = this.GetLevel(this.Selected);
        bool canUpgrade = selectedLevel < MaxLevel && this.Save.Data.SuspiciousDust >= GetTestCostForCurrentLevel(selectedLevel);
        CardchaUi.DrawButton(
            b,
            this.UpgradeButton,
            selectedLevel >= MaxLevel
                ? ModEntry.T("airship.upgrade.button.max")
                : ModEntry.T("airship.upgrade.button.upgrade"),
            new Color(102, 70, 142),
            enabled: canUpgrade,
            textScale: 1.10f,
            textPadding: 4
        );
        CardchaUi.DrawButton(
            b,
            this.CloseButton,
            ModEntry.T("airship.upgrade.button.close"),
            new Color(114, 77, 84),
            enabled: true,
            textScale: 1.10f,
            textPadding: 4
        );

        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            this.Status,
            new Rectangle(inner.X + 190, inner.Bottom - 58, inner.Width - 560, 42),
            new Color(71, 61, 80),
            maxLines: 2,
            minScale: 0.72f,
            centerX: true,
            maxScale: 1.06f,
            centerY: true
        );

        if (this.currentlySnappedComponent is not null)
            CardchaUi.DrawFocus(b, this.currentlySnappedComponent.bounds);

        this.drawMouse(b);
    }

    private void DrawSystemRow(
        SpriteBatch b,
        AirshipUpgradeSystem system,
        ClickableComponent component,
        bool selected)
    {
        Rectangle row = component.bounds;
        Color fill = selected ? new Color(242, 229, 249) : new Color(247, 240, 250);
        Color border = selected ? new Color(156, 101, 192) : new Color(157, 137, 169);
        b.Draw(Game1.staminaRect, row, fill * 0.96f);
        CardchaUi.DrawBorder(b, row, border, selected ? 3 : 2);

        Rectangle icon = new(row.X + 12, row.Y + 12, 68, 68);
        b.Draw(Game1.staminaRect, icon, new Color(48, 39, 66));
        CardchaUi.DrawBorder(b, icon, GetSystemColor(system), 2);
        this.DrawSystemGlyph(b, icon, system);

        int level = this.GetLevel(system);
        string token = GetSystemToken(system);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T($"airship.upgrade.system.{token}.name"),
            new Rectangle(row.X + 94, row.Y + 8, row.Width - 310, 32),
            new Color(64, 46, 78),
            centerY: true,
            maxScale: 1.30f
        );
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            ModEntry.T($"airship.upgrade.system.{token}.desc"),
            new Rectangle(row.X + 94, row.Y + 40, row.Width - 310, 48),
            new Color(88, 76, 96),
            maxLines: 2,
            minScale: 0.82f,
            centerX: false,
            maxScale: 1.06f,
            centerY: true
        );

        Rectangle levelBox = new(row.Right - 242, row.Y + 12, 104, 68);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("airship.upgrade.level", new { level, max = MaxLevel }),
            new Rectangle(levelBox.X, levelBox.Y, levelBox.Width, 28),
            new Color(69, 53, 83),
            centerX: true,
            centerY: true,
            maxScale: 1.02f
        );
        for (int pip = 0; pip < MaxLevel; pip++)
        {
            Rectangle p = new(levelBox.X + 12 + pip * 29, levelBox.Y + 39, 19, 12);
            b.Draw(Game1.staminaRect, p, pip < level ? GetSystemColor(system) : new Color(174, 164, 181));
            CardchaUi.DrawBorder(b, p, new Color(82, 67, 94), 1);
        }

        string costText = level >= MaxLevel
            ? ModEntry.T("airship.upgrade.cost.max")
            : ModEntry.T("airship.upgrade.cost", new { cost = GetTestCostForCurrentLevel(level) });
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            costText,
            new Rectangle(row.Right - 132, row.Y + 18, 120, 54),
            level >= MaxLevel ? new Color(92, 113, 85) : new Color(114, 78, 91),
            centerX: true,
            centerY: true,
            maxScale: 1.00f
        );
    }

    private void DrawSystemGlyph(SpriteBatch b, Rectangle box, AirshipUpgradeSystem system)
    {
        Color color = GetSystemColor(system);
        int cx = box.Center.X;
        int cy = box.Center.Y;
        switch (system)
        {
            case AirshipUpgradeSystem.Engine:
                b.Draw(Game1.staminaRect, new Rectangle(cx - 22, cy - 6, 44, 12), color);
                b.Draw(Game1.staminaRect, new Rectangle(cx - 6, cy - 22, 12, 44), color * 0.82f);
                break;
            case AirshipUpgradeSystem.Navigation:
                b.Draw(Game1.staminaRect, new Rectangle(cx - 4, cy - 26, 8, 52), color);
                b.Draw(Game1.staminaRect, new Rectangle(cx - 26, cy - 4, 52, 8), color * 0.82f);
                break;
            case AirshipUpgradeSystem.Hull:
                b.Draw(Game1.staminaRect, new Rectangle(cx - 24, cy - 18, 48, 10), color);
                b.Draw(Game1.staminaRect, new Rectangle(cx - 18, cy - 8, 36, 24), color * 0.86f);
                break;
            case AirshipUpgradeSystem.Reactor:
                b.Draw(Game1.staminaRect, new Rectangle(cx - 16, cy - 16, 32, 32), color * 0.62f);
                b.Draw(Game1.staminaRect, new Rectangle(cx - 8, cy - 24, 16, 48), color);
                break;
        }
    }

    private static Color GetSystemColor(AirshipUpgradeSystem system)
        => system switch
        {
            AirshipUpgradeSystem.Engine => new Color(247, 179, 82),
            AirshipUpgradeSystem.Navigation => new Color(92, 207, 232),
            AirshipUpgradeSystem.Hull => new Color(127, 151, 220),
            AirshipUpgradeSystem.Reactor => new Color(205, 113, 232),
            _ => new Color(180, 160, 200),
        };
}
