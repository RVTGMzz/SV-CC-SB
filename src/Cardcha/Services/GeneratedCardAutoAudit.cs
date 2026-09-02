using Cardcha.Models;

namespace Cardcha.Services;

internal enum CardAutoAuditStatus
{
    Pass,
    Review,
    Blocked
}

internal readonly record struct CardAutoAuditEntry(
    CardAutoAuditStatus Status,
    int RuntimeRefs,
    int StarRuleCount,
    int MaxLevel,
    string Reason
);

internal static class GeneratedCardAutoAudit
{
    private static readonly Dictionary<string, CardAutoAuditEntry> Entries = new(StringComparer.OrdinalIgnoreCase)
    {
        ["iron_edge"] = new(CardAutoAuditStatus.Pass, 4, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["quick_hands"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["keen_eye"] = new(CardAutoAuditStatus.Pass, 4, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["heavy_blow"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["first_strike"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["finisher"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["hunters_focus"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["steady_grip"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["thick_hide"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["vitality"] = new(CardAutoAuditStatus.Pass, 3, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["second_breath"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["guard_step"] = new(CardAutoAuditStatus.Pass, 4, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["swift_feet"] = new(CardAutoAuditStatus.Pass, 5, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["backstep"] = new(CardAutoAuditStatus.Pass, 4, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["stalwart"] = new(CardAutoAuditStatus.Pass, 3, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["last_push"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["calm_heart"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["scavenger"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["essence_finder"] = new(CardAutoAuditStatus.Pass, 4, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["victory_charge"] = new(CardAutoAuditStatus.Pass, 4, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["lucky_pocket"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["treasure_magnet"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["explorer"] = new(CardAutoAuditStatus.Pass, 3, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["patient_hunter"] = new(CardAutoAuditStatus.Pass, 2, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["rhythm"] = new(CardAutoAuditStatus.Pass, 6, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["bruiser"] = new(CardAutoAuditStatus.Pass, 4, 5, 5, "runtime hook/reference + per-level display contract present"),
        ["resilient"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["momentum"] = new(CardAutoAuditStatus.Pass, 3, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["blood_fang"] = new(CardAutoAuditStatus.Pass, 6, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["executioner"] = new(CardAutoAuditStatus.Pass, 4, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["opening_gambit"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["deadeye"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["predator"] = new(CardAutoAuditStatus.Pass, 3, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["adrenaline"] = new(CardAutoAuditStatus.Pass, 5, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["counterforce"] = new(CardAutoAuditStatus.Pass, 6, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["iron_will"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["field_medic"] = new(CardAutoAuditStatus.Pass, 4, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["lifeline"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["armor_breaker"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["crushing_impact"] = new(CardAutoAuditStatus.Pass, 4, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["fleet_hunter"] = new(CardAutoAuditStatus.Pass, 3, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["treasure_eye"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["card_seeker"] = new(CardAutoAuditStatus.Pass, 6, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["dust_collector"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["fortune_chain"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["battle_trance"] = new(CardAutoAuditStatus.Pass, 3, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["vanguard"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["marked_prey"] = new(CardAutoAuditStatus.Pass, 4, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["unyielding"] = new(CardAutoAuditStatus.Pass, 3, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["collectors_instinct"] = new(CardAutoAuditStatus.Pass, 2, 4, 4, "runtime hook/reference + per-level display contract present"),
        ["berserker_soul"] = new(CardAutoAuditStatus.Pass, 3, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["chain_hunter"] = new(CardAutoAuditStatus.Pass, 8, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["soul_siphon"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["phantom_step"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["reapers_mark"] = new(CardAutoAuditStatus.Pass, 3, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["stoneheart"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["last_stand"] = new(CardAutoAuditStatus.Pass, 14, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["war_drum"] = new(CardAutoAuditStatus.Pass, 5, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["treasure_hunter"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["golden_hand"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["arcane_recycler"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["mirror_guard"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["relentless"] = new(CardAutoAuditStatus.Pass, 3, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["overclock"] = new(CardAutoAuditStatus.Pass, 3, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["lucky_break"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["battle_scholar"] = new(CardAutoAuditStatus.Pass, 6, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["phoenix_heart"] = new(CardAutoAuditStatus.Pass, 6, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["void_walker"] = new(CardAutoAuditStatus.Pass, 8, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["soul_eater"] = new(CardAutoAuditStatus.Pass, 8, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["time_breaker"] = new(CardAutoAuditStatus.Pass, 5, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["titans_grip"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["perfect_hunter"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["kings_ransom"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["cardmaster"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["guardian_angel"] = new(CardAutoAuditStatus.Pass, 2, 3, 3, "runtime hook/reference + per-level display contract present"),
        ["apex_predator"] = new(CardAutoAuditStatus.Pass, 4, 3, 3, "runtime hook/reference + per-level display contract present"),
    };

    public static CardAutoAuditEntry Get(CardDefinition card)
        => Entries.TryGetValue(card.Id, out CardAutoAuditEntry entry)
            ? entry
            : new(CardAutoAuditStatus.Review, 0, card.StarRules?.Count ?? 0, Math.Max(1, card.MaxLevel), "no generated audit entry");

    public static (int pass, int review, int blocked) Counts()
    {
        int pass = Entries.Values.Count(entry => entry.Status == CardAutoAuditStatus.Pass);
        int review = Entries.Values.Count(entry => entry.Status == CardAutoAuditStatus.Review);
        int blocked = Entries.Values.Count(entry => entry.Status == CardAutoAuditStatus.Blocked);
        return (pass, review, blocked);
    }
}
