using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace Cardcha.Services;

/// <summary>
/// Compatibility fallback for modded combat systems which don't route deaths through
/// vanilla Monster.takeDamage / GameLocation.monsterDrop.
///
/// It watches the current location every game tick:
///  - all Monster subclasses are tracked directly;
///  - non-Monster Character types from mods can be tracked when they expose HP-like members;
///  - an unknown custom actor must actually lose HP before a disappearance counts as a death;
///  - obvious companion/friendly/owned actors are filtered out.
///
/// This is intentionally runtime/reflection based: no Pelipper-specific IDs and no hard-coded
/// monster species list.
/// </summary>
internal sealed class UniversalEnemyObserverService
{
    private const long RecentDamageWindowTicks = 180; // ~3 seconds at 60fps
    private const long ForgetAfterTicks = 300;

    private readonly MonsterDeathService Deaths;
    private readonly Dictionary<Character, TrackState> Tracked =
        new(ReferenceCharacterComparer.Instance);
    private readonly Dictionary<Type, ActorAccessor?> AccessorCache = new();

    public long TicksObserved { get; private set; }
    public long MonsterActorsSeen { get; private set; }
    public long CustomHealthActorsSeen { get; private set; }
    public long CustomDeathsInferred { get; private set; }
    public long FriendlyActorsSkipped { get; private set; }
    public long UnknownHealthActorsTracked { get; private set; }
    public string LastCustomType { get; private set; } = "none";
    public string LastCustomName { get; private set; } = "none";

    public UniversalEnemyObserverService(MonsterDeathService deaths)
    {
        this.Deaths = deaths;
    }

    public void Reset()
    {
        this.Tracked.Clear();
        this.AccessorCache.Clear();

        this.TicksObserved = 0;
        this.MonsterActorsSeen = 0;
        this.CustomHealthActorsSeen = 0;
        this.CustomDeathsInferred = 0;
        this.FriendlyActorsSkipped = 0;
        this.UnknownHealthActorsTracked = 0;
        this.LastCustomType = "none";
        this.LastCustomName = "none";
    }

    public void Update(ulong tick)
    {
        if (!Context.IsWorldReady || Game1.currentLocation is null)
            return;

        this.TicksObserved++;

        GameLocation location = Game1.currentLocation;
        Farmer player = Game1.player;

        // GameLocation.characters is a collection of NPC in Stardew 1.6.
        // NPC derives from Character, so keep the concrete inferred type here
        // and consume each entry as Character below.
        var current = location.characters.ToList();
        HashSet<Character> seen = new(ReferenceCharacterComparer.Instance);

        foreach (Character actor in current)
        {
            if (actor is null)
                continue;

            seen.Add(actor);

            if (actor is Monster monster)
            {
                this.ObserveMonster(monster, player, location, tick);
                continue;
            }

            this.ObserveCustomCharacter(actor, player, location, tick);
        }

        // Disappearance fallback:
        // many custom battle systems remove an actor directly instead of calling monsterDrop.
        foreach ((Character actor, TrackState state) in this.Tracked.ToList())
        {
            if (seen.Contains(actor))
                continue;

            long age = (long)tick - (long)state.LastSeenTick;
            bool recentlyDamaged =
                state.WasDamaged
                && ((long)tick - (long)state.LastDamagedTick) <= RecentDamageWindowTicks;

            if (!state.DeathReported && (state.LastHealth <= 0 || recentlyDamaged))
            {
                if (actor is Monster vanishedMonster)
                {
                    // The normal death service's modData marker deduplicates this against
                    // takeDamage/monsterDrop if either one already fired.
                    this.Deaths.HandleDeath(vanishedMonster, player, state.Location);
                }
                else if (state.IsCustomHealthActor)
                {
                    state.DeathReported = true;
                    this.CustomDeathsInferred++;

                    this.Deaths.HandleCustomDeath(
                        state.Name,
                        Math.Max(1, state.MaxHealthSeen),
                        state.LastPosition,
                        state.Location,
                        player,
                        state.SourceType + " [observer-disappear]"
                    );
                }
            }

            if (age >= ForgetAfterTicks || state.DeathReported || recentlyDamaged)
                this.Tracked.Remove(actor);
        }
    }

