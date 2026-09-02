from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
CARDS_PATH = ROOT / 'assets/cards.json'
GENERATED_CS = ROOT / 'Services/GeneratedCardAutoAudit.cs'
REPORT_JSON = ROOT / 'assets/card_auto_audit.json'

cards = json.loads(CARDS_PATH.read_text(encoding='utf-8'))
active = sorted(
    [c for c in cards if 1 <= int(c.get('BaseId', 0)) <= 76],
    key=lambda c: int(c['BaseId'])
)
assert len(active) == 76, f'expected 76 active cards, got {len(active)}'

# Scan real runtime surfaces only. Test-Lab / scenario-runner files are deliberately excluded so the
# audit cannot pass just because a card name appears in its own test instructions or adapter.
scan_files = []
for path in [ROOT / 'ModEntry.cs', *sorted((ROOT / 'Services').glob('*.cs')), *sorted((ROOT / 'Patches').glob('*.cs'))]:
    if not path.exists():
        continue
    if path.name in {
        'CardTestLabService.cs',
        'CardTestArenaService.cs',
        'CardTestLabOverlayService.cs',
        'CardAutoScenarioRunnerService.cs',
        'GeneratedCardAutoAudit.cs',
    }:
        continue
    scan_files.append(path)

texts = {path: path.read_text(encoding='utf-8') for path in scan_files}
results = []
for card in active:
    card_id = str(card.get('Id', '')).strip()
    effect_key = str(card.get('EffectKey', '')).strip()
    max_level = max(1, int(card.get('MaxLevel', 1)))
    star_rules = [str(x).strip() for x in card.get('StarRules', [])]

    star_count_ok = len(star_rules) == max_level
    star_nonempty_ok = bool(star_rules) and all(star_rules)
    progression_ok = max_level == 1 or len(set(star_rules)) > 1

    id_token = f'"{card_id}"'
    effect_token = f'"{effect_key}"' if effect_key else ''
    ref_files = []
    id_refs = 0
    effect_refs = 0
    for path, text in texts.items():
        a = text.count(id_token)
        b = text.count(effect_token) if effect_token else 0
        if a or b:
            ref_files.append(path.relative_to(ROOT).as_posix())
            id_refs += a
            effect_refs += b

    runtime_refs = id_refs + effect_refs
    blocked = False

    reasons = []
    if blocked:
        status = 'BLOCKED'
        reasons.append('Boss Energy subsystem does not exist yet')
    else:
        if not star_count_ok:
            reasons.append(f'StarRules {len(star_rules)}/{max_level}')
        if not star_nonempty_ok:
            reasons.append('missing/blank StarRules')
        if not progression_ok:
            reasons.append('multi-level card has no visible level progression')
        if runtime_refs <= 0:
            reasons.append('no runtime source reference found')
        status = 'PASS' if not reasons else 'REVIEW'

    results.append({
        'baseId': int(card['BaseId']),
        'id': card_id,
        'name': card.get('Name', card_id),
        'effectKey': effect_key,
        'maxLevel': max_level,
        'starRuleCount': len(star_rules),
        'runtimeRefs': runtime_refs,
        'runtimeFiles': ref_files,
        'status': status,
        'reason': '; '.join(reasons) if reasons else 'runtime hook/reference + per-level display contract present',
    })

REPORT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def esc(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')

lines = [
    'using Cardcha.Models;',
    '',
    'namespace Cardcha.Services;',
    '',
    'internal enum CardAutoAuditStatus',
    '{',
    '    Pass,',
    '    Review,',
    '    Blocked',
    '}',
    '',
    'internal readonly record struct CardAutoAuditEntry(',
    '    CardAutoAuditStatus Status,',
    '    int RuntimeRefs,',
    '    int StarRuleCount,',
    '    int MaxLevel,',
    '    string Reason',
    ');',
    '',
    'internal static class GeneratedCardAutoAudit',
    '{',
    '    private static readonly Dictionary<string, CardAutoAuditEntry> Entries = new(StringComparer.OrdinalIgnoreCase)',
    '    {',
]
for r in results:
    status = {'PASS': 'Pass', 'REVIEW': 'Review', 'BLOCKED': 'Blocked'}[r['status']]
    lines.append(
        f'        ["{esc(r["id"])}"] = new(CardAutoAuditStatus.{status}, {r["runtimeRefs"]}, {r["starRuleCount"]}, {r["maxLevel"]}, "{esc(r["reason"])}"),'
    )
lines += [
    '    };',
    '',
    '    public static CardAutoAuditEntry Get(CardDefinition card)',
    '        => Entries.TryGetValue(card.Id, out CardAutoAuditEntry entry)',
    '            ? entry',
    '            : new(CardAutoAuditStatus.Review, 0, card.StarRules?.Count ?? 0, Math.Max(1, card.MaxLevel), "no generated audit entry");',
    '',
    '    public static (int pass, int review, int blocked) Counts()',
    '    {',
    '        int pass = Entries.Values.Count(entry => entry.Status == CardAutoAuditStatus.Pass);',
    '        int review = Entries.Values.Count(entry => entry.Status == CardAutoAuditStatus.Review);',
    '        int blocked = Entries.Values.Count(entry => entry.Status == CardAutoAuditStatus.Blocked);',
    '        return (pass, review, blocked);',
    '    }',
    '}',
    '',
]
GENERATED_CS.write_text('\n'.join(lines), encoding='utf-8')

counts = {
    'PASS': sum(r['status'] == 'PASS' for r in results),
    'REVIEW': sum(r['status'] == 'REVIEW' for r in results),
    'BLOCKED': sum(r['status'] == 'BLOCKED' for r in results),
}
print(f"Auto card contract audit: PASS={counts['PASS']} REVIEW={counts['REVIEW']} BLOCKED={counts['BLOCKED']}")
for r in results:
    if r['status'] != 'PASS':
        print(f"  #{r['baseId']:02} {r['id']}: {r['status']} - {r['reason']}")

assert all(r['starRuleCount'] == r['maxLevel'] for r in results), 'one or more active cards have StarRules/MaxLevel drift'
assert all(r['starRuleCount'] > 0 for r in results), 'one or more active cards have no StarRules'
