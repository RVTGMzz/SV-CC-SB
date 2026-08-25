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

        // Draw the approved closed Cardcha journal directly with pixel primitives.
        // This deliberately avoids a texture dependency so the external Book tab can
        // never become blank because of a damaged or partially-copied PNG.
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

        // The Binder itself also gets a procedural balanced two-page shell. The
        // prefix runs after CardchaBinderMenu drew its base fallback frame, but before
        // the first dynamic tab/content pass. This keeps both covers/pages symmetric
        // and prevents any binary book-frame texture from cutting holes into the UI.
        System.Reflection.MethodInfo? drawRarityTabs =
            AccessTools.Method(typeof(CardchaBinderMenu), "DrawRarityTabs");

        if (drawRarityTabs is not null)
        {
            harmony.Patch(
                drawRarityTabs,
                prefix: new HarmonyMethod(
                    typeof(BookNavigationPatch),
                    nameof(DrawBinderShellPrefix)
                )
            );
        }
        else
        {
            ModEntry.StaticMonitor?.Log(
                "Cardcha v0.2: couldn't find CardchaBinderMenu.DrawRarityTabs; using the safe fallback book frame.",
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
        Rectangle r = ___BookTab.bounds;
        bool focused = graphOwner.currentlySnappedComponent?.myID == ___BookTab.myID;
        Point cursor = CardchaUi.GetUiMousePoint();
        bool hovered = r.Contains(cursor);

        DrawClosedJournalIcon(b, r, focused || hovered);

        if (focused)
            CardchaUi.DrawFocus(b, r);

        if (hovered)
            DrawTooltip(b, ModEntry.T("booktab.tooltip"));

        return false;
    }

    private static bool DrawBinderShellPrefix(
        SpriteBatch b,
        CardchaBinderMenu __instance)
    {
        DrawBalancedBookShell(
            b,
            new Rectangle(
                __instance.xPositionOnScreen,
                __instance.yPositionOnScreen,
                __instance.width,
                __instance.height
            )
        );

        // Continue into the real rarity-tab drawing method.
        return true;
    }

    private static void DrawClosedJournalIcon(
        SpriteBatch b,
        Rectangle r,
        bool highlighted)
    {
        Rectangle shadow = new(r.X + 3, r.Y + 4, r.Width, r.Height);
        b.Draw(Game1.staminaRect, shadow, new Color(49, 30, 24) * 0.58f);

        Rectangle outer = highlighted
            ? new Rectangle(r.X - 2, r.Y - 2, r.Width + 4, r.Height + 4)
            : r;

        Color gold = new(223, 156, 55);
        Color goldLight = new(255, 206, 92);
        Color leatherDark = new(70, 34, 25);
        Color leather = new(125, 58, 38);
        Color leatherLight = new(158, 77, 48);
        Color page = new(238, 209, 157);

        b.Draw(Game1.staminaRect, outer, highlighted ? Color.White : gold);
        Rectangle cover = new(
            outer.X + 3,
            outer.Y + 3,
            Math.Max(1, outer.Width - 6),
            Math.Max(1, outer.Height - 6)
        );
        b.Draw(Game1.staminaRect, cover, leatherDark);

        Rectangle face = new(
            cover.X + Math.Max(4, cover.Width / 7),
            cover.Y + 5,
            Math.Max(10, cover.Width - Math.Max(8, cover.Width / 7) - 6),
            Math.Max(12, cover.Height - 14)
        );
        b.Draw(Game1.staminaRect, face, leather);
        CardchaUi.DrawBorder(b, face, leatherLight, 2);

        // Bound leather spine with three bands, like the approved cover mockup.
        int spineW = Math.Max(7, cover.Width / 7);
        Rectangle spine = new(cover.X + 2, cover.Y + 3, spineW, cover.Height - 6);
        b.Draw(Game1.staminaRect, spine, new Color(91, 42, 30));
        for (int i = 1; i <= 3; i++)
        {
            int y = spine.Y + i * spine.Height / 4;
            b.Draw(Game1.staminaRect, new Rectangle(spine.X, y - 2, spine.Width, 4), leatherLight);
            b.Draw(Game1.staminaRect, new Rectangle(spine.X + 1, y - 1, Math.Max(1, spine.Width - 2), 1), gold * 0.65f);
        }

        // Cream page edge at the bottom and the little blue bookmark.
        Rectangle pageEdge = new(face.X + 2, face.Bottom - Math.Max(5, cover.Height / 9), face.Width - 6, Math.Max(4, cover.Height / 10));
        b.Draw(Game1.staminaRect, pageEdge, page);
        b.Draw(Game1.staminaRect, new Rectangle(pageEdge.X, pageEdge.Y, pageEdge.Width, 1), Color.White * 0.55f);

        int ribbonW = Math.Max(4, cover.Width / 10);
        Rectangle ribbon = new(
            face.X + face.Width / 5,
            pageEdge.Y,
            ribbonW,
            Math.Max(7, cover.Height / 6)
        );
        b.Draw(Game1.staminaRect, ribbon, new Color(43, 83, 124));
        b.Draw(Game1.staminaRect, new Rectangle(ribbon.X + 1, ribbon.Y, Math.Max(1, ribbon.Width - 2), 1), new Color(78, 127, 169));

        // Gold reinforced corners on the two visible outer corners.
        int corner = Math.Max(5, cover.Width / 7);
        DrawCornerGuard(b, new Rectangle(face.Right - corner, face.Y, corner, corner), gold, goldLight, top: true);
        DrawCornerGuard(b, new Rectangle(face.Right - corner, face.Bottom - corner, corner, corner), gold, goldLight, top: false);

        // Central compass/star sigil.
        Point c = new(face.Center.X, face.Center.Y - Math.Max(1, cover.Height / 14));
        int arm = Math.Max(5, Math.Min(face.Width, face.Height) / 5);
        int thick = Math.Max(2, arm / 4);
        b.Draw(Game1.staminaRect, new Rectangle(c.X - thick / 2, c.Y - arm, thick, arm * 2), goldLight);
        b.Draw(Game1.staminaRect, new Rectangle(c.X - arm, c.Y - thick / 2, arm * 2, thick), goldLight);
        int diamond = Math.Max(3, arm / 2);
        for (int dy = -diamond; dy <= diamond; dy++)
        {
            int span = diamond - Math.Abs(dy);
            b.Draw(Game1.staminaRect, new Rectangle(c.X - span, c.Y + dy, span * 2 + 1, 1), gold);
        }

        // Right leather clasp + round brass stud.
        int claspW = Math.Max(9, cover.Width / 4);
        int claspH = Math.Max(8, cover.Height / 5);
        Rectangle clasp = new(
            face.Right - claspW / 3,
            c.Y - claspH / 2,
            claspW,
            claspH
        );
        b.Draw(Game1.staminaRect, clasp, leather);
        CardchaUi.DrawBorder(b, clasp, leatherDark, 2);
        int stud = Math.Max(3, Math.Min(clasp.Width, clasp.Height) / 3);
        b.Draw(Game1.staminaRect, new Rectangle(clasp.Center.X - stud / 2, clasp.Center.Y - stud / 2, stud, stud), goldLight);

        CardchaUi.DrawBorder(b, outer, highlighted ? Color.White : new Color(92, 49, 32), highlighted ? 3 : 2);
    }

    private static void DrawCornerGuard(
        SpriteBatch b,
        Rectangle r,
        Color gold,
        Color light,
        bool top)
    {
        b.Draw(Game1.staminaRect, r, gold);
        int cut = Math.Max(2, r.Width / 3);
        if (top)
        {
            b.Draw(Game1.staminaRect, new Rectangle(r.X, r.Bottom - cut, cut, cut), new Color(125, 58, 38));
        }
        else
        {
            b.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, cut, cut), new Color(125, 58, 38));
        }
        b.Draw(Game1.staminaRect, new Rectangle(r.X + 2, r.Y + 2, Math.Max(1, r.Width - 4), 2), light * 0.75f);
    }

    private static void DrawBalancedBookShell(
        SpriteBatch b,
        Rectangle outer)
    {
        if (outer.Width < 200 || outer.Height < 160)
            return;

        double sx = outer.Width / 1180d;
        double sy = outer.Height / 760d;
        int X(int n) => outer.X + (int)Math.Round(n * sx);
        int Y(int n) => outer.Y + (int)Math.Round(n * sy);
        int W(int n) => Math.Max(1, (int)Math.Round(n * sx));
        int H(int n) => Math.Max(1, (int)Math.Round(n * sy));

        Color leatherDark = new(58, 31, 27);
        Color leather = new(104, 52, 36);
        Color leatherLight = new(139, 73, 45);
        Color gold = new(202, 137, 46);
        Color goldLight = new(246, 192, 81);
        Color pageEdge = new(196, 157, 106);
        Color paper = new(236, 207, 158);
        Color paperLight = new(248, 224, 179);
        Color paperShade = new(211, 179, 132);

        // Equal outer cover rails on both sides.
        Rectangle leftCover = new(X(44), Y(30), W(526), H(700));
        Rectangle rightCover = new(X(610), Y(30), W(526), H(700));
        b.Draw(Game1.staminaRect, leftCover, leatherDark);
        b.Draw(Game1.staminaRect, rightCover, leatherDark);
        CardchaUi.DrawBorder(b, leftCover, leatherLight, Math.Max(2, W(3)));
        CardchaUi.DrawBorder(b, rightCover, leatherLight, Math.Max(2, W(3)));

        // Equal stacked page thickness, including the visible outer edges.
        for (int i = 0; i < 4; i++)
        {
            Rectangle lStack = new(X(62 + i * 3), Y(48 + i * 2), W(500 - i * 5), H(665 - i * 4));
            Rectangle rStack = new(X(618 + i * 2), Y(48 + i * 2), W(500 - i * 5), H(665 - i * 4));
            b.Draw(Game1.staminaRect, lStack, i == 3 ? paper : pageEdge);
            b.Draw(Game1.staminaRect, rStack, i == 3 ? paper : pageEdge);
        }

        Rectangle leftPage = new(X(79), Y(57), W(482), H(647));
        Rectangle rightPage = new(X(619), Y(57), W(482), H(647));
        b.Draw(Game1.staminaRect, leftPage, paper);
        b.Draw(Game1.staminaRect, rightPage, paper);
        CardchaUi.DrawBorder(b, leftPage, paperShade, Math.Max(2, W(2)));
        CardchaUi.DrawBorder(b, rightPage, paperShade, Math.Max(2, W(2)));

        b.Draw(Game1.staminaRect, new Rectangle(leftPage.X + W(7), leftPage.Y + H(7), leftPage.Width - W(14), H(2)), paperLight * 0.85f);
        b.Draw(Game1.staminaRect, new Rectangle(rightPage.X + W(7), rightPage.Y + H(7), rightPage.Width - W(14), H(2)), paperLight * 0.85f);
        b.Draw(Game1.staminaRect, new Rectangle(leftPage.X + W(7), leftPage.Bottom - H(9), leftPage.Width - W(14), H(2)), paperShade * 0.55f);
        b.Draw(Game1.staminaRect, new Rectangle(rightPage.X + W(7), rightPage.Bottom - H(9), rightPage.Width - W(14), H(2)), paperShade * 0.55f);

        // Real central leather spine connecting both covers.
        Rectangle spineShadow = new(X(570), Y(30), W(42), H(700));
        b.Draw(Game1.staminaRect, spineShadow, new Color(37, 23, 22));
        Rectangle spine = new(X(576), Y(35), W(30), H(690));
        b.Draw(Game1.staminaRect, spine, leather);
        CardchaUi.DrawBorder(b, spine, leatherDark, Math.Max(2, W(2)));
        b.Draw(Game1.staminaRect, new Rectangle(spine.X + W(5), spine.Y + H(8), W(3), spine.Height - H(16)), leatherLight * 0.65f);
        b.Draw(Game1.staminaRect, new Rectangle(spine.Right - W(8), spine.Y + H(8), W(3), spine.Height - H(16)), leatherDark * 0.65f);

        // Brass rings/pins on the spine.
        int[] ringY = { 104, 272, 446, 620 };
        foreach (int designY in ringY)
        {
            Rectangle bar = new(X(560), Y(designY), W(62), H(11));
            b.Draw(Game1.staminaRect, bar, gold);
            CardchaUi.DrawBorder(b, bar, new Color(91, 57, 31), Math.Max(1, W(1)));
            Rectangle gem = new(X(586), Y(designY - 5), W(10), H(21));
            b.Draw(Game1.staminaRect, gem, new Color(41, 87, 132));
            CardchaUi.DrawBorder(b, gem, goldLight, Math.Max(1, W(1)));
        }

        // Matching outer brass hardware on BOTH covers: corner guards plus side pins.
        DrawBookCorner(b, X(44), Y(30), W(30), H(30), gold, goldLight);
        DrawBookCorner(b, X(1106), Y(30), W(30), H(30), gold, goldLight);
        DrawBookCorner(b, X(44), Y(700), W(30), H(30), gold, goldLight);
        DrawBookCorner(b, X(1106), Y(700), W(30), H(30), gold, goldLight);

        int[] pinYs = { 155, 370, 585 };
        foreach (int designY in pinYs)
        {
            DrawSidePin(b, new Rectangle(X(38), Y(designY), W(18), H(28)), gold, goldLight);
            DrawSidePin(b, new Rectangle(X(1124), Y(designY), W(18), H(28)), gold, goldLight);
        }

        // Blue bookmark hanging from the bottom like the approved closed-cover art.
        Rectangle ribbon = new(X(324), Y(702), W(34), H(45));
        b.Draw(Game1.staminaRect, ribbon, new Color(39, 77, 117));
        CardchaUi.DrawBorder(b, ribbon, gold, Math.Max(1, W(1)));
        b.Draw(Game1.staminaRect, new Rectangle(ribbon.Center.X - W(2), ribbon.Y + H(9), W(4), H(20)), goldLight * 0.85f);
        b.Draw(Game1.staminaRect, new Rectangle(ribbon.X + W(8), ribbon.Y + H(17), ribbon.Width - W(16), H(3)), goldLight * 0.85f);
    }

    private static void DrawBookCorner(
        SpriteBatch b,
        int x,
        int y,
        int w,
        int h,
        Color gold,
        Color light)
    {
        Rectangle r = new(x, y, w, h);
        b.Draw(Game1.staminaRect, r, gold);
        b.Draw(Game1.staminaRect, new Rectangle(x + Math.Max(2, w / 5), y + Math.Max(2, h / 5), Math.Max(3, w * 3 / 5), Math.Max(3, h * 3 / 5)), new Color(116, 72, 32));
        b.Draw(Game1.staminaRect, new Rectangle(x + Math.Max(3, w / 3), y + Math.Max(3, h / 3), Math.Max(3, w / 3), Math.Max(3, h / 3)), light);
    }

    private static void DrawSidePin(
        SpriteBatch b,
        Rectangle r,
        Color gold,
        Color light)
    {
        b.Draw(Game1.staminaRect, r, new Color(70, 38, 29));
        CardchaUi.DrawBorder(b, r, gold, Math.Max(1, r.Width / 7));
        int dot = Math.Max(3, Math.Min(r.Width, r.Height) / 3);
        b.Draw(Game1.staminaRect, new Rectangle(r.Center.X - dot / 2, r.Center.Y - dot / 2, dot, dot), light);
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
