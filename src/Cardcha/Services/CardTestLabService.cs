using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Services;

internal enum CardLabVerdict
{
    Untested,
    Pass,
    Fail
}

/// <summary>
/// TEST-only orchestration for validating every active Base Set card without permanently mutating
/// the player's collection, loadout, card levels, or story-gating flags.
/// A Lab session may remain active while the menu is closed so the player can perform real gameplay tests.
/// </summary>
internal sealed class CardTestLabService
{
    private readonly CardRegistry Cards;
    private readonly SaveService Save;
    private readonly CombatService Combat;
    private readonly Dictionary<string, CardLabVerdict> Verdicts = new(StringComparer.OrdinalIgnoreCase);

    private bool SessionActive;
    private HashSet<string>? OwnedSnapshot;
    private List<string>? EquippedSnapshot;
    private Dictionary<string, int>? LevelsSnapshot;
    private bool MachineDeliveredSnapshot;
    private bool BinderUnlockedSnapshot;
    private bool MimiMeetupCompletedSnapshot;
    private string ActiveCardIdValue = "";
    private int ActiveLevelValue = 1;
    private bool TestCardEquippedValue;

    public CardTestLabService(CardRegistry cards, SaveService save, CombatService combat)
    {
        this.Cards = cards;
        this.Save = save;
        this.Combat = combat;
    }

    public IReadOnlyList<CardDefinition> ActiveCards
        => this.Cards.All
            .Where(card => card.StableBaseId >= 1 && card.StableBaseId <= 76)
            .OrderBy(card => card.StableBaseId)
            .ToList();

    public bool IsSessionActive => this.SessionActive;
    public string ActiveCardId => this.ActiveCardIdValue;
    public int ActiveLevel => Math.Max(1, this.ActiveLevelValue);
    public bool IsTestCardEquipped => this.TestCardEquippedValue;

    public void BeginSession()
    {
        if (this.SessionActive || !Context.IsWorldReady)
            return;

        SaveData data = this.Save.Data;
        this.OwnedSnapshot = new HashSet<string>(data.OwnedCards, StringComparer.OrdinalIgnoreCase);
        this.EquippedSnapshot = new List<string>(data.EquippedCards);
        this.LevelsSnapshot = new Dictionary<string, int>(data.CardLevels, StringComparer.OrdinalIgnoreCase);
        this.MachineDeliveredSnapshot = data.MachineDelivered;
        this.BinderUnlockedSnapshot = data.BinderUnlocked;
        this.MimiMeetupCompletedSnapshot = data.MimiMeetupCompleted;

        // Make LoadoutService.CardEffectsActive true only in memory. No SaveService.Save() call is made.
        data.MachineDelivered = true;
        data.BinderUnlocked = true;
        data.MimiMeetupCompleted = true;
        this.SessionActive = true;
        this.Combat.ResetVerificationTelemetry();
    }

    public void PrepareCard(CardDefinition card, int requestedLevel)
    {
        if (!Context.IsWorldReady)
            return;

        this.BeginSession();
        SaveData data = this.Save.Data;
        int level = Math.Clamp(requestedLevel, 1, Math.Max(1, card.MaxLevel));

        // Exactly one Lab card is active at a time. This keeps test results attributable to one effect.
        this.Combat.ResetRuntime();
        data.OwnedCards.Add(card.Id);
        data.EquippedCards.Clear();
        data.EquippedCards.Add(card.Id);
        data.CardLevels[card.Id] = level;
        this.ActiveCardIdValue = card.Id;
        this.ActiveLevelValue = level;
        this.TestCardEquippedValue = true;
        this.Combat.ResetVerificationTelemetry();
        this.Combat.SyncPassiveBuffs();
    }

