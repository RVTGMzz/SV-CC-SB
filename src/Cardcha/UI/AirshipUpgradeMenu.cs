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

/// <summary>0648B: one physical station, one upgrade system, one panel.</summary>
internal sealed class AirshipUpgradeMenu : IClickableMenu
{
    internal const int MaxLevel = 3;
    private readonly SaveService Save;
    private readonly ControllerProfileService Controller;
    private readonly AirshipUpgradeSystem System;
    private readonly Rectangle UpgradeButton;
    private readonly Rectangle CloseButton;
    private string Status;

    public AirshipUpgradeMenu(SaveService save, ControllerProfileService controller, AirshipUpgradeSystem system)
        : base(
            Game1.uiViewport.Width/2 - Math.Min(880, Game1.uiViewport.Width-24)/2,
            Game1.uiViewport.Height/2 - Math.Min(560, Game1.uiViewport.Height-24)/2,
            Math.Min(880, Game1.uiViewport.Width-24),
            Math.Min(560, Game1.uiViewport.Height-24),
            showUpperRightCloseButton:false)
    {
        this.Save=save;
        this.Controller=controller;
        this.System=system;
        this.Status=ModEntry.T("airship.upgrade.status.ready");
        this.UpgradeButton=new Rectangle(this.xPositionOnScreen+this.width-286,this.yPositionOnScreen+this.height-80,210,48);
        this.CloseButton=new Rectangle(this.xPositionOnScreen+42,this.yPositionOnScreen+this.height-80,160,48);
    }

    internal static int GetTestCostForCurrentLevel(int currentLevel)
        => currentLevel switch { 0=>5, 1=>10, 2=>20, _=>0 };

    public override void receiveLeftClick(int x,int y,bool playSound=true)
    {
        if(this.UpgradeButton.Contains(x,y)){ this.TryUpgrade(); return; }
        if(this.CloseButton.Contains(x,y)) this.CloseMenu();
    }

    public override void receiveKeyPress(Keys key)
    {
        if(key==Keys.Escape){ this.CloseMenu(); return; }
        if(key is Keys.Enter or Keys.Space){ this.TryUpgrade(); return; }
        base.receiveKeyPress(key);
    }

    public override void receiveGamePadButton(Buttons b)
    {
        if(this.Controller.IsExit(b)||this.Controller.IsDeselect(b)){ this.CloseMenu(); return; }
        if(this.Controller.IsConfirm(b)){ this.TryUpgrade(); return; }
        base.receiveGamePadButton(b);
    }

    private void TryUpgrade()
    {
        int level=this.GetLevel();
        if(level>=MaxLevel){ this.Status=ModEntry.T("airship.upgrade.status.max"); Game1.playSound("cancel"); return; }
        int cost=GetTestCostForCurrentLevel(level);
        if(this.Save.Data.SuspiciousDust<cost)
        {
            this.Status=ModEntry.T("airship.upgrade.status.not_enough",new{cost,dust=this.Save.Data.SuspiciousDust});
            Game1.playSound("cancel"); return;
        }
        this.Save.Data.SuspiciousDust-=cost;
        this.SetLevel(level+1);
        this.Save.Save();
        this.Status=ModEntry.T("airship.upgrade.status.success",new{system=this.GetSystemName(),level=level+1,cost});
        Game1.playSound("discoverMineral");
    }

    private int GetLevel()=>this.System switch
    {
        AirshipUpgradeSystem.Engine=>this.Save.Data.AirshipEngineLevel,
        AirshipUpgradeSystem.Navigation=>this.Save.Data.AirshipNavigationLevel,
        AirshipUpgradeSystem.Hull=>this.Save.Data.AirshipHullLevel,
        AirshipUpgradeSystem.Reactor=>this.Save.Data.AirshipReactorLevel,
        _=>0,
    };

    private void SetLevel(int level)
    {
        level=Math.Clamp(level,0,MaxLevel);
        switch(this.System)
        {
            case AirshipUpgradeSystem.Engine:this.Save.Data.AirshipEngineLevel=level;break;
            case AirshipUpgradeSystem.Navigation:this.Save.Data.AirshipNavigationLevel=level;break;
            case AirshipUpgradeSystem.Hull:this.Save.Data.AirshipHullLevel=level;break;
            case AirshipUpgradeSystem.Reactor:this.Save.Data.AirshipReactorLevel=level;break;
        }
    }

