from pathlib import Path

patch_path = Path('tools/apply_beta3_mimi_split.py')
text = patch_path.read_text(encoding='utf-8')

# The release ZIP gets the approved 80-card atlas injected after CI compilation.
# CI only needs to compile and validate the two-actor MiMi state split here.
start = text.index('# --- Carry forward beta.2 80-card visuals. ---')
end = text.index('# Build guards.')
text = text[:start] + text[end:]
text = text.replace("print('atlas:', width, 'x', height, sha)\n", '')
text = text.replace(
    "print('beta.3: mystery/real MiMi actor split + 80-card visuals applied')",
    "print('beta.3: mystery/real MiMi actor split applied; release visuals injected after CI')",
)

exec(compile(text, str(patch_path), 'exec'))
