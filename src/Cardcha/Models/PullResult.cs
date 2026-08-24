namespace Cardcha.Models;

internal sealed record PullResult(
    CardDefinition Card,
    bool IsNew,
    int DuplicateCopiesAwarded,
    int DustAwarded,
    PullType PullType,
    long PullIndex
);
