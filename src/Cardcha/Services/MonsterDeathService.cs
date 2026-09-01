using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// One deduplicated Cardcha death pipeline.
/// We intentionally listen at two vanilla boundaries:
/// - Monster.takeDamage: primary path for actual player-caused kills.
/// - GameLocation.monsterDrop: fallback for unusual/modded death flows.
/// The monster's modData prevents double rewards when both hooks fire.
/// </summary>
internal sealed class MonsterDeathService
{
    private const string DeathHandledKey = "Ronvotri.Cardcha/DeathHandled";

    private readonly DropService Drops;
    private readonly CombatService Combat;

    public long DeathsHandled { get; private set; }
    public string LastMonsterName { get; private set; } = "none";
    public int LastMonsterMaxHealth { get; private set; }
    public long CustomDeathsHandled { get; private set; }
    public string LastDeathSource { get; private set; } = "none";

    public MonsterDeathService(DropService drops, CombatService combat)
    {
        this.Drops = drops;
        this.Combat = combat;
    }

    public void HandleDeath(Monster monster, Farmer? who, GameLocation? location = null)
    {
        if (monster is null)
            return;

        if (monster.modData.ContainsKey(DeathHandledKey))
            return;

        monster.modData[DeathHandledKey] = "1";

        GameLocation? resolvedLocation =
            location
            ?? monster.currentLocation
            ?? who?.currentLocation
            ?? Game1.currentLocation;

        if (resolvedLocation is null)
            return;

        this.DeathsHandled++;
        this.LastMonsterName = string.IsNullOrWhiteSpace(monster.Name) ? monster.GetType().Name : monster.Name;
        this.LastMonsterMaxHealth = Math.Max(1, monster.MaxHealth);
        this.LastDeathSource = monster.GetType().FullName ?? monster.GetType().Name;

        this.Combat.OnMonsterKilled(monster, who);
        this.Drops.TryDrop(resolvedLocation, monster, who);
    }

    public void HandleCustomDeath(
        string enemyName,
        int maxHealth,
        Microsoft.Xna.Framework.Vector2 position,
        GameLocation location,
        Farmer? who,
        string sourceType
    )
    {
        this.DeathsHandled++;
        this.CustomDeathsHandled++;
        this.LastMonsterName = string.IsNullOrWhiteSpace(enemyName) ? "custom enemy" : enemyName;
        this.LastMonsterMaxHealth = Math.Max(1, maxHealth);
        this.LastDeathSource = sourceType;

        EnemyLootScale scale = DropService.ClassifyEnemy(this.LastMonsterName, sourceType);
        string coreType = sourceType.Split(" [observer", StringSplitOptions.None)[0];
        this.Combat.OnCustomEnemyKilled(who, coreType, scale == EnemyLootScale.BossLike);

        this.Drops.TryDrop(
            location,
            position,
            this.LastMonsterName,
            this.LastMonsterMaxHealth,
            who,
            scale
        );
    }

    public string Describe()
        => $"DeathsHandled={this.DeathsHandled} | CustomDeaths={this.CustomDeathsHandled} | " +
           $"Last={this.LastMonsterName} | LastMaxHP={this.LastMonsterMaxHealth} | LastSource={this.LastDeathSource}";
}
