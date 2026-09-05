from pathlib import Path
import subprocess
import sys

p = Path(__file__).with_name('alpha28_0647e_airship_physical_depth_rebuild.py')
text = p.read_text(encoding='utf-8')
old = '    return "\\n".join(rows)'
new = '    return ",\\n".join(rows)'
if old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding='utf-8')
elif new not in text:
    raise RuntimeError('0647E csv_layer anchor missing')
subprocess.check_call([sys.executable, str(p)])
