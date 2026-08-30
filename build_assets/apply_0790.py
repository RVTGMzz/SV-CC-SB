from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.9.0'


def set_version(path: Path):
    text = path.read_text()
    text, n = re.subn(r'0\.3\.0-alpha\.27\.0\.7\.\d+\.\d+', TARGET, text)
    if n == 0 and TARGET not in text:
        # Older source can still be 0.7.8.9, which the regex above matches; this is only a guard.
        raise AssertionError(f'No version replacement in {path}')
    path.write_text(text)


p = ROOT / 'Services/MimiMysteryTownService.cs'
text = p.read_text()

old = '''            this.EnforceCurrentTimeState(allowAnimation: Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true);\n            this.UpdateNativeWander();\n            this.SyncChaChaWithMimi();\n            this.WorldActors.UpdateChaChaEmotes(dialogueActive: Game1.activeClickableMenu is DialogueBox);\n'''
new = '''            this.EnforceCurrentTimeState(allowAnimation: Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true);\n            this.UpdateNativeWander();\n            this.SyncChaChaWithMimi();\n            // Mystery/??? phase: keep ChaCha visually quiet. Autonomous vanilla emotes can leave\n            // a tiny white emote bubble/frame hovering above this custom 32x32 actor on some runtimes.\n            // Merchant/story phases may still use ChaCha emotes after MiMi has been introduced.\n'''
if new not in text:
    if old not in text:
        raise AssertionError('mystery emote block missing')
    text = text.replace(old, new, 1)

p.write_text(text)

for f in [ROOT/'Cardcha.csproj', ROOT/'Directory.Build.targets', ROOT/'ModEntry.cs']:
    set_version(f)
manifest = json.loads((ROOT/'manifest.json').read_text())
manifest['Version'] = TARGET
(ROOT/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

final = p.read_text()
assert final.count('this.WorldActors.UpdateChaChaEmotes(') == 1, 'Only introduced merchant phase should retain autonomous ChaCha emotes'
assert 'Mystery/??? phase: keep ChaCha visually quiet.' in final
print('0.7.9.0 patch applied')
