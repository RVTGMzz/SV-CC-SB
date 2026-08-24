param(
    [Parameter(Mandatory=$true)][string]$ZipPath,
    [Parameter(Mandatory=$true)][string]$GamePath
)

$ErrorActionPreference = "Stop"
$BuilderRoot = $PSScriptRoot
$ModsPath = Join-Path $GamePath "Mods"

if (-not (Test-Path -LiteralPath $ModsPath)) {
    throw "Mods folder not found: $ModsPath"
}

function Test-FileUnlocked {
    param([Parameter(Mandatory=$true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $true
    }

    $stream = $null
    try {
        $stream = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
    }
}

function Get-CardchaTargets {
    param([string]$ModsRoot)

    $found = @()

    Get-ChildItem -LiteralPath $ModsRoot -Filter "manifest.json" -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $manifest = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
            if ($manifest.UniqueID -eq "Ronvotri.Cardcha") {
                $found += $_.Directory.FullName
            }
        }
        catch {
            # Ignore unrelated malformed manifests.
        }
    }

    return @($found | Sort-Object -Unique)
}

$targets = Get-CardchaTargets -ModsRoot $ModsPath

# PRE-FLIGHT: never start backup/remove if Cardcha.dll is still loaded by SMAPI.
# Windows locks loaded DLLs, so Remove-Item cannot replace the mod while the game is running.
$lockedFiles = @()
foreach ($target in $targets) {
    $dll = Join-Path $target "Cardcha.dll"
    if ((Test-Path -LiteralPath $dll) -and -not (Test-FileUnlocked -Path $dll)) {
        $lockedFiles += $dll
    }
}

# Process hint for clearer logs. The file-lock test above is the real authority.
$runningGameProcesses = @(
    Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -like "Stardew*" -or
        $_.ProcessName -like "StardewModdingAPI*"
    }
)

if ($lockedFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host " CARDCHA INSTALL BLOCKED: GAME/SMAPI IS USING Cardcha.dll"
    Write-Host "============================================================"
    Write-Host ""
    Write-Host "Cardcha build SUCCEEDED, but Windows will not replace a loaded DLL."
    Write-Host "Close Stardew Valley / SMAPI completely, then retry install. No rebuild is required."
    Write-Host "You can also run INSTALL_CARDCHA_ONLY.bat later."
    Write-Host ""
    Write-Host "Locked file(s):"
    foreach ($file in $lockedFiles) {
        Write-Host " - $file"
    }

    if ($runningGameProcesses.Count -gt 0) {
        Write-Host ""
        Write-Host "Detected Stardew-related process(es):"
        foreach ($process in $runningGameProcesses) {
            Write-Host " - $($process.ProcessName) (PID $($process.Id))"
        }
    }

    Write-Host ""
    Write-Host "No old Cardcha folder was removed by this installer run."
    exit 51
}

$BackupRoot = Join-Path $BuilderRoot "_BACKUP_OLD_CARDCHA"
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$preservedConfig = $null

foreach ($target in $targets) {
    $safeName = (Split-Path $target -Leaf) -replace '[^A-Za-z0-9._-]', '_'
    $backup = Join-Path $BackupRoot ($stamp + "_" + $safeName)

    Write-Host "[BACKUP] $target"
    Copy-Item -LiteralPath $target -Destination $backup -Recurse -Force

    $cfg = Join-Path $target "config.json"
    if ((Test-Path -LiteralPath $cfg) -and -not $preservedConfig) {
        $preservedConfig = Join-Path $env:TEMP ("Cardcha_config_" + [guid]::NewGuid().ToString("N") + ".json")
        Copy-Item -LiteralPath $cfg -Destination $preservedConfig -Force
    }

    Write-Host "[REMOVE] $target"
    try {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    catch {
        throw "Could not remove old Cardcha folder '$target'. Close Stardew Valley/SMAPI and any program using Cardcha files, then retry. Original error: $($_.Exception.Message)"
    }
}

$temp = Join-Path $env:TEMP ("Cardcha_install_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $temp | Out-Null

try {
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $temp -Force

    $manifestFile = Get-ChildItem -LiteralPath $temp -Filter "manifest.json" -File -Recurse | Where-Object {
        try {
            $m = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
            $m.UniqueID -eq "Ronvotri.Cardcha"
        }
        catch {
            $false
        }
    } | Select-Object -First 1

    if (-not $manifestFile) {
        throw "Built ZIP does not contain manifest.json for Ronvotri.Cardcha."
    }

    $sourceRoot = $manifestFile.Directory.FullName
    $dest = Join-Path $ModsPath "Cardcha"

    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item -Path (Join-Path $sourceRoot "*") -Destination $dest -Recurse -Force

    if ($preservedConfig -and (Test-Path -LiteralPath $preservedConfig)) {
        Copy-Item -LiteralPath $preservedConfig -Destination (Join-Path $dest "config.json") -Force
    }

    $installedManifest = Get-Content -LiteralPath (Join-Path $dest "manifest.json") -Raw | ConvertFrom-Json

    Write-Host ""
    Write-Host "============================================================"
    Write-Host " CARDCHA INSTALLED FRESH"
    Write-Host " Version: $($installedManifest.Version)"
    Write-Host " Folder : $dest"
    Write-Host "============================================================"
}
finally {
    if (Test-Path -LiteralPath $temp) {
        Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($preservedConfig -and (Test-Path -LiteralPath $preservedConfig)) {
        Remove-Item -LiteralPath $preservedConfig -Force -ErrorAction SilentlyContinue
    }
}
