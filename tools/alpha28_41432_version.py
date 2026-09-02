from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.3.6'

manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

csproj = ROOT / 'Cardcha.csproj'
s = csproj.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
csproj.write_text(s, encoding='utf-8')

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.3.6 Card Test Lab automatic contract audit + per-level UI. -->\n  <Target Name="CardchaAlpha28041436Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')

entry = ROOT / 'ModEntry.cs'
text = entry.read_text(encoding='utf-8')
text = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.3\.\d+ CARD TEST ARENA TEST',
    f'Cardcha! v{VERSION} CARD TEST ARENA TEST',
    text
)
entry.write_text(text, encoding='utf-8')

print(f'Version set to {VERSION}')
