
using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;
using System.Security.Cryptography;
using System.Text;

namespace Cardcha.Services;

internal sealed class SaveService
{
    private const string SaveKey = "cardcha-save-v1";
    private const int CurrentSchemaVersion = 11;
    private readonly IModHelper Helper;

    public SaveData Data { get; private set; } = new();

    public bool LastPersistenceCheckPassed { get; private set; } = true;
    public string LastPersistenceMessage { get; private set; } = "Not checked yet.";
    public string CurrentFingerprint => ComputeFingerprint(this.Data);

    public SaveService(IModHelper helper)
    {
        this.Helper = helper;
    }

    public void Load()
    {
        this.Data = this.Helper.Data.ReadSaveData<SaveData>(SaveKey) ?? new SaveData();

        if (this.Data.GachaSeed == 0)
            this.Data.GachaSeed = CreateSeed();

        int loadedSchema = this.Data.SchemaVersion;
        Normalize();

        // v4: the Wizard-delivered physical book is represented by the persistent Binder tab.
        // Existing prototype saves which already received the machine should keep access.
        if (loadedSchema < 4 && this.Data.MachineDelivered)
            this.Data.BinderUnlocked = true;

        // v5: Binder V2 progression begins with two active slots and per-card levels.
        if (loadedSchema < 5)
        {
            this.Data.ActiveCardSlotCount = Math.Clamp(this.Data.ActiveCardSlotCount <= 0 ? 2 : this.Data.ActiveCardSlotCount, 2, 5);

            foreach (string cardId in this.Data.OwnedCards)
            {
                if (!this.Data.CardLevels.ContainsKey(cardId) || this.Data.CardLevels[cardId] < 1)
                    this.Data.CardLevels[cardId] = 1;
            }
        }

        // v6: duplicate pulls are stored as same-card upgrade copies instead of auto-dusting.
        if (loadedSchema < 6)
            this.Data.CardCopies ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);

        // v7: MiMi becomes the Chapter 1 story lead.
        // Existing saves which already received the Machine/Book are treated as
        // having completed Chapter 1 so they don't get duplicate onboarding.
        if (loadedSchema < 7)
        {
            this.Data.CardchaStoryChapter = 1;

            if (this.Data.MachineDelivered || this.Data.BinderUnlocked)
            {
                this.Data.MimiIntroSeen = true;
                this.Data.MimiMeetupPending = false;
                this.Data.MimiMeetupCompleted = true;
                this.Data.CardchaStoryStage = 3;
            }
            else if (this.Data.FirstScrapTriggered)
            {
                this.Data.MimiIntroSeen = false;
                this.Data.MimiMeetupPending = false;
                this.Data.MimiMeetupCompleted = false;
                this.Data.CardchaStoryStage = 1;
            }
        }

        // v8: MiMi explicitly lends ChaCha, and Chapter 1 ends after the first real pull.
        if (loadedSchema < 8)
        {
            if (this.Data.MachineDelivered || this.Data.BinderUnlocked)
            {
                this.Data.ChaChaLoaned = true;

                if (this.Data.PullIndex > 0)
                {
                    this.Data.FirstPullQuestActive = false;
                    this.Data.FirstPullCompleted = true;
                    this.Data.Chapter1Completed = true;
                    this.Data.CardchaStoryStage = Math.Max(this.Data.CardchaStoryStage, 4);
                }
                else
                {
                    this.Data.FirstPullQuestActive = true;
                    this.Data.FirstPullCompleted = false;
                    this.Data.Chapter1Completed = false;
                    this.Data.CardchaStoryStage = Math.Max(this.Data.CardchaStoryStage, 3);
                }
            }
        }

        // v9: Cardboard/Shiny Scrap move into the Binder wallet instead of backpack slots.
        // Existing completed-story saves get MiMi's merchant routine immediately.
        if (loadedSchema < 9)
        {
            this.Data.CardboardScraps = Math.Max(0, this.Data.CardboardScraps);
            this.Data.ShinyScraps = Math.Max(0, this.Data.ShinyScraps);

            if (this.Data.MimiMeetupCompleted && this.Data.MimiMerchantUnlockedDay < 0)
                this.Data.MimiMerchantUnlockedDay = Math.Max(-1, Game1.Date.TotalDays - 1);
        }

