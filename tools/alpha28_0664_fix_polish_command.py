from pathlib import Path

p = Path('src/Cardcha/ModEntry.cs')
s = p.read_text(encoding='utf-8')
needle = '        helper.ConsoleCommands.Add("cardcha_boss1_visual_status", "Show Verdant Guardian visual animation state.", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe() + "\\n" + this.VerdantSummons.Describe(), LogLevel.Alert));\n'
insert = needle + '        helper.ConsoleCommands.Add("cardcha_boss1_polish_status", "Show Verdant arena cinematic/camera/sound polish state.", (_, _) => this.Monitor.Log(this.VerdantArenaPolish.Describe(), LogLevel.Alert));\n'
if 'cardcha_boss1_polish_status' not in s:
    if needle not in s:
        raise RuntimeError('0664 summon-aware boss visual command anchor missing')
    s = s.replace(needle, insert, 1)
p.write_text(s, encoding='utf-8')
print('0664 polish status command patched')
