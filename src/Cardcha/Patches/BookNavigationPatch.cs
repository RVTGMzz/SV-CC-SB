using Cardcha.UI;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.Patches;

internal static class BookNavigationPatch
{
    private static CardchaBookTabService? Service;
    private static Texture2D? CoverIcon;
    private static bool CoverIconChecked;

    public static void Apply(
        Harmony harmony,
        CardchaBookTabService service)
    {
        Service = service;

        System.Reflection.MethodInfo? target =
            AccessTools.Method(
                typeof(IClickableMenu),
                nameof(IClickableMenu.applyMovementKey),
                new[] { typeof(int) }
            );

        if (target is null)
            throw new InvalidOperationException(
                "Could not find IClickableMenu.applyMovementKey(int)."
            );

        harmony.Patch(
            target,
            prefix: new HarmonyMethod(
                typeof(BookNavigationPatch),
                nameof(Prefix)
            )
        );

        // v0.2 visual pass: preserve all of the mature Book-tab attachment/navigation logic,
        // but replace only its drawing with the approved closed leather Cardcha journal cover.
        System.Reflection.MethodInfo? drawTab =
            AccessTools.Method(typeof(CardchaBookTabService), "DrawTab");

        if (drawTab is not null)
        {
            harmony.Patch(
                drawTab,
                prefix: new HarmonyMethod(
                    typeof(BookNavigationPatch),
                    nameof(DrawTabPrefix)
                )
            );
        }
        else
        {
            ModEntry.StaticMonitor?.Log(
                "Cardcha v0.2: couldn't find CardchaBookTabService.DrawTab; keeping the legacy Book icon safely.",
                LogLevel.Warn
            );
        }
    }

    private static bool Prefix(
        IClickableMenu __instance,
        int direction)
    {
        try
        {
            if (Service?.TryHandleMovementKey(
                    __instance,
                    direction
                ) == true)
            {
                return false;
            }
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.LogOnce(
                $"Cardcha Book movement intercept failed safely: {ex}",
                LogLevel.Warn
            );
        }

        return true;
    }

    private static bool DrawTabPrefix(
        SpriteBatch b,
        IClickableMenu graphOwner,
        ClickableComponent ___BookTab)
    {
        Texture2D? texture = TryGetCoverIcon();
        if (texture is null)
            return true;

        Rectangle r = ___BookTab.bounds;
        bool focused = graphOwner.currentlySnappedComponent?.myID == ___BookTab.myID;
        Point cursor = CardchaUi.GetUiMousePoint();
        bool hovered = r.Contains(cursor);

        Rectangle shadow = new(r.X + 3, r.Y + 4, r.Width, r.Height);
        b.Draw(Game1.staminaRect, shadow, new Color(49, 30, 24) * 0.58f);

        Rectangle outer = focused || hovered
            ? new Rectangle(r.X - 2, r.Y - 2, r.Width + 4, r.Height + 4)
            : r;

        b.Draw(Game1.staminaRect, outer, focused ? Color.White : CardchaUi.Gold * 0.95f);
        Rectangle face = new(outer.X + 3, outer.Y + 3, Math.Max(1, outer.Width - 6), Math.Max(1, outer.Height - 6));
        b.Draw(texture, face, Color.White);
        CardchaUi.DrawBorder(b, outer, focused ? Color.White : new Color(102, 55, 36), focused ? 3 : 2);

        if (focused)
            CardchaUi.DrawFocus(b, r);

        if (hovered)
            DrawTooltip(b, ModEntry.T("booktab.tooltip"));

        return false;
    }

    private static Texture2D? TryGetCoverIcon()
    {
        if (CoverIconChecked)
            return CoverIcon;

        CoverIconChecked = true;
        try
        {
            CoverIcon = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/binder_cover_icon.png");
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.LogOnce(
                $"Cardcha v0.2 couldn't load binder_cover_icon.png; keeping legacy Book icon. {ex.Message}",
                LogLevel.Warn
            );
        }

        return CoverIcon;
    }

    private static void DrawTooltip(SpriteBatch b, string text)
    {
        Point cursor = CardchaUi.GetUiMousePoint();
        Vector2 size = Game1.smallFont.MeasureString(text);
        const int pad = 8;

        int x = Math.Min(
            cursor.X + 16,
            Game1.uiViewport.Width - (int)size.X - pad * 2 - 8
        );
        int y = Math.Max(
            8,
            cursor.Y - (int)size.Y - pad * 2 - 10
        );

        Rectangle box = new(
            x,
            y,
            (int)size.X + pad * 2,
            (int)size.Y + pad * 2
        );

        b.Draw(Game1.staminaRect, box, new Color(45, 35, 31) * 0.96f);
        CardchaUi.DrawBorder(b, box, CardchaUi.Gold, 2);
        b.DrawString(
            Game1.smallFont,
            text,
            new Vector2(box.X + pad, box.Y + pad),
            Color.White
        );
    }
}
