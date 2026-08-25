from pathlib import Path
import struct

root = Path('src/Cardcha')

# Use the approved high-detail portable machine artwork in MiMi's shop.
shop_p = root / 'UI/MimiScrapShopMenu.cs'
shop = shop_p.read_text(encoding='utf-8')
shop = shop.replace(
    'this.MachineTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/portable_machine.png");',
    'this.MachineTexture = ModEntry.StaticHelper?.ModContent.Load<Texture2D>("assets/portable_machine_ui.png");'
)
shop = shop.replace(
'''            b.Draw(
                this.MachineTexture,
                machineTarget,
                new Rectangle(0, 0, 16, 32),
                Color.White
            );''',
'''            b.Draw(
                this.MachineTexture,
                machineTarget,
                this.MachineTexture.Bounds,
                Color.White
            );'''
)
if 'assets/portable_machine_ui.png' not in shop or 'this.MachineTexture.Bounds' not in shop:
    raise SystemExit('alpha.5 portable shop visual patch did not apply')
shop_p.write_text(shop, encoding='utf-8')

# portable_machine.png is intentionally kept 16x32 because Stardew BigCraftable
# sprites require that footprint. Its pixels are now derived from the approved
# 48x96 portable_machine_ui.png so hotbar/inventory use the same visual identity.
png = (root / 'assets/portable_machine.png').read_bytes()
if png[:8] != b'\x89PNG\r\n\x1a\n':
    raise SystemExit('portable_machine.png is not a PNG')
w, h = struct.unpack('>II', png[16:24])
if (w, h) != (16, 32):
    raise SystemExit(f'portable_machine.png must stay 16x32 for BigCraftable, got {w}x{h}')

# One clean test package version.
for rel in ('Cardcha.csproj', 'manifest.json'):
    p = root / rel
    s = p.read_text(encoding='utf-8')
    s = s.replace('0.2.0-alpha.4', '0.2.0-alpha.5')
    p.write_text(s, encoding='utf-8')

print('alpha.5: portable machine now matches portable_machine_ui visual')