    public string Describe()
        => $"ObserverTicks={this.TicksObserved} | MonsterSeen={this.MonsterActorsSeen} | " +
           $"CustomHealthSeen={this.CustomHealthActorsSeen} | CustomDeathsInferred={this.CustomDeathsInferred} | " +
           $"FriendlySkipped={this.FriendlyActorsSkipped} | UnknownCustomTracked={this.UnknownHealthActorsTracked} | " +
           $"LastCustom={this.LastCustomName} ({this.LastCustomType})";

    private void ObserveMonster(
        Monster monster,
        Farmer player,
        GameLocation location,
        ulong tick
    )
    {
        this.MonsterActorsSeen++;

        if (!this.Tracked.TryGetValue(monster, out TrackState? state))
        {
            state = new TrackState
            {
                Name = string.IsNullOrWhiteSpace(monster.Name) ? monster.GetType().Name : monster.Name,
                SourceType = monster.GetType().FullName ?? monster.GetType().Name,
                LastHealth = monster.Health,
                MaxHealthSeen = Math.Max(1, monster.MaxHealth),
                LastPosition = monster.Position,
                Location = location,
                LastSeenTick = tick,
                IsCustomHealthActor = false
            };
            this.Tracked[monster] = state;
        }

        if (monster.Health < state.LastHealth)
        {
            state.WasDamaged = true;
            state.LastDamagedTick = tick;
        }

        state.LastHealth = monster.Health;
        state.MaxHealthSeen = Math.Max(state.MaxHealthSeen, Math.Max(monster.MaxHealth, monster.Health));
        state.LastPosition = monster.Position;
        state.Location = location;
        state.LastSeenTick = tick;

        if (monster.Health <= 0 && !state.DeathReported)
        {
            state.DeathReported = true;
            this.Deaths.HandleDeath(monster, player, location);
        }
    }

    private void ObserveCustomCharacter(
        Character actor,
        Farmer player,
        GameLocation location,
        ulong tick
    )
    {
        Type type = actor.GetType();

        // Vanilla NPCs aren't combat targets; don't waste reflection on them.
        if (type.Assembly == typeof(Game1).Assembly)
            return;

        ActorAccessor? accessor = GetAccessor(type);
        if (accessor is null)
            return;

        int? health = accessor.ReadHealth(actor);
        if (!health.HasValue)
            return;

        int? maxHealth = accessor.ReadMaxHealth(actor);
        int hp = health.Value;
        int maxHp = Math.Max(1, maxHealth ?? hp);

        bool friendly = LooksFriendly(actor, accessor);
        if (friendly)
        {
            this.FriendlyActorsSkipped++;
            this.Tracked.Remove(actor);
            return;
        }

        this.CustomHealthActorsSeen++;
        this.LastCustomType = type.FullName ?? type.Name;
        this.LastCustomName = string.IsNullOrWhiteSpace(actor.Name) ? type.Name : actor.Name;

        if (!this.Tracked.TryGetValue(actor, out TrackState? state))
        {
            state = new TrackState
            {
                Name = this.LastCustomName,
                SourceType = this.LastCustomType,
                LastHealth = hp,
                MaxHealthSeen = maxHp,
                LastPosition = actor.Position,
                Location = location,
                LastSeenTick = tick,
                IsCustomHealthActor = true
            };

            this.Tracked[actor] = state;
            this.UnknownHealthActorsTracked++;
            return;
        }

        if (hp < state.LastHealth)
        {
            state.WasDamaged = true;
            state.LastDamagedTick = tick;
        }

        state.LastHealth = hp;
        state.MaxHealthSeen = Math.Max(state.MaxHealthSeen, Math.Max(maxHp, hp));
        state.LastPosition = actor.Position;
        state.Location = location;
        state.LastSeenTick = tick;

        // Custom actors don't get loot just because they happen to expose Health=0 at spawn.
        // We require an observed HP loss in this session/location.
        if (hp <= 0 && state.WasDamaged && !state.DeathReported)
        {
            state.DeathReported = true;
            this.CustomDeathsInferred++;

            this.Deaths.HandleCustomDeath(
                state.Name,
                state.MaxHealthSeen,
                state.LastPosition,
                location,
                player,
                state.SourceType + " [observer-hp0]"
            );
        }
    }

