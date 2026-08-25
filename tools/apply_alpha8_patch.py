from pathlib import Path

ROOT = Path('src/Cardcha')

service = ROOT / 'Services/MimiMysteryTownService.cs'
text = service.read_text(encoding='utf-8')
old = '''            if (e.NewTime >= MerchantEndTime)
            {
                // Merchant hours are strict: at 17:00 MiMi disappears immediately.
                this.Flight = FlightState.None;
                this.MerchantFlight = false;
                this.HideNativeOffMap();
                this.MerchantDepartedToday = true;
                return;
            }
'''
new = '''            if (e.NewTime >= MerchantEndTime)
            {
                // At 17:00, let the player actually SEE MiMi leave when they're in Town.
                // Reuse the same broom departure presentation as mystery-phase MiMi:
                // lift above street level, draw above roofs, fly across Town, then despawn.
                if (!harsh && playerInTown && !this.MerchantDepartedToday && this.Flight == FlightState.None)
                {
                    this.StartMerchantDepartureFlight();
                }
                else if (this.Flight == FlightState.None)
                {
                    this.HideNativeOffMap();
                    this.MerchantDepartedToday = true;
                }
                return;
            }
'''
if old not in text:
    raise SystemExit('alpha.8 merchant 17:00 block not found')
service.write_text(text.replace(old, new, 1), encoding='utf-8')

# One clean package version.
for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    content = path.read_text(encoding='utf-8')
    if '0.2.0-alpha.7' not in content:
        raise SystemExit(f'alpha.7 version missing in {rel}')
    path.write_text(content.replace('0.2.0-alpha.7', '0.2.0-alpha.8'), encoding='utf-8')

print('alpha.8: restored visible 17:00 MiMi broom departure over Town rooftops')
