from pathlib import Path
import re

root = Path('src/Cardcha')
menu_p = root / 'UI/CardchaBinderMenuV2.cs'
service_p = root / 'UI/CardchaBookTabService.cs'
patch_p = root / 'Patches/BookNavigationPatch.cs'
csproj_p = root / 'Cardcha.csproj'
manifest_p = root / 'manifest.json'

# --- Binder ---
text = menu_p.read_text(encoding='utf-8')
if 'using StardewModdingAPI;' not in text:
    text = text.replace('using StardewValley;\n', 'using StardewModdingAPI;\nusing StardewValley;\n', 1)

# Remove the obsolete binary book-frame dependency if it is still present.
text = text.replace('    private readonly Texture2D? BookFrame;\n', '')
text = re.sub(
    r'\n        try\n        \{\n            this\.BookFrame = ModEntry\.StaticHelper\?\.ModContent\.Load<Texture2D>\("assets/binder_book_frame\.png"\);\n        \}\n        catch \(Exception ex\)\n        \{\n            this\.BookFrame = null;\n            ModEntry\.LogOnce\("binder-book-frame", \$"Couldn\'t load approved Cardcha book frame; using runtime fallback\. \{ex\.Message\}"\);\n        \}\n',
    '\n',
    text,
    count=1,
)
text = text.replace(
'''        if (this.BookFrame is not null) b.Draw(this.BookFrame, book, Color.White);\n        else CardchaUi.DrawBookFrame(b, book);''',
'''        CardchaUi.DrawBookFrame(b, book);''')
text = text.replace(
'''        if (this.BookFrame is not null)\n            b.Draw(this.BookFrame, book, Color.White);\n        else\n            CardchaUi.DrawBookFrame(b, book);''',
'''        CardchaUi.DrawBookFrame(b, book);''')

old_ctor = '''    ) : base(\n        Game1.uiViewport.Width / 2 - Math.Min(DesignWidth, Game1.uiViewport.Width - 24) / 2,\n        Game1.uiViewport.Height / 2 - Math.Min(DesignHeight, Game1.uiViewport.Height - 24) / 2,\n        Math.Min(DesignWidth, Game1.uiViewport.Width - 24),\n        Math.Min(DesignHeight, Game1.uiViewport.Height - 24),\n        showUpperRightCloseButton: false)'''
new_ctor = '''    ) : base(\n        2,\n        2,\n        Math.Max(320, Game1.uiViewport.Width - 4),\n        Math.Max(240, Game1.uiViewport.Height - 4),\n        showUpperRightCloseButton: false)'''
if old_ctor in text:
    text = text.replace(old_ctor, new_ctor, 1)

repls = {
    'this.DetailScrollViewport = this.R(664, 328, 382, 174);':'this.DetailScrollViewport = this.R(620, 318, 468, 188);',
    'this.DetailScrollTrack = this.R(1052, 328, 12, 174);':'this.DetailScrollTrack = this.R(1094, 318, 12, 188);',
    'this.EquipButton = new ClickableComponent(this.R(688, 590, 355, 45), "equip") { myID = EquipId };':'this.EquipButton = new ClickableComponent(this.R(628, 588, 470, 48), "equip") { myID = EquipId };',
    'this.UnequipButton = new ClickableComponent(this.R(688, 646, 355, 45), "unequip") { myID = UnequipId };':'this.UnequipButton = new ClickableComponent(this.R(628, 644, 470, 48), "unequip") { myID = UnequipId };',
    'this.UpgradeButton = new ClickableComponent(this.R(688, 702, 355, 42), "upgrade") { myID = UpgradeId };':'this.UpgradeButton = new ClickableComponent(this.R(628, 700, 470, 44), "upgrade") { myID = UpgradeId };',
    'this.R(716, 58, 300, 42)':'this.R(650, 50, 430, 48)',
    'this.R(724, 113, 286, 46)':'this.R(650, 108, 430, 50)',
    'this.R(698, 190, 342, 116)':'this.R(640, 184, 450, 126)',
    'this.R(714, 112, 306, 48)':'this.R(642, 108, 446, 52)',
    'this.R(684, 184, 78, 78)':'this.R(636, 176, 88, 88)',
    'this.R(778, 184, 250, 24)':'this.R(742, 178, 344, 28)',
    'this.R(778, 210, 250, 22)':'this.R(742, 210, 344, 26)',
    'this.R(778, 236, 250, 22)':'this.R(742, 239, 344, 24)',
    'this.R(684, 269, 356, 48)':'this.R(636, 268, 452, 46)',
    'Rectangle noteBox = this.R(678, 516, 375, 62);':'Rectangle noteBox = this.R(620, 516, 486, 64);',
    'this.R(690, 520, 160, 22)':'this.R(634, 520, 180, 24)',
    'this.R(690, 543, 350, 31)':'this.R(634, 546, 458, 30)',
}
for a, b in repls.items():
    if a in text:
        text = text.replace(a, b)