    private ActorAccessor? GetAccessor(Type type)
    {
        if (this.AccessorCache.TryGetValue(type, out ActorAccessor? cached))
            return cached;

        MemberInfo? health = FindNumericMember(
            type,
            "Health", "health",
            "CurrentHealth", "currentHealth",
            "CurrentHP", "currentHP",
            "HP", "Hp", "hp"
        );

        if (health is null)
        {
            this.AccessorCache[type] = null;
            return null;
        }

        MemberInfo? max = FindNumericMember(
            type,
            "MaxHealth", "maxHealth",
            "MaximumHealth", "maximumHealth",
            "MaxHP", "maxHP", "maxHp",
            "MaximumHP", "maximumHP"
        );

        ActorAccessor accessor = new(health, max);
        this.AccessorCache[type] = accessor;
        return accessor;
    }

    private static bool LooksFriendly(Character actor, ActorAccessor accessor)
    {
        Type type = actor.GetType();

        string[] friendlyFlags =
        {
            "IsCompanion", "isCompanion", "Companion",
            "IsFriendly", "isFriendly", "Friendly",
            "IsPartner", "isPartner", "Partner",
            "IsOwned", "isOwned", "Owned",
            "IsTamed", "isTamed", "Tamed",
            "PlayerOwned", "IsPlayerOwned", "isPlayerOwned"
        };

        foreach (string name in friendlyFlags)
        {
            bool? value = ReadBooleanMember(type, actor, name);
            if (value == true)
                return true;
        }

        // Mod-data is often the easiest generic signal available across independent mods.
        foreach ((string key, string value) in actor.modData.Pairs)
        {
            string combined = (key + "=" + value).ToLowerInvariant();
            if (combined.Contains("companion")
                || combined.Contains("friendly")
                || combined.Contains("partner")
                || combined.Contains("owned")
                || combined.Contains("tamed"))
            {
                if (!combined.Contains("false") && !combined.Contains("hostile"))
                    return true;
            }
        }

        return false;
    }

    private static MemberInfo? FindNumericMember(Type type, params string[] names)
    {
        for (Type? cursor = type; cursor is not null; cursor = cursor.BaseType)
        {
            BindingFlags flags =
                BindingFlags.Instance
                | BindingFlags.Public
                | BindingFlags.NonPublic
                | BindingFlags.DeclaredOnly;

            foreach (string name in names)
            {
                PropertyInfo? prop = cursor.GetProperties(flags)
                    .FirstOrDefault(p =>
                        p.GetIndexParameters().Length == 0
                        && p.Name.Equals(name, StringComparison.OrdinalIgnoreCase)
                    );

                if (prop is not null)
                    return prop;

                FieldInfo? field = cursor.GetFields(flags)
                    .FirstOrDefault(f => f.Name.Equals(name, StringComparison.OrdinalIgnoreCase));

                if (field is not null)
                    return field;
            }
        }

        return null;
    }

