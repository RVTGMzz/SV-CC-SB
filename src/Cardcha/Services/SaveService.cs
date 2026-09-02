using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;
using System.Security.Cryptography;
using System.Text;

namespace Cardcha.Services;

internal sealed class SaveService
{
    private const string SaveKey = "cardcha-save-v1";
    private const int CurrentSchemaVersion = 18;
    private readonly IModHelper Helper;
    private int TransientTestDepth;

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

        if (loadedSchema < 4 && this.Data.MachineDelivered)
            this.Data.BinderUnlocked = true;

        if (loadedSchema < 5)
        {
            this.Data.AirshipEngineLevel = Math.Clamp(this.Data.AirshipEngineLevel, 0, 3);
        this.Data.AirshipNavigationLevel = Math.Clamp(this.Data.AirshipNavigationLevel, 0, 3);
        this.Data.AirshipHullLevel = Math.Clamp(this.Data.AirshipHullLevel, 0, 3);
        this.Data.AirshipReactorLevel = Math.Clamp(this.Data.AirshipReactorLevel, 0, 3);

        this.Data.ActiveCardSlotCount = Math.Clamp(this.Data.ActiveCardSlotCount <= 0 ? 2 : this.Data.ActiveCardSlotCount, 2, 5);

            foreach (string cardId in this.Data.OwnedCards)
            {
                if (!this.Data.CardLevels.ContainsKey(cardId) || this.Data.CardLevels[cardId] < 1)
                    this.Data.CardLevels[cardId] = 1;
            }
        }