# Make the text less aggressively shrunk.
text = text.replace('maxScale: 0.84f);', 'maxScale: 0.96f);')
text = text.replace('maxScale: 0.72f);', 'maxScale: 0.90f);')
text = text.replace('maxScale: 0.78f);', 'maxScale: 0.92f);')
text = text.replace('minScale: 0.56f, maxScale: 0.92f', 'minScale: 0.68f, maxScale: 0.96f')
text = text.replace('minScale: 0.62f, maxScale: 0.88f', 'minScale: 0.72f, maxScale: 1.00f')
text = text.replace('padding: 1, maxScale: 0.95f);', 'padding: 1, maxScale: 1.04f);')
text = text.replace('padding: 1, maxScale: 0.88f);', 'padding: 1, maxScale: 0.98f);')

if 'internal bool TryHandleRawControllerButton(SButton button)' not in text:
    marker = '    public override void receiveGamePadButton(Buttons b)\n'
    handler = '''    internal bool TryHandleRawControllerButton(SButton button)\n    {\n        if (this.currentlySnappedComponent?.myID != DetailScrollId)\n            return false;\n\n        if (button == SButton.ControllerA)\n        {\n            this.DetailInspectMode = !this.DetailInspectMode;\n            this.Status = ModEntry.T(this.DetailInspectMode\n                ? "binder.detail.inspect-on"\n                : "binder.detail.inspect-exit");\n            Game1.playSound("smallSelect");\n            return true;\n        }\n\n        if (button == SButton.ControllerB && this.DetailInspectMode)\n        {\n            this.DetailInspectMode = false;\n            this.Status = ModEntry.T("binder.detail.inspect-exit");\n            Game1.playSound("smallSelect");\n            return true;\n        }\n\n        return false;\n    }\n\n'''
    if marker not in text:
        raise SystemExit('receiveGamePadButton marker missing')
    text = text.replace(marker, handler + marker, 1)

menu_p.write_text(text, encoding='utf-8')

# --- Book tab input raw interception ---
text = service_p.read_text(encoding='utf-8')
if 'binder.TryHandleRawControllerButton(e.Button)' not in text:
    needle = '''    public void OnButtonPressed(\n        object? sender,\n        ButtonPressedEventArgs e)\n    {\n        IClickableMenu? menu = Game1.activeClickableMenu;\n        if (!IsSupported(menu) || !this.Save.Data.BinderUnlocked)\n            return;\n'''
    replacement = '''    public void OnButtonPressed(\n        object? sender,\n        ButtonPressedEventArgs e)\n    {\n        IClickableMenu? menu = Game1.activeClickableMenu;\n\n        if (menu is CardchaBinderMenu binder\n            && binder.TryHandleRawControllerButton(e.Button))\n        {\n            this.Helper.Input.Suppress(e.Button);\n            return;\n        }\n\n        if (!IsSupported(menu) || !this.Save.Data.BinderUnlocked)\n            return;\n'''
    if needle not in text:
        raise SystemExit('BookTab OnButtonPressed marker missing')
    text = text.replace(needle, replacement, 1)
service_p.write_text(text, encoding='utf-8')

# --- Book shell: remove thick central spine and use near-full-height pages ---
text = patch_p.read_text(encoding='utf-8')
start = text.find('    private static void DrawBalancedBookShell(')
end = text.find('    private static void DrawBookCorner(', start)
if start < 0 or end < 0:
    raise SystemExit('DrawBalancedBookShell markers missing')