    private string Token()=>this.System switch
    {
        AirshipUpgradeSystem.Engine=>"engine",
        AirshipUpgradeSystem.Navigation=>"navigation",
        AirshipUpgradeSystem.Hull=>"hull",
        AirshipUpgradeSystem.Reactor=>"reactor",
        _=>"engine",
    };
    private string GetSystemName()=>ModEntry.T($"airship.upgrade.system.{this.Token()}.name");
    private string GetSystemDesc()=>ModEntry.T($"airship.upgrade.system.{this.Token()}.desc");

    private void CloseMenu(){ Game1.playSound("bigDeSelect"); Game1.exitActiveMenu(); }

    public override void draw(SpriteBatch b)
    {
        b.Draw(Game1.fadeToBlackRect,Game1.graphics.GraphicsDevice.Viewport.Bounds,Color.Black*0.70f);
        Rectangle panel=new(this.xPositionOnScreen,this.yPositionOnScreen,this.width,this.height);
        CardchaUi.DrawInsetPanel(b,panel,new Color(53,42,61),new Color(178,126,84),5,8);
        Rectangle inner=new(panel.X+22,panel.Y+22,panel.Width-44,panel.Height-44);
        CardchaUi.DrawInsetPanel(b,inner,new Color(238,224,204),new Color(126,83,62),3,5);

        string title=ModEntry.T("airship.upgrade.title");
        Vector2 ts=Game1.dialogueFont.MeasureString(title);
        b.DrawString(Game1.dialogueFont,title,new Vector2(inner.Center.X-ts.X/2f,inner.Y+18),new Color(67,47,55));

        string name=this.GetSystemName();
        Vector2 ns=Game1.dialogueFont.MeasureString(name);
        b.DrawString(Game1.dialogueFont,name,new Vector2(inner.Center.X-ns.X/2f,inner.Y+94),new Color(75,53,65));

        Rectangle card=new(inner.X+60,inner.Y+150,inner.Width-120,178);
        CardchaUi.DrawInsetPanel(b,card,new Color(224,207,187),new Color(145,99,69),2,4);
        int level=this.GetLevel();
        int cost=GetTestCostForCurrentLevel(level);
        b.DrawString(Game1.smallFont,this.GetSystemDesc(),new Vector2(card.X+24,card.Y+22),new Color(74,57,58));
        b.DrawString(Game1.smallFont,ModEntry.T("airship.upgrade.level",new{level,max=MaxLevel}),new Vector2(card.X+24,card.Y+84),new Color(84,60,67));
        b.DrawString(Game1.smallFont,ModEntry.T("airship.upgrade.dust",new{amount=this.Save.Data.SuspiciousDust}),new Vector2(card.X+24,card.Y+116),new Color(84,60,67));
        string costText=level>=MaxLevel?ModEntry.T("airship.upgrade.cost.max"):ModEntry.T("airship.upgrade.cost",new{cost});
        b.DrawString(Game1.smallFont,costText,new Vector2(card.Right-220,card.Y+100),new Color(99,67,70));

        b.DrawString(Game1.smallFont,this.Status,new Vector2(inner.X+60,inner.Bottom-118),new Color(75,58,67));
        DrawButton(b,this.CloseButton,ModEntry.T("airship.upgrade.button.close"),true);
        DrawButton(b,this.UpgradeButton,level<MaxLevel?ModEntry.T("airship.upgrade.button.upgrade"):ModEntry.T("airship.upgrade.button.max"),level<MaxLevel);
        drawMouse(b);
    }

    private static void DrawButton(SpriteBatch b,Rectangle r,string text,bool enabled)
    {
        Color fill=enabled?new Color(126,83,70):new Color(116,108,105);
        CardchaUi.DrawInsetPanel(b,r,fill,new Color(72,52,55),2,3);
        Vector2 s=Game1.smallFont.MeasureString(text);
        b.DrawString(Game1.smallFont,text,new Vector2(r.Center.X-s.X/2f,r.Center.Y-s.Y/2f),Color.White*0.94f);
    }
}
