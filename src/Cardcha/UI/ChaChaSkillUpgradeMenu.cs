using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

/// <summary>
/// Airship-only upgrade screen for ChaCha's four normal-form support skills.
/// Skill discovery still happens in the custom regions; this station only upgrades skills
/// already found by the player, using the matching physical region material + Magic Dust.
/// </summary>
internal sealed class ChaChaSkillUpgradeMenu : IClickableMenu
{
    private const int BackId = 100;
    private const int SkillBaseId = 200;

    private readonly SaveService Save;
    private readonly ChaChaSkillService Skills;
    private readonly ChaChaSkillMaterialService Materials;
    private readonly ControllerProfileService Controller;

    private readonly Rectangle Outer;
    private readonly Rectangle Header;
    private readonly Rectangle Content;
    private readonly ClickableComponent BackButton;
    private readonly List<ClickableComponent> SkillButtons = new();

    private Texture2D? SkillIcons;
    private Texture2D? MaterialIcons;
    private string Status;
    private bool LastInputWasController;

    public ChaChaSkillUpgradeMenu(
        SaveService save,
        ChaChaSkillService skills,
        ChaChaSkillMaterialService materials,
        ControllerProfileService controller)
        : base(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height, showUpperRightCloseButton: false)
    {
        this.Save = save;
        this.Skills = skills;
        this.Materials = materials;
        this.Controller = controller;
        this.Status = ModEntry.T("chacha.station.status.ready");

        int vw = Game1.uiViewport.Width;
        int vh = Game1.uiViewport.Height;
        int w = Math.Min(1180, Math.Max(760, vw - 54));
        int h = Math.Min(760, Math.Max(560, vh - 60));
        int x = vw / 2 - w / 2;
        int y = vh / 2 - h / 2;
        this.Outer = new Rectangle(x, y, w, h);
        this.Header = new Rectangle(x + 26, y + 20, w - 52, 72);
        this.Content = new Rectangle(x + 28, this.Header.Bottom + 18, w - 56, h - 154);
        this.BackButton = new ClickableComponent(new Rectangle(this.Header.X, this.Header.Y + 12, 112, 44), "back") { myID = BackId };

        int gap = 14;
        int cardW = (this.Content.Width - gap) / 2;
        int cardH = (this.Content.Height - gap) / 2;
        for (int i = 0; i < 4; i++)
        {
            int col = i % 2;
            int row = i / 2;
            Rectangle r = new(
                this.Content.X + col * (cardW + gap),
                this.Content.Y + row * (cardH + gap),
                cardW,
                cardH
            );
            this.SkillButtons.Add(new ClickableComponent(r, $"skill-{i}") { myID = SkillBaseId + i });
        }

        this.TryLoadTextures();
        this.ConfigureNeighbors();
        this.populateClickableComponentList();
        if (Game1.options.SnappyMenus)
            this.snapToDefaultClickableComponent();
    }

    public override void snapToDefaultClickableComponent()
    {
        this.currentlySnappedComponent = this.SkillButtons[0];
        this.snapCursorToCurrentSnappedComponent();
    }

    public override void populateClickableComponentList()
    {
        base.populateClickableComponentList();
        this.allClickableComponents.Clear();
        this.allClickableComponents.Add(this.BackButton);
        this.allClickableComponents.AddRange(this.SkillButtons);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        this.LastInputWasController = true;
        if (this.Controller.IsExit(b))
        {
            this.Close();
            return;
        }

        if (this.Controller.IsConfirm(b) && this.currentlySnappedComponent is not null)
        {
            int id = this.currentlySnappedComponent.myID;
            if (id == BackId)
                this.Close();
            else if (id >= SkillBaseId && id < SkillBaseId + 4)
                this.TryUpgrade(id - SkillBaseId);
            return;
        }

        base.receiveGamePadButton(b);
    }