    public void PrepareBaseline(CardDefinition card, int requestedLevel)
    {
        if (!Context.IsWorldReady)
            return;

        this.BeginSession();
        SaveData data = this.Save.Data;
        int level = Math.Clamp(requestedLevel, 1, Math.Max(1, card.MaxLevel));

        // Baseline mode keeps the selected card/level visible but equips no Cardcha card.
        this.Combat.ResetRuntime();
        data.OwnedCards.Add(card.Id);
        data.EquippedCards.Clear();
        data.CardLevels[card.Id] = level;
        this.ActiveCardIdValue = card.Id;
        this.ActiveLevelValue = level;
        this.TestCardEquippedValue = false;
        this.Combat.ResetVerificationTelemetry();
        this.Combat.SyncPassiveBuffs();
    }

    public bool IsSelectedCardEquipped(CardDefinition card)
        => this.SessionActive
           && this.TestCardEquippedValue
           && this.ActiveCardIdValue.Equals(card.Id, StringComparison.OrdinalIgnoreCase)
           && this.Save.Data.EquippedCards.Contains(card.Id, StringComparer.OrdinalIgnoreCase);

    public void EndSession()
    {
        if (!this.SessionActive)
            return;

        // Remove temporary runtime buffs while the test loadout is still active.
        this.Combat.ResetRuntime();

        SaveData data = this.Save.Data;
        if (this.OwnedSnapshot is not null)
            data.OwnedCards = new HashSet<string>(this.OwnedSnapshot, StringComparer.OrdinalIgnoreCase);
        if (this.EquippedSnapshot is not null)
            data.EquippedCards = new List<string>(this.EquippedSnapshot);
        if (this.LevelsSnapshot is not null)
            data.CardLevels = new Dictionary<string, int>(this.LevelsSnapshot, StringComparer.OrdinalIgnoreCase);

        data.MachineDelivered = this.MachineDeliveredSnapshot;
        data.BinderUnlocked = this.BinderUnlockedSnapshot;
        data.MimiMeetupCompleted = this.MimiMeetupCompletedSnapshot;

        this.SessionActive = false;
        this.OwnedSnapshot = null;
        this.EquippedSnapshot = null;
        this.LevelsSnapshot = null;
        this.ActiveCardIdValue = "";
        this.ActiveLevelValue = 1;
        this.TestCardEquippedValue = false;
        this.Combat.ResetVerificationTelemetry();
        this.Combat.SyncPassiveBuffs();
    }

    public void ResetTelemetry() => this.Combat.ResetVerificationTelemetry();

    public void SetVerdict(CardDefinition card, CardLabVerdict verdict)
        => this.Verdicts[card.Id] = verdict;

    public CardLabVerdict GetVerdict(CardDefinition card)
        => this.Verdicts.TryGetValue(card.Id, out CardLabVerdict verdict) ? verdict : CardLabVerdict.Untested;

    public (int pass, int fail, int untested) GetVerdictCounts()
    {
        IReadOnlyList<CardDefinition> cards = this.ActiveCards;
        int pass = cards.Count(card => this.GetVerdict(card) == CardLabVerdict.Pass);
        int fail = cards.Count(card => this.GetVerdict(card) == CardLabVerdict.Fail);
        return (pass, fail, cards.Count - pass - fail);
    }

    public void SetHealthPercent(double percent)
    {
        if (!Context.IsWorldReady || Game1.player is null)
            return;

        double clamped = Math.Clamp(percent, 0.01, 1.0);
        Game1.player.health = Math.Clamp((int)Math.Round(Game1.player.maxHealth * clamped), 1, Game1.player.maxHealth);
    }

    public string BuildTelemetry(CardDefinition selected)
    {
        if (!Context.IsWorldReady)
            return "World not ready.";

        SaveData data = this.Save.Data;
        int level = data.CardLevels.TryGetValue(selected.Id, out int storedLevel) ? storedLevel : 1;
        string selectedEquipped = this.IsSelectedCardEquipped(selected) ? "YES" : "no";
        string activeMode = string.IsNullOrWhiteSpace(this.ActiveCardIdValue)
            ? "not prepared"
            : this.TestCardEquippedValue
                ? $"EQUIPPED: {this.ActiveCardIdValue} Lv {this.ActiveLevelValue}"
                : $"BASELINE / UNEQUIPPED: {this.ActiveCardIdValue} Lv {this.ActiveLevelValue}";

        return
            $"Lab run: {activeMode}\n" +
            $"Selected: #{selected.StableBaseId:00} {selected.Name} | Lv {level} | Selected equipped {selectedEquipped}\n" +
            $"Player HP: {Game1.player.health}/{Game1.player.maxHealth}\n" +
            this.Combat.BuildVerificationReport();
    }

