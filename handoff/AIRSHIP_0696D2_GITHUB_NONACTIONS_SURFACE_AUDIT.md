# AIRSHIP 0696D2 GitHub Non-Actions Surface Audit

Date: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Scope: exact D2.1 source recovery only. This audit intentionally does **not** revisit GitHub Actions, which is already exhaustively documented elsewhere.

## Purpose

Check GitHub surfaces outside Actions/history where binary/image evidence can sometimes survive independently of branch files:

- Issues
- Pull requests
- issue/PR image-attachment references
- Releases / release assets

## Issue search

Repository-scoped searches returned no relevant issue trail for:

- `airship`
- `0696`
- `Observation Window`

A repository-scoped issue search for `private-user-images.githubusercontent.com` also returned no result, so no issue/PR conversation indexed by GitHub exposes a private-user-image attachment reference through that search surface.

## Pull requests

The repository PR collection contains only earlier workstreams, including alpha26.x CI/recovery and older v02/book-visual work. No PR title/body/ref in the collection is tied to 0696D2, the Observation Window environment matrix, or the 2026-09-13 D2.1 approval/materialization window.

Therefore there is no 0696D2 PR discussion trail to inspect for an attachment source.

## Releases

The repository Releases collection returned an empty array:

`[]`

So there are no release assets, draft releases, or published release attachments available as an alternate D2.1 byte source through the connected GitHub surface.

## Commit-comments limitation

The connected GitHub read surface does not expose the repository commit-comments collection endpoint used for a date-range enumeration. No claim is made that GitHub globally has zero commit comments; only that no recoverable commit-comment attachment trail is exposed through the available connector path used here.

This limitation does not relax the exact-byte gate.

## Result

**0 authoritative D2.1 source candidates found on the accessible GitHub non-Actions collaboration/release surfaces.**

No source files were generated, copied, resized, re-encoded, or installed. `.69` remains intentionally unmaterialized.

## Recovery implication

Do not repeat Issues/PR/Releases searches unless new evidence provides a specific issue number, PR number, attachment URL, release/tag, or comment identifier.

The next valid recovery source remains an authoritative original/local copy whose four PNG byte streams independently match the recorded SHA256 values.
