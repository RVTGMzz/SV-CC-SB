from pathlib import Path
import re

p = Path('src/Cardcha/UI/CardTestLabMenu.cs')
s = p.read_text(encoding='utf-8')

def once(old, new):
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'missing anchor: {old[:120]!r}')
    s = s.replace(old, new, 1)

once('    private readonly CardRenderer Renderer;\n', '    private readonly CardRenderer Renderer;\n    private readonly CardTestArenaService Arena;\n')
once('    private Rectangle HpLowRect;\n', '    private Rectangle HpLowRect;\n    private Rectangle DummyFullRect;\n    private Rectangle DummyLowRect;\n    private Rectangle ArenaRect;\n')
s = s.replace('public CardTestLabMenu(CardTestLabService lab, CardRenderer renderer)', 'public CardTestLabMenu(CardTestLabService lab, CardRenderer renderer, CardTestArenaService arena)')
once('        this.Renderer = renderer;\n', '        this.Renderer = renderer;\n        this.Arena = arena;\n')

if '            case Keys.T:\n                this.EnterArenaAndPlay();' not in s:
    once(
        '            case Keys.End:\n                this.EndLabAndRestore();\n                return;\n',
        '            case Keys.T:\n                this.EnterArenaAndPlay();\n                return;\n            case Keys.F7:\n                this.Arena.ResetDummy(1.0);\n                return;\n            case Keys.F6:\n                this.Arena.ResetDummy(0.19);\n                return;\n            case Keys.End:\n                this.EndLabAndRestore();\n                return;\n'
    )

if '            case Buttons.RightTrigger:\n                this.EnterArenaAndPlay();' not in s:
    once(
        '            case Buttons.Start:\n                this.EndLabAndRestore();\n                return;\n',
        '            case Buttons.RightTrigger:\n                this.EnterArenaAndPlay();\n                return;\n            case Buttons.LeftTrigger:\n                this.Arena.ResetDummy(1.0);\n                return;\n            case Buttons.RightStick:\n                this.Arena.ResetDummy(0.19);\n                return;\n            case Buttons.Start:\n                this.EndLabAndRestore();\n                return;\n'
    )

if 'else if (this.DummyFullRect.Contains(x, y)) this.Arena.ResetDummy(1.0);' not in s:
    once(
        '        else if (this.HpLowRect.Contains(x, y)) this.Lab.SetHealthPercent(0.19);\n        else if (this.ReturnRect.Contains(x, y) || this.CloseRect.Contains(x, y)) this.ReturnToGame();\n',
        '        else if (this.HpLowRect.Contains(x, y)) this.Lab.SetHealthPercent(0.19);\n        else if (this.DummyFullRect.Contains(x, y)) this.Arena.ResetDummy(1.0);\n        else if (this.DummyLowRect.Contains(x, y)) this.Arena.ResetDummy(0.19);\n        else if (this.ArenaRect.Contains(x, y)) this.EnterArenaAndPlay();\n        else if (this.ReturnRect.Contains(x, y) || this.CloseRect.Contains(x, y)) this.ReturnToGame();\n'
    )

s = s.replace(
    'string guide = "↑↓ CHỌN LÁ   •   ←→ LEVEL   •   A EQUIP & PLAY   •   X UNEQUIP & PLAY   •   gõ cardcha_card_test để mở lại và xem kết quả";',
    'string guide = "↑↓ CHỌN LÁ   •   ←→ LEVEL   •   A EQUIP   •   X BASELINE   •   RT VÀO ARENA   •   B THU NHỎ   •   F8 / R-STICK MỞ LẠI";'
)