new_func = r'''    private static void DrawBalancedBookShell(\n        SpriteBatch b,\n        Rectangle outer)\n    {\n        if (outer.Width < 200 || outer.Height < 160)\n            return;\n\n        double sx = outer.Width / 1180d;\n        double sy = outer.Height / 760d;\n        int X(int n) => outer.X + (int)Math.Round(n * sx);\n        int Y(int n) => outer.Y + (int)Math.Round(n * sy);\n        int W(int n) => Math.Max(1, (int)Math.Round(n * sx));\n        int H(int n) => Math.Max(1, (int)Math.Round(n * sy));\n\n        Color leatherDark = new(58, 31, 27);\n        Color leatherLight = new(139, 73, 45);\n        Color gold = new(202, 137, 46);\n        Color goldLight = new(246, 192, 81);\n        Color pageEdge = new(196, 157, 106);\n        Color paper = new(236, 207, 158);\n        Color paperLight = new(248, 224, 179);\n        Color paperShade = new(211, 179, 132);\n\n        Rectangle leftCover = new(X(48), Y(8), W(535), H(744));\n        Rectangle rightCover = new(X(597), Y(8), W(535), H(744));\n        b.Draw(Game1.staminaRect, leftCover, leatherDark);\n        b.Draw(Game1.staminaRect, rightCover, leatherDark);\n        CardchaUi.DrawBorder(b, leftCover, leatherLight, Math.Max(2, W(3)));\n        CardchaUi.DrawBorder(b, rightCover, leatherLight, Math.Max(2, W(3)));\n\n        for (int i = 0; i < 4; i++)\n        {\n            Rectangle lStack = new(X(60 + i * 3), Y(20 + i * 2), W(520 - i * 5), H(716 - i * 4));\n            Rectangle rStack = new(X(600 + i * 2), Y(20 + i * 2), W(520 - i * 5), H(716 - i * 4));\n            b.Draw(Game1.staminaRect, lStack, i == 3 ? paper : pageEdge);\n            b.Draw(Game1.staminaRect, rStack, i == 3 ? paper : pageEdge);\n        }\n\n        Rectangle leftPage = new(X(72), Y(28), W(510), H(700));\n        Rectangle rightPage = new(X(598), Y(28), W(510), H(700));\n        b.Draw(Game1.staminaRect, leftPage, paper);\n        b.Draw(Game1.staminaRect, rightPage, paper);\n        CardchaUi.DrawBorder(b, leftPage, paperShade, Math.Max(2, W(2)));\n        CardchaUi.DrawBorder(b, rightPage, paperShade, Math.Max(2, W(2)));\n\n        b.Draw(Game1.staminaRect, new Rectangle(leftPage.X + W(7), leftPage.Y + H(7), leftPage.Width - W(14), H(2)), paperLight * 0.85f);\n        b.Draw(Game1.staminaRect, new Rectangle(rightPage.X + W(7), rightPage.Y + H(7), rightPage.Width - W(14), H(2)), paperLight * 0.85f);\n        b.Draw(Game1.staminaRect, new Rectangle(leftPage.X + W(7), leftPage.Bottom - H(9), leftPage.Width - W(14), H(2)), paperShade * 0.55f);\n        b.Draw(Game1.staminaRect, new Rectangle(rightPage.X + W(7), rightPage.Bottom - H(9), rightPage.Width - W(14), H(2)), paperShade * 0.55f);\n\n        Rectangle foldShadow = new(X(584), Y(24), W(10), H(708));\n        b.Draw(Game1.staminaRect, foldShadow, new Color(121, 84, 59) * 0.34f);\n        b.Draw(Game1.staminaRect, new Rectangle(X(588), Y(30), W(2), H(696)), paperLight * 0.45f);\n\n        DrawBookCorner(b, X(48), Y(8), W(30), H(30), gold, goldLight);\n        DrawBookCorner(b, X(1102), Y(8), W(30), H(30), gold, goldLight);\n        DrawBookCorner(b, X(48), Y(722), W(30), H(30), gold, goldLight);\n        DrawBookCorner(b, X(1102), Y(722), W(30), H(30), gold, goldLight);\n\n        int[] pinYs = { 145, 365, 585 };\n        foreach (int designY in pinYs)\n        {\n            DrawSidePin(b, new Rectangle(X(42), Y(designY), W(18), H(28)), gold, goldLight);\n            DrawSidePin(b, new Rectangle(X(1120), Y(designY), W(18), H(28)), gold, goldLight);\n        }\n\n        Rectangle ribbon = new(X(324), Y(718), W(34), H(38));\n        b.Draw(Game1.staminaRect, ribbon, new Color(39, 77, 117));\n        CardchaUi.DrawBorder(b, ribbon, gold, Math.Max(1, W(1)));\n        b.Draw(Game1.staminaRect, new Rectangle(ribbon.Center.X - W(2), ribbon.Y + H(7), W(4), H(18)), goldLight * 0.85f);\n        b.Draw(Game1.staminaRect, new Rectangle(ribbon.X + W(8), ribbon.Y + H(15), ribbon.Width - W(16), H(3)), goldLight * 0.85f);\n    }\n\n'''
text = text[:start] + new_func.replace('\\n','\n') + text[end:]
patch_p.write_text(text, encoding='utf-8')

# Version bump for the one test package.
csproj = csproj_p.read_text(encoding='utf-8').replace('0.2.0-alpha.2', '0.2.0-alpha.3')
manifest = manifest_p.read_text(encoding='utf-8').replace('0.2.0-alpha.2', '0.2.0-alpha.3')
csproj_p.write_text(csproj, encoding='utf-8')
manifest_p.write_text(manifest, encoding='utf-8')

# Assertions that protect the test build from regressing to alpha.2 behavior.
menu = menu_p.read_text(encoding='utf-8')
assert 'binder_book_frame.png' not in menu
assert 'TryHandleRawControllerButton' in menu
assert 'Game1.uiViewport.Width - 4' in menu
assert 'this.R(620, 318, 468, 188)' in menu
svc = service_p.read_text(encoding='utf-8')
assert 'binder.TryHandleRawControllerButton(e.Button)' in svc
nav = patch_p.read_text(encoding='utf-8')
assert 'Real central leather spine' not in nav
assert 'foldShadow' in nav
print('alpha.3 patch applied successfully')
