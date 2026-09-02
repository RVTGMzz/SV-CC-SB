from pathlib import Path

p = Path('src/Cardcha/UI/CardTestLabMenu.cs')
s = p.read_text(encoding='utf-8')


def replace_once(old: str, new: str) -> None:
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'missing Card Test Lab UI anchor: {old[:140]!r}')
    s = s.replace(old, new, 1)

# 20% larger preferred canvas, with viewport clamping.
replace_once(
    '    private readonly IReadOnlyList<CardDefinition> Cards;\n\n    private int SelectedIndex;\n',
    '    private readonly IReadOnlyList<CardDefinition> Cards;\n\n'
    '    private const int PreferredWidth = 1776;\n'
    '    private const int PreferredHeight = 1080;\n'
    '    private const long SelectionDebounceMs = 160L;\n'
    '    private long LastSelectionInputAtMs;\n\n'
    '    private int SelectedIndex;\n'
)

s = s.replace('Math.Min(1480, Game1.uiViewport.Width - 24)', 'Math.Min(PreferredWidth, Game1.uiViewport.Width - 24)')
s = s.replace('Math.Min(900, Game1.uiViewport.Height - 24)', 'Math.Min(PreferredHeight, Game1.uiViewport.Height - 24)')

# Mouse support: selectable card rows, every action button, plus wheel navigation.
old_click = '''    public override void receiveLeftClick(int x, int y, bool playSound = true)\n    {\n        if (this.PrevRect.Contains(x, y)) this.MoveSelection(-1);\n        else if (this.NextRect.Contains(x, y)) this.MoveSelection(1);\n        else if (this.LevelDownRect.Contains(x, y)) this.ChangeLevel(-1);\n        else if (this.LevelUpRect.Contains(x, y)) this.ChangeLevel(1);\n        else if (this.EquipRect.Contains(x, y)) this.EquipAndPlay();\n        else if (this.UnequipRect.Contains(x, y)) this.UnequipAndPlay();\n        else if (this.PassRect.Contains(x, y)) this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);\n        else if (this.FailRect.Contains(x, y)) this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);\n        else if (this.ResetRect.Contains(x, y)) this.Lab.ResetTelemetry();\n        else if (this.HpFullRect.Contains(x, y)) this.Lab.SetHealthPercent(1.0);\n        else if (this.HpLowRect.Contains(x, y)) this.Lab.SetHealthPercent(0.19);\n        else if (this.DummyFullRect.Contains(x, y)) this.Arena.ResetDummy(1.0);\n        else if (this.DummyLowRect.Contains(x, y)) this.Arena.ResetDummy(0.19);\n        else if (this.ArenaRect.Contains(x, y)) this.EnterArenaAndPlay();\n        else if (this.ReturnRect.Contains(x, y) || this.CloseRect.Contains(x, y)) this.ReturnToGame();\n        else if (this.EndLabRect.Contains(x, y)) this.EndLabAndRestore();\n    }\n'''
new_click = '''    public override void receiveLeftClick(int x, int y, bool playSound = true)\n    {\n        if (this.TrySelectCardRowAt(x, y))\n            return;\n\n        if (this.PrevRect.Contains(x, y)) this.MoveSelection(-1, force: true);\n        else if (this.NextRect.Contains(x, y)) this.MoveSelection(1, force: true);\n        else if (this.LevelDownRect.Contains(x, y)) this.ChangeLevel(-1);\n        else if (this.LevelUpRect.Contains(x, y)) this.ChangeLevel(1);\n        else if (this.EquipRect.Contains(x, y)) this.EquipAndPlay();\n        else if (this.UnequipRect.Contains(x, y)) this.UnequipAndPlay();\n        else if (this.PassRect.Contains(x, y))\n        {\n            this.Lab.SetVerdict(this.Selected, CardLabVerdict.Pass);\n            Game1.playSound("coin");\n        }\n        else if (this.FailRect.Contains(x, y))\n        {\n            this.Lab.SetVerdict(this.Selected, CardLabVerdict.Fail);\n            Game1.playSound("cancel");\n        }\n        else if (this.ResetRect.Contains(x, y))\n        {\n            this.Lab.ResetTelemetry();\n            Game1.playSound("smallSelect");\n        }\n        else if (this.HpFullRect.Contains(x, y)) this.Lab.SetHealthPercent(1.0);\n        else if (this.HpLowRect.Contains(x, y)) this.Lab.SetHealthPercent(0.19);\n        else if (this.DummyFullRect.Contains(x, y)) this.Arena.ResetDummy(1.0);\n        else if (this.DummyLowRect.Contains(x, y)) this.Arena.ResetDummy(0.19);\n        else if (this.ArenaRect.Contains(x, y)) this.EnterArenaAndPlay();\n        else if (this.ReturnRect.Contains(x, y) || this.CloseRect.Contains(x, y)) this.ReturnToGame();\n        else if (this.EndLabRect.Contains(x, y)) this.EndLabAndRestore();\n        else base.receiveLeftClick(x, y, playSound);\n    }\n\n    public override void receiveScrollWheelAction(int direction)\n    {\n        if (direction > 0)\n            this.MoveSelection(-1, force: true);\n        else if (direction < 0)\n            this.MoveSelection(1, force: true);\n    }\n'''
replace_once(old_click, new_click)

