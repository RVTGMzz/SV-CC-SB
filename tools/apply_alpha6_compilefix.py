from pathlib import Path

p = Path('src/Cardcha/UI/CardchaBinderMenuV2.cs')
s = p.read_text(encoding='utf-8')
s = s.replace('string body = description + "\n" + ModEntry.T("binder.scrap-tooltip.count", new { count });', 'string body = description + "\\n" + ModEntry.T("binder.scrap-tooltip.count", new { count });')
p.write_text(s, encoding='utf-8')
print('alpha.6 compile fix: scrap tooltip newline escaped')