    private static bool? ReadBooleanMember(Type type, object instance, string name)
    {
        for (Type? cursor = type; cursor is not null; cursor = cursor.BaseType)
        {
            BindingFlags flags =
                BindingFlags.Instance
                | BindingFlags.Public
                | BindingFlags.NonPublic
                | BindingFlags.DeclaredOnly;

            PropertyInfo? prop = cursor.GetProperties(flags)
                .FirstOrDefault(p =>
                    p.GetIndexParameters().Length == 0
                    && p.Name.Equals(name, StringComparison.OrdinalIgnoreCase)
                );

            if (prop is not null)
            {
                try
                {
                    object? value = prop.GetValue(instance);
                    if (value is bool b)
                        return b;

                    PropertyInfo? wrappedValue = value?.GetType().GetProperty("Value");
                    if (wrappedValue?.GetValue(value) is bool wb)
                        return wb;
                }
                catch { }
            }

            FieldInfo? field = cursor.GetFields(flags)
                .FirstOrDefault(f => f.Name.Equals(name, StringComparison.OrdinalIgnoreCase));

            if (field is not null)
            {
                try
                {
                    object? value = field.GetValue(instance);
                    if (value is bool b)
                        return b;

                    PropertyInfo? wrappedValue = value?.GetType().GetProperty("Value");
                    if (wrappedValue?.GetValue(value) is bool wb)
                        return wb;
                }
                catch { }
            }
        }

        return null;
    }

    private sealed class ActorAccessor
    {
        private readonly MemberInfo HealthMember;
        private readonly MemberInfo? MaxHealthMember;

        public ActorAccessor(MemberInfo healthMember, MemberInfo? maxHealthMember)
        {
            this.HealthMember = healthMember;
            this.MaxHealthMember = maxHealthMember;
        }

        public int? ReadHealth(object actor)
            => ReadNumeric(this.HealthMember, actor);

        public int? ReadMaxHealth(object actor)
            => this.MaxHealthMember is null ? null : ReadNumeric(this.MaxHealthMember, actor);

        private static int? ReadNumeric(MemberInfo member, object actor)
        {
            try
            {
                object? value = member switch
                {
                    PropertyInfo p => p.GetValue(actor),
                    FieldInfo f => f.GetValue(actor),
                    _ => null
                };

                return ConvertNumeric(value);
            }
            catch
            {
                return null;
            }
        }

        private static int? ConvertNumeric(object? value)
        {
            if (value is null)
                return null;

            if (value is int i) return i;
            if (value is uint ui) return ui > int.MaxValue ? int.MaxValue : (int)ui;
            if (value is short s) return s;
            if (value is ushort us) return us;
            if (value is long l) return (int)Math.Clamp(l, int.MinValue, int.MaxValue);
            if (value is float f) return (int)Math.Round(f);
            if (value is double d) return (int)Math.Round(d);
            if (value is decimal m) return (int)Math.Round(m);

            PropertyInfo? wrapped = value.GetType().GetProperty(
                "Value",
                BindingFlags.Instance | BindingFlags.Public
            );

            if (wrapped is not null)
                return ConvertNumeric(wrapped.GetValue(value));

            return null;
        }
    }

    private sealed class TrackState
    {
        public string Name { get; set; } = "enemy";
        public string SourceType { get; set; } = "unknown";
        public int LastHealth { get; set; }
        public int MaxHealthSeen { get; set; }
        public Vector2 LastPosition { get; set; }
        public GameLocation Location { get; set; } = null!;
        public ulong LastSeenTick { get; set; }
        public ulong LastDamagedTick { get; set; }
        public bool WasDamaged { get; set; }
        public bool DeathReported { get; set; }
        public bool IsCustomHealthActor { get; set; }
    }

    private sealed class ReferenceCharacterComparer : IEqualityComparer<Character>
    {
        public static readonly ReferenceCharacterComparer Instance = new();

        public bool Equals(Character? x, Character? y)
            => ReferenceEquals(x, y);

        public int GetHashCode(Character obj)
            => RuntimeHelpers.GetHashCode(obj);
    }
}