    public override void receiveKeyPress(Keys key)
    {
        this.LastInputWasController = false;
        if (key == Keys.Escape)
        {
            this.Close();
            return;
        }

        if ((key == Keys.Enter || key == Keys.Space) && this.currentlySnappedComponent is not null)
        {
            int id = this.currentlySnappedComponent.myID;
            if (id >= SkillBaseId && id < SkillBaseId + 4)
                this.TryUpgrade(id - SkillBaseId);
            return;
        }

        base.receiveKeyPress(key);
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        this.LastInputWasController = false;
        if (this.BackButton.bounds.Contains(x, y))
        {
            this.Close();
            return;
        }

        for (int i = 0; i < this.SkillButtons.Count; i++)
        {
            if (this.SkillButtons[i].bounds.Contains(x, y))
            {
                this.TryUpgrade(i);
                return;
            }
        }

        base.receiveLeftClick(x, y, playSound);
    }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect, new Rectangle(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height), Color.Black * 0.84f);

        Color deep = new(35, 25, 43);
        Color panel = new(52, 38, 60);
        Color gold = new(236, 176, 76);
        Color pink = new(238, 105, 181);
        CardchaUi.DrawRoundedPanel(b, this.Outer, deep, gold, thickness: 4, radius: 18);
        CardchaUi.DrawCornerOrnaments(b, this.Outer, gold * 0.72f);
        CardchaUi.DrawButton(b, this.BackButton, ModEntry.T("chacha.station.back"), new Color(83, 59, 84), enabled: true, textScale: 0.95f);

        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T("chacha.station.title"),
            new Rectangle(this.Header.X + 126, this.Header.Y, this.Header.Width - 252, 40),
            new Color(255, 219, 157),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.92f
        );
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("chacha.station.subtitle", new { dust = Math.Max(0, this.Save.Data.SuspiciousDust) }),
            new Rectangle(this.Header.X + 126, this.Header.Y + 40, this.Header.Width - 252, 26),
            Color.White * 0.76f,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.92f
        );

        for (int i = 0; i < 4; i++)
            this.DrawSkillCard(b, i, panel, pink, gold);

        Rectangle statusRect = new(this.Outer.X + 40, this.Outer.Bottom - 43, this.Outer.Width - 80, 28);
        CardchaUi.DrawScaledText(b, Game1.smallFont, this.Status, statusRect, Color.White * 0.86f, centerX: true, centerY: true, padding: 2, maxScale: 0.94f);

        this.drawMouse(b);
    }

    private void DrawSkillCard(SpriteBatch b, int index, Color panel, Color pink, Color gold)
    {
        ClickableComponent button = this.SkillButtons[index];
        Rectangle r = button.bounds;
        string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(index);
        bool found = this.Skills.HasSkill(skillId);
        int level = this.Skills.GetLevel(skillId);
        bool maxed = found && level >= ChaChaSkillService.MaxSkillLevel;
        bool focused = this.currentlySnappedComponent?.myID == button.myID;

        Color accent = index switch
        {
            0 => new Color(129, 245, 184),
            1 => new Color(135, 190, 255),
            2 => new Color(115, 220, 255),
            _ => new Color(255, 205, 93)
        };
        CardchaUi.DrawRoundedPanel(
            b,
            r,
            panel,
            focused ? Color.White : found ? accent : new Color(104, 83, 111),
            thickness: focused ? 4 : 3,
            radius: 13
        );

        int iconSize = Math.Clamp(r.Height / 3, 72, 104);
        Rectangle skillIcon = new(r.X + 18, r.Y + 18, iconSize, iconSize);
        Rectangle materialIcon = new(r.Right - iconSize - 18, r.Y + 18, iconSize, iconSize);
        DrawIcon(b, this.SkillIcons, index, skillIcon, found ? Color.White : Color.White * 0.24f);
        DrawIcon(b, this.MaterialIcons, index, materialIcon, found ? Color.White : Color.White * 0.34f);

        Rectangle title = new(skillIcon.Right + 12, r.Y + 18, materialIcon.X - skillIcon.Right - 24, 38);
        CardchaUi.DrawScaledText(
            b,
            Game1.dialogueFont,
            ModEntry.T($"chacha.skill.{skillId}.name"),
            title,
            found ? Color.White : Color.White * 0.62f,
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.72f
        );

        Rectangle regionRect = new(title.X, title.Bottom + 2, title.Width, 30);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("chacha.station.region", new { region = index + 1, range = GetLevelRange(index) }),
            regionRect,
            accent * (found ? 0.94f : 0.52f),
            centerX: true,
            centerY: true,
            padding: 1,
            maxScale: 0.84f
        );

        Rectangle levelRect = new(r.X + 20, skillIcon.Bottom + 12, r.Width - 40, 34);
        string levelText = found
            ? ModEntry.T("chacha.station.level", new { level, max = ChaChaSkillService.MaxSkillLevel })
            : ModEntry.T("chacha.station.locked");
        CardchaUi.DrawScaledText(b, Game1.dialogueFont, levelText, levelRect, found ? gold : Color.White * 0.45f, centerX: true, centerY: true, padding: 2, maxScale: 0.68f);

        string materialId = ChaChaSkillMaterialService.GetMaterialIdForSkill(skillId);
        int count = this.Materials.CountMaterial(materialId);
        Rectangle materialText = new(r.X + 20, levelRect.Bottom + 4, r.Width - 40, 28);
        CardchaUi.DrawScaledText(
            b,
            Game1.smallFont,
            ModEntry.T("chacha.station.material-count", new { name = ModEntry.T($"item.chacha-material.{index + 1}.name"), count }),
            materialText,
            Color.White * (found ? 0.84f : 0.48f),
            centerX: true,
            centerY: true,
            padding: 2,
            maxScale: 0.82f
        );

        Rectangle costRect = new(r.X + 20, materialText.Bottom + 3, r.Width - 40, Math.Max(30, r.Bottom - materialText.Bottom - 16));
        string cost;
        if (!found)
        {
            cost = ModEntry.T("chacha.station.find-first", new { region = index + 1 });
        }
        else if (maxed)
        {
            cost = ModEntry.T("chacha.station.max");
        }
        else
        {
            ChaChaUpgradeQuote quote = this.Materials.GetUpgradeQuote(skillId)!.Value;
            cost = ModEntry.T("chacha.station.upgrade-cost", new
            {
                next = quote.NextLevel,
                material = quote.MaterialCost,
                dust = quote.DustCost
            });
        }
        CardchaUi.DrawAutoFitWrappedText(
            b,
            Game1.smallFont,
            cost,
            costRect,
            maxed ? gold : found ? Color.White * 0.90f : Color.White * 0.48f,
            maxLines: 2,
            minScale: 0.60f,
            maxScale: 0.88f,
            centerX: true
        );
    }

    private void TryUpgrade(int index)
    {
        string skillId = ChaChaSkillMaterialService.GetSkillIdForIndex(index);
        bool ok = this.Materials.TryUpgrade(skillId, out string status);
        this.Status = status;
        if (!ok)
            Game1.playSound("cancel");
    }

    private void ConfigureNeighbors()
    {
        this.BackButton.downNeighborID = SkillBaseId;
        this.BackButton.rightNeighborID = SkillBaseId;
        for (int i = 0; i < this.SkillButtons.Count; i++)
        {
            int col = i % 2;
            int row = i / 2;
            ClickableComponent c = this.SkillButtons[i];
            c.leftNeighborID = col == 0 ? BackId : SkillBaseId + i - 1;
            c.rightNeighborID = col == 1 ? BackId : SkillBaseId + i + 1;
            c.upNeighborID = row == 0 ? BackId : SkillBaseId + i - 2;
            c.downNeighborID = row == 1 ? BackId : SkillBaseId + i + 2;
        }
    }

    private void TryLoadTextures()
    {
        try
        {
            this.SkillIcons = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillIconsTextureAsset);
        }
        catch
        {
            this.SkillIcons = null;
        }

        try
        {
            this.MaterialIcons = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillMaterialsTextureAsset);
        }
        catch
        {
            this.MaterialIcons = null;
        }
    }

    private static void DrawIcon(SpriteBatch b, Texture2D? texture, int index, Rectangle dest, Color tint)
    {
        if (texture is null)
        {
            CardchaUi.DrawRoundedPanel(b, dest, new Color(29, 25, 37), tint * 0.40f, thickness: 2, radius: 12);
            CardchaUi.DrawScaledText(b, Game1.dialogueFont, "?", dest, tint, centerX: true, centerY: true, padding: 7, maxScale: 0.8f);
            return;
        }

        Rectangle source = new(index * 32, 0, 32, 32);
        b.Draw(texture, dest, source, tint);
    }

    private static string GetLevelRange(int index)
        => index switch
        {
            0 => "0–20",
            1 => "21–40",
            2 => "41–60",
            _ => "61–80"
        };

    private void Close()
    {
        Game1.playSound("bigDeSelect");
        Game1.exitActiveMenu();
    }
}