    public string BuildInstruction(CardDefinition card)
    {
        return card.Id.ToLowerInvariant() switch
        {
            "iron_edge" => "EQUIP & PLAY, hit the same enemy with a weapon, reopen Lab, then read Damage BEFORE->AFTER. Use UNEQUIP & PLAY for baseline.",
            "keen_eye" => "EQUIP & PLAY and attack normally. Reopen Lab and inspect Crit BEFORE->AFTER; compare with UNEQUIP baseline.",
            "vitality" => "EQUIP & PLAY. Max HP should increase immediately. UNEQUIP & PLAY should remove the temporary bonus.",
            "executioner" => "Lower an enemy below the threshold, EQUIP & PLAY, then hit it and compare outgoing damage against UNEQUIP baseline.",
            "first_strike" => "EQUIP & PLAY and hit a fresh/full-health enemy once, then hit again. The first-hit bonus should only apply once.",
            "armor_breaker" => "EQUIP & PLAY and hit one target repeatedly. Keep the same target so stack behavior can be observed.",
            "blood_fang" => "Take damage first, EQUIP & PLAY, then kill an enemy. Reopen Lab and inspect HP recovery + Blood Fang proc telemetry.",
            "chain_hunter" => "EQUIP & PLAY and kill enemies quickly. Reopen Lab to inspect Chain Hunter stacks and timer.",
            "phoenix_heart" => "Use only in TEST. EQUIP & PLAY, take lethal damage, then verify the once-per-day rescue before marking PASS.",
            "last_stand" => "Set HP 19%, EQUIP & PLAY, keep a living monster nearby, then reopen Lab and inspect LastStand state.",
            "soul_eater" => "EQUIP & PLAY, kill enemies, then reopen Lab to inspect Soul Eater kill counter, bonus percent, and timer.",
            "victory_charge" => "BLOCKED: Boss Energy does not exist yet. Do not mark PASS based on a substitute effect.",
            _ => BuildGenericInstruction(card)
        };
    }

    private static string BuildGenericInstruction(CardDefinition card)
    {
        string key = card.EffectKey?.ToLowerInvariant() ?? "";
        string id = card.Id.ToLowerInvariant();

        if (key.Contains("crit") || id.Contains("crit"))
            return "EQUIP & PLAY, attack repeatedly, reopen Lab and inspect Crit telemetry. Compare against UNEQUIP baseline.";
        if (key.Contains("damage") || id.Contains("strike") || id.Contains("hunter") || id.Contains("predator"))
            return "Use UNEQUIP & PLAY for a baseline hit, then EQUIP & PLAY and repeat the same test. Compare Damage BEFORE->AFTER.";
        if (key.Contains("health") || key.Contains("heal") || id.Contains("heart") || id.Contains("medic"))
            return "Change HP first, EQUIP & PLAY, trigger the exact condition, then reopen Lab and inspect HP/proc telemetry.";
        if (key.Contains("drop") || key.Contains("loot") || id.Contains("scavenger") || id.Contains("seeker") || id.Contains("treasure"))
            return "EQUIP & PLAY and defeat eligible enemies. Reopen Lab after several kills; RNG misses alone are not failures.";
        if (key.Contains("pull") || key.Contains("gacha") || id.Contains("cardmaster") || id.Contains("collector"))
            return "EQUIP & PLAY, perform the relevant Standard/Premium pull, then reopen Lab and verify the real gacha result/counter.";
        if (key.Contains("defense") || key.Contains("speed") || key.Contains("buff"))
            return "EQUIP & PLAY and observe the player/passive state. Use UNEQUIP & PLAY immediately after for comparison.";

        return "EQUIP & PLAY, perform the exact condition in the description, reopen Lab, then judge using telemetry + visible gameplay. UNEQUIP gives the baseline.";
    }
}
