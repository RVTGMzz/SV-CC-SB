from pathlib import Path

p = Path('src/Cardcha/Services/MilestoneBossService.cs')
s = p.read_text(encoding='utf-8')
old = '''        this.CuratorAdaptationStacks = 0;
        this.DecisionSerial = 0;
        this.EchoTargetTile = Point.Zero;
        this.EchoTargetTile2 = Point.Zero;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
    }

    private void RemoveMarkedActors'''
new = '''        this.EchoTargetTile = Point.Zero;
        this.EchoTargetTile2 = Point.Zero;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
        this.CuratorAdaptationStacks = 0;
        this.DecisionSerial = 0;
    }

    private void RemoveMarkedActors'''
if new not in s:
    if old not in s:
        raise RuntimeError('0673 pre-normalize: ResetRuntime anchor missing')
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('0673 pre-normalize PASS')
