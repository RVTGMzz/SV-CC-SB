# CARDCHA REPOSITORY RELOCATION CI RECHECK — 2026-09-19

Current canonical repository:

`RVTGMzz/SV-CC-SB`

Branch:

`cardcha-alpha28-0696d2-window-environment-matrix`

Current gameplay checkpoint:

`0696D3-J Collision Lanes`

Current TEST version:

`0.3.0-alpha.28.0.4.14.4.5.12.74`

## Relocation validation

The repository rename/owner move was rechecked through the current GitHub connection.

Repository ID remains:

`1344823595`

The active D3-J workflow can:
- checkout `RVTGMzz/SV-CC-SB`;
- materialize the D3-I clean console asset;
- run the D3-J collision validator;
- run no-legacy Window and render-depth guards;
- configure the SMAPI build environment;
- compile Release;
- assemble the D3-J package;
- pass the D3-J package audit.

## Rerun evidence

Workflow run:

`35364163371`

Original successful job:

`105662423365`

Relocation recheck / rerun job:

`105839686184`

On the rerun, all stages through package audit passed.

The rerun's temporary package SHA256 was:

`315b862c47ce1d4438ad010bdfb4930bf83b7f2eb2249e9149719904726d8284`

This rebuild was NOT published and is NOT canonical.

The final publish step failed only because the canonical release tag already existed:

`cardcha-0696d3j-test-d9665fdf`

GitHub reported:

`a release with the same tag name already exists`

This is not a source, validator, compile, or package-audit failure.

## Canonical D3-J package remains unchanged

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3j-test-d9665fdf`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.74_0696D3J_CollisionLanes_TEST.zip`

Canonical SHA256:

`66e41d4ae5d55228951ea2ea04acf9f8d1e4de5e52fac1a8bbcacc492e22ddf4`

Do not replace the canonical package with a rerun rebuild solely because its ZIP bytes differ.

## Workflow hardening

Workflow-only commit:

`65ac89115d0488527062fd67eecc3eb7abe45a01`

The D3-J prerelease step is now rerun-safe:
- if the exact tag already exists, publish is skipped successfully;
- existing canonical assets are preserved;
- rerun rebuilds cannot silently replace the canonical package.

The workflow file was also removed from its own push-path trigger so a workflow-only maintenance edit does not generate a redundant Cardcha TEST release.

## Status

**REPOSITORY RELOCATION: VERIFIED**  
**D3-J VALIDATOR / COMPILE / PACKAGE AUDIT: VERIFIED UNDER NEW OWNER**  
**CANONICAL PACKAGE: UNCHANGED**  
**RUNTIME: RETEST REQUIRED**

Only Ron's in-game test of the canonical D3-J package can promote Runtime PASS.
