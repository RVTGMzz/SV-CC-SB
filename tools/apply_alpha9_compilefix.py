from pathlib import Path

path = Path('src/Cardcha/Services/MimiMysteryTownService.cs')
text = path.read_text(encoding='utf-8')
old = '''        if (Game1.timeOfDay >= MerchantEndTime)
        {
            bool playerInTown = Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true;
            if (!IsHarshMerchantWeather() && playerInTown && !this.MerchantDepartedToday && this.Flight == FlightState.None)
'''
new = '''        if (Game1.timeOfDay >= MerchantEndTime)
        {
            bool viewerInTown = Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true;
            if (!IsHarshMerchantWeather() && viewerInTown && !this.MerchantDepartedToday && this.Flight == FlightState.None)
'''
if old not in text:
    raise SystemExit('alpha.9 compile fix pattern missing')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print('alpha.9 compile fix: merchant departure viewer variable')