        // v10: the Wizard-house appointment becomes a real quest and expires into a
        // forced third-morning home visit. Old pending saves start their countdown today
        // instead of unexpectedly firing the doorstep scene immediately after updating.
        if (loadedSchema < 10)
        {
            if (this.Data.MimiMeetupPending && !this.Data.MimiMeetupCompleted)
                this.Data.MimiMeetupOfferedDay = Game1.Date.TotalDays;
            else if (this.Data.MimiMeetupCompleted)
                this.Data.MimiMeetupOfferedDay = -1;
        }

        // v11: portable-machine entitlement is tracked separately from the physical item.
        // No automatic grant on migration; the device is either bought from MiMi or earned at
        // 50 unique cards. Existing debug items are detected by PortableMachineService on load.
        if (loadedSchema < 11)
        {
            this.Data.PortableMachinePurchased = false;
            this.Data.PortableMachineGifted = false;
        }

        if (loadedSchema < CurrentSchemaVersion)
        {
            this.Data.SchemaVersion = CurrentSchemaVersion;
            this.Data.LastStateFingerprint = ComputeFingerprint(this.Data);
            this.LastPersistenceCheckPassed = true;
            this.LastPersistenceMessage =
                $"Migrated Cardcha save schema {loadedSchema} -> {CurrentSchemaVersion}; fingerprint initialized ({Short(this.Data.LastStateFingerprint)}).";

            // Persist the migration immediately without touching collection/loadout state.
            this.Save();
            return;
        }

        this.Data.SchemaVersion = CurrentSchemaVersion;

        string expected = this.Data.LastStateFingerprint ?? "";
        string actual = ComputeFingerprint(this.Data);

        if (string.IsNullOrWhiteSpace(expected))
        {
            this.Data.LastStateFingerprint = actual;
            this.LastPersistenceCheckPassed = true;
            this.LastPersistenceMessage =
                $"Persistence fingerprint initialized ({Short(actual)}).";
            this.Save();
            return;
        }