        if (loadedSchema < 6)
            this.Data.CardCopies ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);

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

        if (loadedSchema < 9)
        {
            this.Data.CardboardScraps = Math.Max(0, this.Data.CardboardScraps);
            this.Data.ShinyScraps = Math.Max(0, this.Data.ShinyScraps);
        this.Data.SuspiciousDust = Math.Max(0, this.Data.SuspiciousDust);
        this.Data.DuplicatePullStreak = Math.Max(0, this.Data.DuplicatePullStreak);

        this.Data.AirshipHighestRegionUnlocked = Math.Clamp(this.Data.AirshipHighestRegionUnlocked, 0, 4);
        this.Data.AirshipUnlockedDay = Math.Max(-1, this.Data.AirshipUnlockedDay);
        this.Data.AirshipFlightsTaken = Math.Max(0, this.Data.AirshipFlightsTaken);
        this.Data.AirshipTotalFarePaid = Math.Max(0, this.Data.AirshipTotalFarePaid);

        this.Data.AirshipHighestRegionUnlocked = Math.Clamp(this.Data.AirshipHighestRegionUnlocked, 0, 4);
        this.Data.AirshipUnlockedDay = Math.Max(-1, this.Data.AirshipUnlockedDay);

            if (this.Data.MimiMeetupCompleted && this.Data.MimiMerchantUnlockedDay < 0)
                this.Data.MimiMerchantUnlockedDay = Math.Max(-1, Game1.Date.TotalDays - 1);
        }

        if (loadedSchema < 10)
        {
            if (this.Data.MimiMeetupPending && !this.Data.MimiMeetupCompleted)
                this.Data.MimiMeetupOfferedDay = Game1.Date.TotalDays;
            else if (this.Data.MimiMeetupCompleted)
                this.Data.MimiMeetupOfferedDay = -1;
        }

        if (loadedSchema < 11)
        {
            this.Data.PortableMachinePurchased = false;
            this.Data.PortableMachineGifted = false;
        }

        // v12: Binder v0.3 favorites. Existing saves begin with an empty personal shortcut list.
        if (loadedSchema < 12)
            this.Data.FavoriteCardIds = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        // v13: early prototype builds seeded ten demo cards into untouched collections.
        // Only repair the unmistakable pre-Binder, zero-pull state so earned cards are never removed.
        if (loadedSchema < 13
            && this.Data.PullIndex == 0
            && !this.Data.MachineDelivered
            && !this.Data.BinderUnlocked
            && !this.Data.MimiMeetupCompleted
            && this.Data.OwnedCards.Count > 0)
        {
            this.Data.OwnedCards.Clear();
            this.Data.EquippedCards.Clear();
            this.Data.CardLevels.Clear();
            this.Data.CardCopies.Clear();
            this.Data.FavoriteCardIds.Clear();
        }

        // v15: Airship foundation. Existing saves that already completed the MiMi/Wizard
        // handoff receive Region I access immediately instead of replaying onboarding.
        if (loadedSchema < 15)
        {
            if (this.Data.MimiMeetupCompleted || this.Data.MachineDelivered || this.Data.BinderUnlocked)
            {
                this.Data.AirshipUnlocked = true;
                this.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Data.AirshipHighestRegionUnlocked);
                if (this.Data.AirshipUnlockedDay < 0)
                    this.Data.AirshipUnlockedDay = Game1.Date.TotalDays;
            }
        }

        // v16: Sky Dock interior + MiMi fare telemetry.
        if (loadedSchema < 16)
        {
            this.Data.AirshipFlightsTaken = Math.Max(0, this.Data.AirshipFlightsTaken);
            this.Data.AirshipTotalFarePaid = Math.Max(0, this.Data.AirshipTotalFarePaid);
        }

        // v17: Airship infrastructure foundation. Existing saves begin with all four
        // subsystems dormant at level 0 and retain their Magic Dust untouched.
        if (loadedSchema < 17)
        {
            this.Data.AirshipEngineLevel = Math.Clamp(this.Data.AirshipEngineLevel, 0, 3);
            this.Data.AirshipNavigationLevel = Math.Clamp(this.Data.AirshipNavigationLevel, 0, 3);
            this.Data.AirshipHullLevel = Math.Clamp(this.Data.AirshipHullLevel, 0, 3);
            this.Data.AirshipReactorLevel = Math.Clamp(this.Data.AirshipReactorLevel, 0, 3);
        }

        // v18: full active-card runtime audit.
        if (loadedSchema < 18)
        {
            this.Data.StandardPullIndex = Math.Max(0, this.Data.StandardPullIndex);
            this.Data.BattleScholarMonsterTypesToday = new HashSet<string>(
                this.Data.BattleScholarMonsterTypesToday ?? new HashSet<string>(),
                StringComparer.OrdinalIgnoreCase
            );
        }

        if (loadedSchema < CurrentSchemaVersion)
        {
            this.Data.SchemaVersion = CurrentSchemaVersion;
            this.Data.LastStateFingerprint = ComputeFingerprint(this.Data);
            this.LastPersistenceCheckPassed = true;
            this.LastPersistenceMessage =
                $"Migrated Cardcha save schema {loadedSchema} -> {CurrentSchemaVersion}; fingerprint initialized ({Short(this.Data.LastStateFingerprint)}).";
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
            this.LastPersistenceMessage = $"Persistence fingerprint initialized ({Short(actual)}).";
            this.Save();
            return;
        }

        this.LastPersistenceCheckPassed = expected.Equals(actual, StringComparison.OrdinalIgnoreCase);
        this.LastPersistenceMessage = this.LastPersistenceCheckPassed
            ? $"PASS — save state matches fingerprint {Short(actual)}."
            : $"WARNING — loaded state fingerprint changed. Saved={Short(expected)} Loaded={Short(actual)}. Data was kept; no automatic rollback was performed.";
    }

    internal IDisposable BeginTransientTestScope()
    {
        SaveData snapshot = CloneData(this.Data);
        this.TransientTestDepth++;
        return new TransientScope(() =>
        {
            this.Data = snapshot;
            this.TransientTestDepth = Math.Max(0, this.TransientTestDepth - 1);
        });
    }

    private static SaveData CloneData(SaveData d)
        => new()
        {
            SchemaVersion = d.SchemaVersion,
            OwnedCards = new HashSet<string>(d.OwnedCards ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),
            EquippedCards = new List<string>(d.EquippedCards ?? new List<string>()),
            CardLevels = new Dictionary<string, int>(d.CardLevels ?? new Dictionary<string, int>(), StringComparer.OrdinalIgnoreCase),
            CardCopies = new Dictionary<string, int>(d.CardCopies ?? new Dictionary<string, int>(), StringComparer.OrdinalIgnoreCase),
            FavoriteCardIds = new HashSet<string>(d.FavoriteCardIds ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),
            ActiveCardSlotCount = d.ActiveCardSlotCount,
            SuspiciousDust = d.SuspiciousDust,
            PullIndex = d.PullIndex,
            GachaSeed = d.GachaSeed,
            StandardSinceRare = d.StandardSinceRare,
            StandardSinceEpic = d.StandardSinceEpic,
            StandardSinceLegendary = d.StandardSinceLegendary,
            PremiumSinceEpic = d.PremiumSinceEpic,
            PremiumSinceLegendary = d.PremiumSinceLegendary,
            DuplicatePullStreak = d.DuplicatePullStreak,
            StandardPullIndex = d.StandardPullIndex,
            BattleScholarMonsterTypesToday = new HashSet<string>(d.BattleScholarMonsterTypesToday ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),
            PhoenixHeartUsedToday = d.PhoenixHeartUsedToday,
            LifelineUsedToday = d.LifelineUsedToday,
            GuardianAngelUsedToday = d.GuardianAngelUsedToday,
            CardboardScraps = d.CardboardScraps,
            ShinyScraps = d.ShinyScraps,
            FirstScrapTriggered = d.FirstScrapTriggered,
            FirstScrapDay = d.FirstScrapDay,
            MachineLetterQueued = d.MachineLetterQueued,
            MachineDelivered = d.MachineDelivered,
            BinderUnlocked = d.BinderUnlocked,
            MimiIntroSeen = d.MimiIntroSeen,
            MimiMeetupPending = d.MimiMeetupPending,
            MimiMeetupCompleted = d.MimiMeetupCompleted,
            ChaChaLoaned = d.ChaChaLoaned,
            FirstPullQuestActive = d.FirstPullQuestActive,
            FirstPullCompleted = d.FirstPullCompleted,
            Chapter1Completed = d.Chapter1Completed,
            CardchaStoryChapter = d.CardchaStoryChapter,
            CardchaStoryStage = d.CardchaStoryStage,
            MimiMerchantUnlockedDay = d.MimiMerchantUnlockedDay,
            MimiFirstMerchantPepTalkShown = d.MimiFirstMerchantPepTalkShown,
            FirstScrapPickupNoticeShown = d.FirstScrapPickupNoticeShown,
            MimiMeetupOfferedDay = d.MimiMeetupOfferedDay,
            PortableMachinePurchased = d.PortableMachinePurchased,
            PortableMachineGifted = d.PortableMachineGifted,
            AirshipFlybySeen = d.AirshipFlybySeen,
            AirshipUnlocked = d.AirshipUnlocked,
            AirshipUnlockedDay = d.AirshipUnlockedDay,
            AirshipHighestRegionUnlocked = d.AirshipHighestRegionUnlocked,
            AirshipFlightsTaken = d.AirshipFlightsTaken,
            AirshipTotalFarePaid = d.AirshipTotalFarePaid,
            AirshipEngineLevel = d.AirshipEngineLevel,
            AirshipNavigationLevel = d.AirshipNavigationLevel,
            AirshipHullLevel = d.AirshipHullLevel,
            AirshipReactorLevel = d.AirshipReactorLevel,
            LastStateFingerprint = d.LastStateFingerprint ?? ""
        };

    private sealed class TransientScope : IDisposable
    {
        private Action? OnDispose;
        public TransientScope(Action onDispose) => this.OnDispose = onDispose;
        public void Dispose()
        {
            Action? action = this.OnDispose;
            this.OnDispose = null;
            action?.Invoke();
        }
    }

    public void Save()
    {
        if (this.TransientTestDepth > 0)
            return;

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
    {
        this.Data.PhoenixHeartUsedToday = false;
        this.Data.LifelineUsedToday = false;
        this.Data.GuardianAngelUsedToday = false;
        this.Data.BattleScholarMonsterTypesToday.Clear();
    }

    public string DescribePersistence()
        => $"{this.LastPersistenceMessage} Current={Short(this.CurrentFingerprint)}";

    private void Normalize()
    {
        this.Data.EquippedCards ??= new List<string>();
        this.Data.OwnedCards ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        this.Data.CardLevels ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        this.Data.CardCopies ??= new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        this.Data.FavoriteCardIds ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        this.Data.LastStateFingerprint ??= "";
        this.Data.CardboardScraps = Math.Max(0, this.Data.CardboardScraps);
        this.Data.ShinyScraps = Math.Max(0, this.Data.ShinyScraps);
        this.Data.SuspiciousDust = Math.Max(0, this.Data.SuspiciousDust);
        this.Data.DuplicatePullStreak = Math.Max(0, this.Data.DuplicatePullStreak);

        this.Data.ActiveCardSlotCount = Math.Clamp(this.Data.ActiveCardSlotCount <= 0 ? 2 : this.Data.ActiveCardSlotCount, 2, 5);

        this.Data.EquippedCards = this.Data.EquippedCards
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Take(5)
            .ToList();

        this.Data.FavoriteCardIds = new HashSet<string>(
            this.Data.FavoriteCardIds.Where(p => !string.IsNullOrWhiteSpace(p)),
            StringComparer.OrdinalIgnoreCase
        );

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
        string owned = string.Join(",", (data.OwnedCards ?? new HashSet<string>())
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));

        string equipped = string.Join(",", (data.EquippedCards ?? new List<string>())
            .Where(p => !string.IsNullOrWhiteSpace(p)));

        string favorites = string.Join(",", (data.FavoriteCardIds ?? new HashSet<string>())
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));

        string levels = string.Join(",", (data.CardLevels ?? new Dictionary<string, int>())
            .OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase)
            .Select(p => $"{p.Key}:{p.Value}"));

        string copies = string.Join(",", (data.CardCopies ?? new Dictionary<string, int>())
            .OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase)
            .Select(p => $"{p.Key}:{p.Value}"));

        string battleScholarTypes = string.Join(",", (data.BattleScholarMonsterTypesToday ?? new HashSet<string>())
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));

        string canonical = string.Join(
            "|",
            CurrentSchemaVersion,
            owned,
            equipped,
            favorites,
            levels,
            copies,
            data.ActiveCardSlotCount,
            data.SuspiciousDust,
            data.PullIndex,
            data.StandardPullIndex,
            data.GachaSeed,
            data.StandardSinceRare,
            data.StandardSinceEpic,
            data.StandardSinceLegendary,
            data.PremiumSinceEpic,
            data.PremiumSinceLegendary,
            data.DuplicatePullStreak,
            battleScholarTypes,
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
            data.PortableMachineGifted ? 1 : 0,
            data.AirshipFlybySeen ? 1 : 0,
            data.AirshipUnlocked ? 1 : 0,
            data.AirshipUnlockedDay,
            data.AirshipHighestRegionUnlocked,
            data.AirshipFlightsTaken,
            data.AirshipTotalFarePaid,
            data.AirshipEngineLevel,
            data.AirshipNavigationLevel,
            data.AirshipHullLevel,
            data.AirshipReactorLevel
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
