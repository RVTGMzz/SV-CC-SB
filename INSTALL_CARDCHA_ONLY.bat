@echo off
chcp 65001 >nul
setlocal EnableExtensions DisableDelayedExpansion

title Cardcha! v0.1.17-alpha.11.36 Install Built Package
cd /d "%~dp0"

set "ROOT=%~dp0"
set "READY=%ROOT%_READY_TO_INSTALL"
set "RELEASES=%ROOT%_releases"
set "GAME_PATH=E:\SteamLibrary\steamapps\common\Stardew Valley"
set "INSTALLER=%ROOT%INSTALL_BUILT_CARDCHA.ps1"
set "LOG=%ROOT%install-only-log.txt"
set "BUILT_ZIP="

cls
echo ============================================================
echo   CARDCHA! - INSTALL BUILT PACKAGE ONLY (NO REBUILD)
echo ============================================================
echo.

if not exist "%INSTALLER%" goto :NO_INSTALLER
if not exist "%GAME_PATH%\Mods" goto :NO_GAME

for %%Z in ("%READY%\*.zip") do if exist "%%~fZ" set "BUILT_ZIP=%%~fZ"
if not defined BUILT_ZIP for %%Z in ("%RELEASES%\*.zip") do if exist "%%~fZ" set "BUILT_ZIP=%%~fZ"
if not defined BUILT_ZIP goto :NO_ZIP

>"%LOG%" echo ===== CARDCHA INSTALL-ONLY LOG =====
>>"%LOG%" echo Date: %date% %time%
>>"%LOG%" echo Zip: %BUILT_ZIP%
>>"%LOG%" echo GamePath: %GAME_PATH%
>>"%LOG%" echo.

echo Package:
echo %BUILT_ZIP%
echo.

:TRY_INSTALL
powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%" -ZipPath "%BUILT_ZIP%" -GamePath "%GAME_PATH%" >>"%LOG%" 2>&1
if errorlevel 52 goto :INSTALL_FAIL
if errorlevel 51 goto :LOCKED
if errorlevel 1 goto :INSTALL_FAIL

echo.
echo ============================================================
echo  CAI DAT XONG - KHONG CAN BUILD LAI
echo ============================================================
echo Installed to:
echo %GAME_PATH%\Mods\Cardcha
echo.
pause
exit /b 0

:LOCKED
echo.
echo Stardew Valley / SMAPI van dang chay va khoa Cardcha.dll.
echo Tat game + SMAPI HOAN TOAN, sau do bam R de thu lai.
echo Khong co build nao duoc chay lai.
echo.
choice /C RX /N /M "[R] Retry / [X] Exit: "
if errorlevel 2 exit /b 51
goto :TRY_INSTALL

:NO_INSTALLER
echo [LOI] Thieu INSTALL_BUILT_CARDCHA.ps1.
pause
exit /b 21

:NO_GAME
echo [LOI] Khong tim thay Mods folder tai:
echo %GAME_PATH%\Mods
pause
exit /b 20

:NO_ZIP
echo [LOI] Chua co ZIP da build trong _READY_TO_INSTALL hoac _releases.
echo Hay chay BUILD_CARDCHA.bat it nhat mot lan.
pause
exit /b 31

:INSTALL_FAIL
echo.
echo [LOI] Cai dat that bai vi mot loi khac DLL lock.
echo Gui install-only-log.txt de kiem tra.
start "" notepad "%LOG%"
pause
exit /b 50