# More breathing room and larger card list typography.
s = s.replace('int contentTop = outer.Y + 126;', 'int contentTop = outer.Y + 132;')
s = s.replace('int controlsHeight = 126;', 'int controlsHeight = 144;')
s = s.replace('int listWidth = Math.Min(455, Math.Max(330, outer.Width / 3));', 'int listWidth = Math.Min(546, Math.Max(396, outer.Width / 3));')
s = s.replace('int rowHeight = 43;', 'int rowHeight = 51;')
s = s.replace('0.82f, SpriteEffects.None, 1f);\n            string label', '0.94f, SpriteEffects.None, 1f);\n            string label')
s = s.replace('Color.White, 0.88f);\n        }\n    }\n\n    private void DrawSelectedDetail', 'Color.White, 1.0f);\n        }\n    }\n\n    private void DrawSelectedDetail')

# Detail text scales up roughly 10-20%, using the extra canvas space.
s = s.replace('Color.White, 0.92f);', 'Color.White, 1.0f);', 1)
s = s.replace('new Color(206, 196, 225), 0f, Vector2.Zero, 0.86f', 'new Color(206, 196, 225), 0f, Vector2.Zero, 0.96f')
s = s.replace('new Color(255, 218, 116), 0f, Vector2.Zero, 0.98f', 'new Color(255, 218, 116), 0f, Vector2.Zero, 1.08f')
s = s.replace('runColor, 0f, Vector2.Zero, 0.84f', 'runColor, 0f, Vector2.Zero, 0.94f')
s = s.replace('verdictColor, 0f, Vector2.Zero, 0.88f', 'verdictColor, 0f, Vector2.Zero, 0.98f')
s = s.replace('new Color(241, 234, 220), 0.88f, maxLines: 4', 'new Color(241, 234, 220), 0.98f, maxLines: 4')
s = s.replace('new Color(255, 218, 116), 0f, Vector2.Zero, 0.94f', 'new Color(255, 218, 116), 0f, Vector2.Zero, 1.02f')
s = s.replace('instructionArea, Color.White, 0.86f, maxLines: 4', 'instructionArea, Color.White, 0.96f, maxLines: 4')
s = s.replace('new Color(145, 214, 255), 0f, Vector2.Zero, 0.94f', 'new Color(145, 214, 255), 0f, Vector2.Zero, 1.02f')
s = s.replace('new Color(215, 230, 239), 0.78f, maxLines: 12', 'new Color(215, 230, 239), 0.90f, maxLines: 12')
s = s.replace('float scale = Math.Min(0.86f, (rect.Width - 12f)', 'float scale = Math.Min(0.96f, (rect.Width - 12f)')

# Debounce selection at the shared input sink, so D-pad events arriving through both
# key + gamepad routes cannot advance two cards in one physical press.
old_move = '''    private void MoveSelection(int delta)\n    {\n        if (this.Cards.Count == 0)\n            return;\n        this.SelectedIndex = (this.SelectedIndex + delta + this.Cards.Count) % this.Cards.Count;\n        this.RequestedLevel = Math.Clamp(this.RequestedLevel, 1, Math.Max(1, this.Selected.MaxLevel));\n        Game1.playSound("shiny4");\n    }\n'''
new_move = '''    private void MoveSelection(int delta, bool force = false)\n    {\n        if (this.Cards.Count == 0 || delta == 0)\n            return;\n\n        long now = Environment.TickCount64;\n        if (!force && now - this.LastSelectionInputAtMs < SelectionDebounceMs)\n            return;\n\n        this.LastSelectionInputAtMs = now;\n        this.SelectIndex((this.SelectedIndex + delta + this.Cards.Count) % this.Cards.Count);\n    }\n\n    private void SelectIndex(int index)\n    {\n        if (this.Cards.Count == 0)\n            return;\n\n        int next = Math.Clamp(index, 0, this.Cards.Count - 1);\n        if (next == this.SelectedIndex)\n            return;\n\n        this.SelectedIndex = next;\n        this.RequestedLevel = Math.Clamp(this.RequestedLevel, 1, Math.Max(1, this.Selected.MaxLevel));\n        Game1.playSound("shiny4");\n    }\n\n    private bool TrySelectCardRowAt(int x, int y)\n    {\n        Rectangle outer = new(this.xPositionOnScreen, this.yPositionOnScreen, this.width, this.height);\n        int contentTop = outer.Y + 132;\n        int controlsHeight = 144;\n        int panelHeight = outer.Bottom - controlsHeight - contentTop;\n        int listWidth = Math.Min(546, Math.Max(396, outer.Width / 3));\n        Rectangle panel = new(outer.X + 20, contentTop, listWidth, panelHeight);\n\n        if (!panel.Contains(x, y))\n            return false;\n\n        const int rowHeight = 51;\n        int visible = Math.Max(7, (panel.Height - 20) / rowHeight);\n        int start = Math.Clamp(this.SelectedIndex - visible / 2, 0, Math.Max(0, this.Cards.Count - visible));\n        int end = Math.Min(this.Cards.Count, start + visible);\n\n        for (int i = start; i < end; i++)\n        {\n            int row = i - start;\n            Rectangle rowRect = new(panel.X + 10, panel.Y + 10 + row * rowHeight, panel.Width - 20, rowHeight - 4);\n            if (!rowRect.Contains(x, y))\n                continue;\n\n            this.LastSelectionInputAtMs = Environment.TickCount64;\n            this.SelectIndex(i);\n            return true;\n        }\n\n        return false;\n    }\n'''
replace_once(old_move, new_move)