        this.LastPersistenceCheckPassed = expected.Equals(actual, StringComparison.OrdinalIgnoreCase);
        this.LastPersistenceMessage = this.LastPersistenceCheckPassed
            ? $"PASS — save state matches fingerprint {Short(actual)}."
            : $"WARNING — loaded state fingerprint changed. Saved={Short(expected)} Loaded={Short(actual)}. Data was kept; no automatic rollback was performed.";
    }

    public void Save()
    {
        if (!Context.IsWorldReady)
            return;

        Normalize();
        this.Data.SchemaVersion = CurrentSchemaVersion;
        this.Data.LastStateFingerprint = ComputeFingerprint(this.Data);
        this.Helper.Data.WriteSaveData(SaveKey, this.Data);
    }

    public void Clear()
    {
        this.Data = new SaveData();
        this.LastPersistenceCheckPassed = true;
        this.LastPersistenceMessage = "Not checked yet.";
    }

    public void ResetForNewDay()
        => this.Data.PhoenixHeartUsedToday = false;

    public string DescribePersistence()
        => $"{this.LastPersistenceMessage} Current={Short(this.CurrentFingerprint)}";

    private void Normalize()
    {
        this.Data.EquippedCards ??= new List<string>();
        this.Data.OwnedCards ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        this.Data.CardLevels ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        this.Data.CardCopies ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        this.Data.LastStateFingerprint ??= "";
        this.Data.CardboardScraps = Math.Max(0, this.Data.CardboardScraps);
        this.Data.ShinyScraps = Math.Max(0, this.Data.ShinyScraps);

        this.Data.ActiveCardSlotCount = Math.Clamp(this.Data.ActiveCardSlotCount <= 0 ? 2 : this.Data.ActiveCardSlotCount, 2, 5);

        this.Data.EquippedCards = this.Data.EquippedCards
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Take(5)
            .ToList();

        // Card levels are stored only for owned cards and always clamped to at least 1.
        Dictionary<string, int> levels = new(StringComparer.OrdinalIgnoreCase);
        foreach (string cardId in this.Data.OwnedCards.Where(p => !string.IsNullOrWhiteSpace(p)))
        {
            int level = 1;
            if (this.Data.CardLevels.TryGetValue(cardId, out int stored) && stored > 1)
                level = stored;

            levels[cardId] = Math.Clamp(level, 1, 5);
        }
        this.Data.CardLevels = levels;

        Dictionary<string, int> copies = new(StringComparer.OrdinalIgnoreCase);
        foreach ((string id, int count) in this.Data.CardCopies)
        {
            if (!string.IsNullOrWhiteSpace(id) && count > 0)
                copies[id] = count;
        }
        this.Data.CardCopies = copies;
    }

    private static string ComputeFingerprint(SaveData data)
    {
        string owned = string.Join(
            ",",
            (data.OwnedCards ?? new HashSet<string>())
                .Where(p => !string.IsNullOrWhiteSpace(p))
                .OrderBy(p => p, StringComparer.OrdinalIgnoreCase)
        );

        string equipped = string.Join(
            ",",
            (data.EquippedCards ?? new List<string>())
                .Where(p => !string.IsNullOrWhiteSpace(p))
        );

        string levels = string.Join(
            ",",
            (data.CardLevels ?? new Dictionary<string, int>())
                .OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase)
                .Select(p => $"{p.Key}:{p.Value}")
        );

        string copies = string.Join(
            ",",
            (data.CardCopies ?? new Dictionary<string, int>())
                .OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase)
                .Select(p => $"{p.Key}:{p.Value}")
        );

        string canonical = string.Join(
            "|",
            CurrentSchemaVersion,
            owned,
            equipped,
            levels,
            copies,
            data.ActiveCardSlotCount,
            data.SuspiciousDust,
            data.PullIndex,
            data.GachaSeed,
            data.StandardSinceRare,
            data.StandardSinceEpic,
            data.StandardSinceLegendary,
            data.PremiumSinceEpic,
            data.PremiumSinceLegendary,
            data.PhoenixHeartUsedToday ? 1 : 0,
            data.CardboardScraps,
            data.ShinyScraps,
            data.FirstScrapTriggered ? 1 : 0,
            data.FirstScrapDay,
            data.MachineLetterQueued ? 1 : 0,
            data.MachineDelivered ? 1 : 0,
            data.BinderUnlocked ? 1 : 0,
            data.MimiIntroSeen ? 1 : 0,
            data.MimiMeetupPending ? 1 : 0,
            data.MimiMeetupCompleted ? 1 : 0,
            data.ChaChaLoaned ? 1 : 0,
            data.FirstPullQuestActive ? 1 : 0,
            data.FirstPullCompleted ? 1 : 0,
            data.Chapter1Completed ? 1 : 0,
            data.CardchaStoryChapter,
            data.CardchaStoryStage,
            data.MimiMerchantUnlockedDay,
            data.FirstScrapPickupNoticeShown ? 1 : 0,
            data.MimiMeetupOfferedDay,
            data.PortableMachinePurchased ? 1 : 0,
            data.PortableMachineGifted ? 1 : 0
        );

        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(canonical));
        return Convert.ToHexString(hash);
    }

    private static string Short(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return "none";

        return value.Length <= 12 ? value : value[..12];
    }

    private static ulong CreateSeed()
    {
        unchecked
        {
            ulong unique = (ulong)Math.Max(1L, Game1.uniqueIDForThisGame);
            ulong player = (ulong)Math.Max(1L, Game1.player?.UniqueMultiplayerID ?? 1L);
            return Mix(unique ^ (player * 0x9E3779B97F4A7C15UL));
        }
    }

    internal static ulong Mix(ulong x)
    {
        x ^= x >> 30;
        x *= 0xBF58476D1CE4E5B9UL;
        x ^= x >> 27;
        x *= 0x94D049BB133111EBUL;
        x ^= x >> 31;
        return x;
    }
}
