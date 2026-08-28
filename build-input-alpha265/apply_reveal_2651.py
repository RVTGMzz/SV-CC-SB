from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
p = root / "UI" / "CardchaRevealMenu.cs"
s = p.read_text(encoding="utf-8")

# Cross-input debounce: some controller/Steam-Input setups can emit a gamepad activation
# and a synthetic mouse activation for the same physical press. Without a short lock,
# a revealed card can open its detail panel and immediately close it again in the same press.
if "ResultActivationDebounceMs" not in s:
    marker = "    private int LastDetailResultIndex = -1;\n"
    addition = (
        marker
        + "    private const double ResultActivationDebounceMs = 180d;\n"
        + "    private int LastActivatedResultIndex = -1;\n"
        + "    private double LastResultActivationAtMs = -10000d;\n"
        + "    private double DetailOpenedAtMs = -10000d;\n"
    )
    if marker not in s:
        raise SystemExit("CardchaRevealMenu field insertion point not found")
    s = s.replace(marker, addition, 1)

# Single-pull controller should focus the result card too, not Continue.
old_snap = '''        if (this.Phase != RevealPhase.Results)\n            this.currentlySnappedComponent = this.Skip;\n        else if (this.Results.Count > 1)\n            this.currentlySnappedComponent = this.ResultButtons.FirstOrDefault() ?? this.Continue;\n        else\n            this.currentlySnappedComponent = this.Continue;\n'''
new_snap = '''        if (this.Phase != RevealPhase.Results)\n            this.currentlySnappedComponent = this.Skip;\n        else\n            this.currentlySnappedComponent = this.ResultButtons.FirstOrDefault() ?? this.Continue;\n'''
if old_snap in s:
    s = s.replace(old_snap, new_snap, 1)
elif new_snap not in s:
    raise SystemExit("CardchaRevealMenu snapToDefault pattern not found")

# Don't let a synthetic second input instantly close a detail panel that just opened.
old_mouse_modal = '''        if (this.SelectedResultIndex >= 0)\n        {\n            int closedIndex = this.SelectedResultIndex;\n'''
new_mouse_modal = '''        if (this.SelectedResultIndex >= 0)\n        {\n            if (Environment.TickCount64 - this.DetailOpenedAtMs < ResultActivationDebounceMs)\n                return;\n\n            int closedIndex = this.SelectedResultIndex;\n'''
if old_mouse_modal in s:
    s = s.replace(old_mouse_modal, new_mouse_modal, 1)
elif new_mouse_modal not in s:
    raise SystemExit("CardchaRevealMenu mouse modal pattern not found")

old_pad_modal = '''        if (this.Phase == RevealPhase.Results && this.SelectedResultIndex >= 0)\n        {\n            if (this.Controller.IsConfirm(b) || this.Controller.IsExit(b))\n            {\n                int closedIndex = this.SelectedResultIndex;\n'''
new_pad_modal = '''        if (this.Phase == RevealPhase.Results && this.SelectedResultIndex >= 0)\n        {\n            if (this.Controller.IsConfirm(b) || this.Controller.IsExit(b))\n            {\n                if (this.Controller.IsConfirm(b)\n                    && Environment.TickCount64 - this.DetailOpenedAtMs < ResultActivationDebounceMs)\n                    return;\n\n                int closedIndex = this.SelectedResultIndex;\n'''
if old_pad_modal in s:
    s = s.replace(old_pad_modal, new_pad_modal, 1)
elif new_pad_modal not in s:
    raise SystemExit("CardchaRevealMenu gamepad modal pattern not found")

# Debounce repeated/synthetic activations of the same result. Intentional second presses after
# the short lock still work: facedown -> reveal, revealed -> open details, repeatable forever.
old_reveal = '''    private void RevealResult(int index)\n    {\n        if (index < 0 || index >= this.Results.Count)\n            return;\n\n        if (this.Revealed[index])\n        {\n            this.SelectedResultIndex = index;\n'''
new_reveal = '''    private void RevealResult(int index)\n    {\n        if (index < 0 || index >= this.Results.Count)\n            return;\n\n        double now = Environment.TickCount64;\n        if (index == this.LastActivatedResultIndex\n            && now - this.LastResultActivationAtMs < ResultActivationDebounceMs)\n            return;\n\n        this.LastActivatedResultIndex = index;\n        this.LastResultActivationAtMs = now;\n\n        if (this.Revealed[index])\n        {\n            this.SelectedResultIndex = index;\n            this.DetailOpenedAtMs = now;\n'''
if old_reveal in s:
    s = s.replace(old_reveal, new_reveal, 1)
elif new_reveal not in s:
    raise SystemExit("CardchaRevealMenu RevealResult pattern not found")

p.write_text(s, encoding="utf-8")

# Hotfix version.
csproj = root / "Cardcha.csproj"
t = csproj.read_text(encoding="utf-8")
t = re.sub(r"<Version>[^<]+</Version>", "<Version>0.3.0-alpha.26.5.1</Version>", t, count=1)
csproj.write_text(t, encoding="utf-8")

manifest = root / "manifest.json"
t = manifest.read_text(encoding="utf-8")
t = re.sub(r'"Version"\s*:\s*"[^"]+"', '"Version": "0.3.0-alpha.26.5.1"', t, count=1)
manifest.write_text(t, encoding="utf-8")

print("alpha26.5.1 reveal reopen hotfix applied")