# Larger button hitboxes made possible by the wider/taller menu.
old_rects = '''        int gap = 7;\n        int row1Y = this.yPositionOnScreen + this.height - 106;\n        int row2Y = this.yPositionOnScreen + this.height - 56;\n\n        int x = left;\n        this.PrevRect = new Rectangle(x, row1Y, 102, 42); x += 102 + gap;\n        this.NextRect = new Rectangle(x, row1Y, 102, 42); x += 102 + gap;\n        this.LevelDownRect = new Rectangle(x, row1Y, 76, 42); x += 76 + gap;\n        this.LevelUpRect = new Rectangle(x, row1Y, 76, 42); x += 76 + gap;\n        this.EquipRect = new Rectangle(x, row1Y, 172, 42); x += 172 + gap;\n        this.UnequipRect = new Rectangle(x, row1Y, 188, 42); x += 188 + gap;\n        this.ResetRect = new Rectangle(x, row1Y, Math.Max(140, Math.Min(190, left + available - x)), 42);\n\n        x = left;\n        this.PassRect = new Rectangle(x, row2Y, 96, 42); x += 96 + gap;\n        this.FailRect = new Rectangle(x, row2Y, 96, 42); x += 96 + gap;\n        this.HpFullRect = new Rectangle(x, row2Y, 100, 42); x += 100 + gap;\n        this.HpLowRect = new Rectangle(x, row2Y, 94, 42); x += 94 + gap;\n        this.DummyFullRect = new Rectangle(x, row2Y, 145, 42); x += 145 + gap;\n        this.DummyLowRect = new Rectangle(x, row2Y, 142, 42); x += 142 + gap;\n        this.ArenaRect = new Rectangle(x, row2Y, 140, 42); x += 140 + gap;\n        this.ReturnRect = new Rectangle(x, row2Y, 128, 42); x += 128 + gap;\n        this.EndLabRect = new Rectangle(x, row2Y, Math.Max(175, Math.Min(220, left + available - x)), 42);\n\n        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 148, this.yPositionOnScreen + 18, 126, 38);\n'''
new_rects = '''        int gap = 8;\n        int row1Y = this.yPositionOnScreen + this.height - 124;\n        int row2Y = this.yPositionOnScreen + this.height - 66;\n\n        int x = left;\n        this.PrevRect = new Rectangle(x, row1Y, 118, 50); x += 118 + gap;\n        this.NextRect = new Rectangle(x, row1Y, 118, 50); x += 118 + gap;\n        this.LevelDownRect = new Rectangle(x, row1Y, 88, 50); x += 88 + gap;\n        this.LevelUpRect = new Rectangle(x, row1Y, 88, 50); x += 88 + gap;\n        this.EquipRect = new Rectangle(x, row1Y, 198, 50); x += 198 + gap;\n        this.UnequipRect = new Rectangle(x, row1Y, 218, 50); x += 218 + gap;\n        this.ResetRect = new Rectangle(x, row1Y, Math.Max(168, Math.Min(228, left + available - x)), 50);\n\n        x = left;\n        this.PassRect = new Rectangle(x, row2Y, 108, 50); x += 108 + gap;\n        this.FailRect = new Rectangle(x, row2Y, 108, 50); x += 108 + gap;\n        this.HpFullRect = new Rectangle(x, row2Y, 116, 50); x += 116 + gap;\n        this.HpLowRect = new Rectangle(x, row2Y, 110, 50); x += 110 + gap;\n        this.DummyFullRect = new Rectangle(x, row2Y, 170, 50); x += 170 + gap;\n        this.DummyLowRect = new Rectangle(x, row2Y, 166, 50); x += 166 + gap;\n        this.ArenaRect = new Rectangle(x, row2Y, 164, 50); x += 164 + gap;\n        this.ReturnRect = new Rectangle(x, row2Y, 148, 50); x += 148 + gap;\n        this.EndLabRect = new Rectangle(x, row2Y, Math.Max(198, Math.Min(258, left + available - x)), 50);\n\n        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 164, this.yPositionOnScreen + 18, 142, 42);\n'''
replace_once(old_rects, new_rects)

p.write_text(s, encoding='utf-8')
print('Applied alpha28.0.4.14.3.4 Card Test Lab controller/mouse/20-percent UI hotfix')