old = '''        DrawButton(b, this.PassRect, "PASS [Y/P]", new Color(57, 137, 92));\n        DrawButton(b, this.FailRect, "FAIL [RB/F]", new Color(155, 62, 75));\n        DrawButton(b, this.HpFullRect, "HP 100% [1]", new Color(69, 111, 96));\n        DrawButton(b, this.HpLowRect, "HP 19% [2]", new Color(145, 91, 78));\n        DrawButton(b, this.ReturnRect, "RETURN TO GAME [B/Q]", new Color(74, 79, 105));\n        DrawButton(b, this.EndLabRect, "END LAB / RESTORE [START]", new Color(120, 75, 82));\n'''
new = '''        DrawButton(b, this.PassRect, "PASS [Y/P]", new Color(57, 137, 92));\n        DrawButton(b, this.FailRect, "FAIL [RB/F]", new Color(155, 62, 75));\n        DrawButton(b, this.HpFullRect, "ME 100% [1]", new Color(69, 111, 96));\n        DrawButton(b, this.HpLowRect, "ME 19% [2]", new Color(145, 91, 78));\n        DrawButton(b, this.DummyFullRect, "DUMMY 100% [LT/F7]", new Color(74, 105, 126));\n        DrawButton(b, this.DummyLowRect, "DUMMY 19% [R3/F6]", new Color(111, 82, 128));\n        DrawButton(b, this.ArenaRect, "TEST ARENA [RT/T]", new Color(56, 128, 126));\n        DrawButton(b, this.ReturnRect, "MINIMIZE [B/Q]", new Color(74, 79, 105));\n        DrawButton(b, this.EndLabRect, "END LAB / RESTORE [START]", new Color(120, 75, 82));\n'''
once(old, new)

if '    private void EnterArenaAndPlay()\n' not in s:
    once(
        '    private void ReturnToGame()\n',
        '''    private void EnterArenaAndPlay()\n    {\n        Game1.playSound("wand");\n        this.exitThisMenu();\n        this.Arena.EnterArena();\n    }\n\n    private void ReturnToGame()\n'''
    )

s = s.replace(
    '    private void EndLabAndRestore()\n    {\n        this.Lab.EndSession();',
    '    private void EndLabAndRestore()\n    {\n        this.Arena.ExitArena();\n        this.Lab.EndSession();'
)

if 'this.DummyFullRect = new Rectangle' not in s:
    pattern = re.compile(r'    private void RebuildRects\(\)\n    \{.*?\n    \}\n\n    private static void DrawWrapped', re.S)
    repl = '''    private void RebuildRects()\n    {\n        int left = this.xPositionOnScreen + 20;\n        int available = this.width - 40;\n        int gap = 7;\n        int row1Y = this.yPositionOnScreen + this.height - 106;\n        int row2Y = this.yPositionOnScreen + this.height - 56;\n\n        int x = left;\n        this.PrevRect = new Rectangle(x, row1Y, 102, 42); x += 102 + gap;\n        this.NextRect = new Rectangle(x, row1Y, 102, 42); x += 102 + gap;\n        this.LevelDownRect = new Rectangle(x, row1Y, 76, 42); x += 76 + gap;\n        this.LevelUpRect = new Rectangle(x, row1Y, 76, 42); x += 76 + gap;\n        this.EquipRect = new Rectangle(x, row1Y, 172, 42); x += 172 + gap;\n        this.UnequipRect = new Rectangle(x, row1Y, 188, 42); x += 188 + gap;\n        this.ResetRect = new Rectangle(x, row1Y, Math.Max(140, Math.Min(190, left + available - x)), 42);\n\n        x = left;\n        this.PassRect = new Rectangle(x, row2Y, 96, 42); x += 96 + gap;\n        this.FailRect = new Rectangle(x, row2Y, 96, 42); x += 96 + gap;\n        this.HpFullRect = new Rectangle(x, row2Y, 100, 42); x += 100 + gap;\n        this.HpLowRect = new Rectangle(x, row2Y, 94, 42); x += 94 + gap;\n        this.DummyFullRect = new Rectangle(x, row2Y, 145, 42); x += 145 + gap;\n        this.DummyLowRect = new Rectangle(x, row2Y, 142, 42); x += 142 + gap;\n        this.ArenaRect = new Rectangle(x, row2Y, 140, 42); x += 140 + gap;\n        this.ReturnRect = new Rectangle(x, row2Y, 128, 42); x += 128 + gap;\n        this.EndLabRect = new Rectangle(x, row2Y, Math.Max(175, Math.Min(220, left + available - x)), 42);\n\n        this.CloseRect = new Rectangle(this.xPositionOnScreen + this.width - 148, this.yPositionOnScreen + 18, 126, 38);\n    }\n\n    private static void DrawWrapped'''
    s, n = pattern.subn(repl, s, count=1)
    if n != 1:
        raise SystemExit('failed replacing RebuildRects')

p.write_text(s, encoding='utf-8')
print('Applied Card Test Arena menu integration')
