param(
    [switch]$SkipBuildEnvironmentCheck
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Version = "0.3.0-alpha.28.0.4.14.4.5.12.72"
$Project = Join-Path $Root "src\Cardcha\Cardcha.csproj"
$DistRoot = Join-Path $Root "dist\0696D3H"
$PackageRoot = Join-Path $DistRoot "Cardcha"
$ZipName = "Cardcha_v$($Version)_0696D3H_DensityRunnerInteractionPolish_TEST.zip"
$ZipPath = Join-Path $DistRoot $ZipName
$AuditPath = Join-Path $Root "handoff\AIRSHIP_0696D3H_LOCAL_PACKAGE_AUDIT.json"

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

Write-Host "[D3-H] Root: $Root"
Require-Command "python"
Require-Command "dotnet"

if (-not $SkipBuildEnvironmentCheck) {
    Write-Host "[D3-H] Checking Pillow..."
    python -c "import PIL; print(PIL.__version__)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[D3-H] Pillow missing; installing deterministic validator version..."
        python -m pip install --disable-pip-version-check Pillow==11.3.0
    }
}

Write-Host "[D3-H] 1/6 Static D3-H validator"
python (Join-Path $Root "tools\alpha28_0696d3h_density_runner_interaction_polish.py")
if ($LASTEXITCODE -ne 0) { throw "D3-H validator failed." }

Write-Host "[D3-H] 2/6 Historical guards"
python (Join-Path $Root "tools\validate_0696d2_no_legacy_overlay_reuse.py")
if ($LASTEXITCODE -ne 0) { throw "No-legacy Window guard failed." }
python (Join-Path $Root "tools\validate_render_depth_contract.py")
if ($LASTEXITCODE -ne 0) { throw "Render-depth guard failed." }

Write-Host "[D3-H] 3/6 Release compile"
dotnet build $Project -c Release --nologo
if ($LASTEXITCODE -ne 0) {
    throw "Release compile failed. If ModBuildConfig cannot locate Stardew Valley/SMAPI references, install/configure the Stardew ModBuildConfig environment first."
}

Write-Host "[D3-H] 4/6 Assemble package"
if (Test-Path $DistRoot) { Remove-Item $DistRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null

Copy-Item (Join-Path $Root "src\Cardcha\manifest.json") $PackageRoot
$Config = Join-Path $Root "src\Cardcha\config.json"
if (Test-Path $Config) { Copy-Item $Config $PackageRoot }
Copy-Item (Join-Path $Root "src\Cardcha\assets") $PackageRoot -Recurse
Copy-Item (Join-Path $Root "src\Cardcha\i18n") $PackageRoot -Recurse

$Dll = Get-ChildItem (Join-Path $Root "src\Cardcha\bin\Release") -Filter "Cardcha.dll" -Recurse |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
if (-not $Dll) { throw "Cardcha.dll not found under bin\Release." }
Copy-Item $Dll.FullName (Join-Path $PackageRoot "Cardcha.dll")

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $PackageRoot -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host "[D3-H] 5/6 Package audit"
python (Join-Path $Root "tools\alpha28_0696d3h_package_audit.py") $ZipPath --report $AuditPath
if ($LASTEXITCODE -ne 0) { throw "D3-H package audit failed." }

Write-Host "[D3-H] 6/6 SHA256"
$Hash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $ZipName" | Set-Content -Encoding ascii (Join-Path $DistRoot "$ZipName.sha256")

Write-Host ""
Write-Host "D3-H LOCAL BUILD/PACKAGE PASS" -ForegroundColor Green
Write-Host "ZIP:    $ZipPath"
Write-Host "SHA256: $Hash"
Write-Host "Audit:  $AuditPath"
Write-Host ""
Write-Host "This is still NOT Runtime PASS. Ron must test this exact ZIP in Stardew Valley."
