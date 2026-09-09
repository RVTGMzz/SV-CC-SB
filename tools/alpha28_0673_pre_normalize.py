from pathlib import Path

p = Path('src/Cardcha/Services/MilestoneBossService.cs')
s = p.read_text(encoding='utf-8')

# Once 0673 has already been materialized, the route-confirm fields prove this
# source no longer needs the 0672-only anchor normalization.
if 'private long RouteConfirmUntilMs;' in s and 'private MilestoneBossKind? RouteConfirmKind;' in s:
    print('0673 pre-normalize: already materialized, no-op')
else:
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
