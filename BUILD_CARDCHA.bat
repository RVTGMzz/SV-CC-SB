@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion

title Cardcha! v0.1.17-alpha.11.32 Auto Build + Install
cd /d "%~dp0"

set "ROOT=%~dp0"
set "EXPECTED_BUILD=Cardcha! v0.1.17-alpha.11.32 NATIVE WORLD ACTORS + FAIRY FOLLOW"
set "PROJECT=%ROOT%src\Cardcha\Cardcha.csproj"
set "RELEASES=%ROOT%_releases"
set "READY=%ROOT%_READY_TO_INSTALL"
set "LOG=%ROOT%build-log.txt"
set "GAME_PATH=E:\SteamLibrary\steamapps\common\Stardew Valley"
set "INSTALLER=%ROOT%INSTALL_BUILT_CARDCHA.ps1"

cls
echo ============================================================
echo   CARDCHA! v0.1.17-alpha.11.32 - AUTO BUILD + SAFE INSTALL
echo ============================================================
echo.
echo Game:
echo %GAME_PATH%
echo.
echo QUAN TRONG:
echo - Tat Stardew Valley va SMAPI truoc khi chay file nay.
echo - Builder se backup va xoa moi Cardcha cu trong Mods.
echo - Sau do cai dung DLL vua build vao Mods\Cardcha.
echo.

>"%LOG%" echo ===== CARDCHA AUTO BUILD + INSTALL LOG =====
>>"%LOG%" echo ExpectedBuild: %EXPECTED_BUILD%
>>"%LOG%" echo Date: %date% %time%
>>"%LOG%" echo Root: %ROOT%
>>"%LOG%" echo GamePath: %GAME_PATH%
>>"%LOG%" echo.

if not exist "%PROJECT%" goto :NO_PROJECT
if not exist "%GAME_PATH%\Stardew Valley.dll" goto :NO_GAME
if not exist "%GAME_PATH%\StardewModdingAPI.dll" goto :NO_GAME
if not exist "%INSTALLER%" goto :NO_INSTALLER

where dotnet >nul 2>&1
if errorlevel 1 goto :NO_SDK

for /f "delims=" %%V in ('dotnet --version 2^>nul') do set "DOTNET_VERSION=%%V"
echo [OK] .NET SDK: %DOTNET_VERSION%
>>"%LOG%" echo .NET SDK: %DOTNET_VERSION%

if exist "%RELEASES%" rmdir /s /q "%RELEASES%"
if exist "%READY%" rmdir /s /q "%READY%"
mkdir "%RELEASES%" >nul 2>&1
mkdir "%READY%" >nul 2>&1

echo.
echo [1/3] Restore...
>>"%LOG%" echo.
>>"%LOG%" echo ===== DOTNET RESTORE =====
dotnet restore "%PROJECT%" >>"%LOG%" 2>&1
if errorlevel 1 goto :BUILD_FAIL

echo [2/3] Build...
>>"%LOG%" echo.
>>"%LOG%" echo ===== DOTNET BUILD =====
dotnet build "%PROJECT%" -c Release --no-restore -p:EnableModDeploy=false -p:EnableModZip=true >>"%LOG%" 2>&1
if errorlevel 1 goto :BUILD_FAIL

set "BUILT_ZIP="
for %%Z in ("%RELEASES%\*.zip") do (
    if exist "%%~fZ" (
        set "BUILT_ZIP=%%~fZ"
        copy /y "%%~fZ" "%READY%\%%~nxZ" >nul
    )
)

if not defined BUILT_ZIP goto :NO_ZIP

echo [3/3] Auto-install vao Mods...
>>"%LOG%" echo.
>>"%LOG%" echo ===== AUTO INSTALL =====
:TRY_INSTALL
powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%" -ZipPath "%BUILT_ZIP%" -GamePath "%GAME_PATH%" >>"%LOG%" 2>&1
if errorlevel 52 goto :INSTALL_FAIL
if errorlevel 51 goto :INSTALL_PENDING
if errorlevel 1 goto :INSTALL_FAIL
goto :INSTALL_SUCCESS

:INSTALL_PENDING
echo.
echo ============================================================
echo  BUILD THANH CONG - CAI DAT DANG CHO
echo ============================================================
echo.
echo Stardew Valley / SMAPI dang su dung Cardcha.dll.
echo Day KHONG PHAI loi build. Windows khong the thay DLL dang duoc game nap.
echo.
echo Ban build moi da duoc giu san tai:
echo %READY%
echo.
echo Hay tat Stardew Valley + SMAPI HOAN TOAN.
echo Sau do:
echo   [R] Thu cai lai NGAY, khong build lai
echo   [X] Thoat va cai sau bang INSTALL_CARDCHA_ONLY.bat
echo.
choice /C RX /N /M "Lua chon [R/X]: "
if errorlevel 2 goto :INSTALL_DEFERRED
goto :TRY_INSTALL

:INSTALL_DEFERRED
>>"%LOG%" echo ===== BUILD SUCCESS - INSTALL DEFERRED (DLL LOCKED) =====
echo.
echo [OK] Build da thanh cong. Khong can build lai.
echo Chi can tat game roi chay INSTALL_CARDCHA_ONLY.bat.
echo.
pause
exit /b 0

:INSTALL_SUCCESS

echo.
echo ============================================================
echo                    XONG!
echo ============================================================
echo.
echo Da build VA cai truc tiep vao:
echo %GAME_PATH%\Mods\Cardcha
echo.
echo Khi mo SMAPI, phai thay:
echo [Cardcha!] Cardcha! v0.1.17-alpha.11.32 NATIVE WORLD ACTORS ACTIVE...
echo.
echo Va lenh nay phai ton tai:
echo cardcha_version
echo cardcha_drop_status
echo.
echo Backup Cardcha cu nam trong:
echo %ROOT%_BACKUP_OLD_CARDCHA
echo.

>>"%LOG%" echo.
>>"%LOG%" echo ===== SUCCESS =====

pause
exit /b 0

:NO_PROJECT
echo [LOI] Khong tim thay Cardcha.csproj.
>>"%LOG%" echo ERROR: Project missing.
pause
exit /b 10

:NO_GAME
echo [LOI] Khong tim thay Stardew Valley + SMAPI tai:
echo %GAME_PATH%
>>"%LOG%" echo ERROR: Game/SMAPI path invalid.
pause
exit /b 20

:NO_INSTALLER
echo [LOI] Thieu INSTALL_BUILT_CARDCHA.ps1.
>>"%LOG%" echo ERROR: Installer script missing.
pause
exit /b 21

:NO_SDK
echo [LOI] Khong tim thay .NET SDK.
>>"%LOG%" echo ERROR: .NET SDK missing.
pause
exit /b 30

:NO_ZIP
echo [LOI] Build thanh cong nhung khong tim thay ZIP.
>>"%LOG%" echo ERROR: ZIP missing after build.
pause
exit /b 31

:BUILD_FAIL
echo.
echo [LOI] BUILD FAILED. Gui build-log.txt.
>>"%LOG%" echo ===== BUILD FAILED =====
start "" notepad "%LOG%"
pause
exit /b 40

:INSTALL_FAIL
echo.
echo [LOI] Build xong nhung AUTO INSTALL that bai vi mot loi khac DLL lock.
echo Build ZIP van duoc giu trong _READY_TO_INSTALL.
echo Gui build-log.txt de kiem tra.
>>"%LOG%" echo ===== INSTALL FAILED =====
start "" notepad "%LOG%"
pause
exit /b 50
