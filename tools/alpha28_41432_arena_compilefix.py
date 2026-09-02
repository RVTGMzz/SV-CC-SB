from pathlib import Path

p = Path('src/Cardcha/Services/CardTestArenaService.cs')
s = p.read_text(encoding='utf-8')
s = s.replace('    public void OnSaveLoaded()\n', '    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)\n')
s = s.replace('    public void OnReturnedToTitle()\n', '    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)\n')
s = s.replace('    public void OnUpdateTicked(UpdateTickedEventArgs e)\n', '    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)\n')
p.write_text(s, encoding='utf-8')
print('Card Test Arena event signatures fixed')
