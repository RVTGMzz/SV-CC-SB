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
/// TEST-only orchestration for visually validating every active Base Set card without permanently
/// mutating the player's collection, loadout, card levels, or story-gating flags.
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

        // Reset transient state before swapping cards so buffs such as Vitality are removed cleanly.
        this.Combat.ResetRuntime();
        data.OwnedCards.Add(card.Id);
        data.EquippedCards.Clear();
        data.EquippedCards.Add(card.Id);
        data.CardLevels[card.Id] = level;
        this.Combat.ResetVerificationTelemetry();
        this.Combat.SyncPassiveBuffs();
    }

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
        string equipped = data.EquippedCards.Contains(selected.Id, StringComparer.OrdinalIgnoreCase) ? "YES" : "no";
        return
            $"Selected: #{selected.StableBaseId:00} {selected.Name} | Lv {level} | Equipped {equipped}\n" +
            $"Player HP: {Game1.player.health}/{Game1.player.maxHealth}\n" +
            this.Combat.BuildVerificationReport();
    }

    public string BuildInstruction(CardDefinition card)
    {
        return card.Id.ToLowerInvariant() switch
        {
            "iron_edge" => "Hit the same enemy with a weapon. Watch Damage last BEFORE->AFTER.",
            "keen_eye" => "Attack normally. Watch Crit last BEFORE->AFTER; a modified crit hook proves the bonus is wired.",
            "vitality" => "Press PREPARE. Max HP should increase immediately; closing Lab must restore it.",
            "executioner" => "Lower an enemy below the threshold, then hit it and compare outgoing damage.",
            "first_strike" => "Hit a fresh/full-health enemy once, then hit again. First hit should receive the card bonus only once.",
            "armor_breaker" => "Hit one target repeatedly. Keep the same target so stack behavior can be observed.",
            "blood_fang" => "Take damage first, then kill an enemy. Watch HP recovery and Blood Fang proc telemetry.",
            "chain_hunter" => "Kill enemies quickly. Watch Chain Hunter stacks and remaining timer in telemetry.",
            "phoenix_heart" => "Use only on a disposable TEST save state. Take lethal damage and verify the once-per-day rescue.",
            "last_stand" => "Keep a living monster nearby, press HP 19%, then watch the LastStand passive state.",
            "soul_eater" => "Kill enemies and watch Soul Eater kill counter, bonus percent, and timer.",
            "victory_charge" => "BLOCKED: Boss Energy does not exist yet. Do not mark PASS based on a substitute effect.",
            _ => BuildGenericInstruction(card)
        };
    }

    private static string BuildGenericInstruction(CardDefinition card)
    {
        string key = card.EffectKey?.ToLowerInvariant() ?? "";
        string id = card.Id.ToLowerInvariant();

        if (key.Contains("crit") || id.Contains("crit"))
            return "Attack repeatedly and watch Crit telemetry. A modified hook is visible even if RNG does not crit.";
        if (key.Contains("damage") || id.Contains("strike") || id.Contains("hunter") || id.Contains("predator"))
            return "Attack an enemy and compare Damage BEFORE->AFTER in telemetry.";
        if (key.Contains("health") || key.Contains("heal") || id.Contains("heart") || id.Contains("medic"))
            return "Change HP first, trigger the card condition, then watch the HP line and proc counters.";
        if (key.Contains("drop") || key.Contains("loot") || id.Contains("scavenger") || id.Contains("seeker") || id.Contains("treasure"))
            return "Defeat eligible enemies and watch the real drop result. RNG misses are not failures by themselves.";
        if (key.Contains("pull") || key.Contains("gacha") || id.Contains("cardmaster") || id.Contains("collector"))
            return "Prepare this card, then perform the relevant Standard/Premium pull and verify the real gacha result/counter.";
        if (key.Contains("defense") || key.Contains("speed") || key.Contains("buff"))
            return "Press PREPARE and observe the player/passive buff telemetry; enter combat if the condition requires a monster.";

        return "Prepare the card, perform the exact condition written in its description, and use telemetry + visible gameplay result together.";
    }
}
