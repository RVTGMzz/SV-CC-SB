@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "REPO=https://github.com/ronvotri/Cardcha-Shardbound.git"
set "BRANCH=main"
set "MSG=Sync full Cardcha source v0.1.17-alpha.11.36"

echo ============================================================
echo   CARDCHA: SHARDBOUND - FULL SOURCE SYNC TO GITHUB
echo ============================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Git is not installed or not in PATH.
  echo Install Git for Windows, then run this file again.
  pause
  exit /b 1
)

if not exist ".git" (
  echo [1/5] Initializing local Git repository...
  git init >nul || goto :FAIL
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin "%REPO%" || goto :FAIL
) else (
  git remote set-url origin "%REPO%" || goto :FAIL
)

echo [2/5] Fetching current private repository state...
git fetch origin "%BRANCH%" || goto :FAIL

echo [3/5] Keeping this builder folder as the working tree...
rem Mixed reset imports the current remote history/index WITHOUT replacing
rem the files in this folder, so the complete source/assets remain intact.
git checkout -B "%BRANCH%" >nul 2>&1 || goto :FAIL
git reset --mixed "origin/%BRANCH%" >nul || goto :FAIL

echo [4/5] Staging complete Cardcha source and runtime assets...
git add -A || goto :FAIL

git diff --cached --quiet
if not errorlevel 1 (
  echo [OK] GitHub already matches this folder. Nothing to push.
  pause
  exit /b 0
)

git config user.name >nul 2>&1
if errorlevel 1 git config user.name "ronvotri"
git config user.email >nul 2>&1
if errorlevel 1 git config user.email "ronvotri@users.noreply.github.com"

git commit -m "%MSG%" || goto :FAIL

echo [5/5] Pushing to %REPO% ...
git push -u origin "%BRANCH%" || goto :FAIL

echo.
echo ============================================================
echo   FULL SOURCE SYNC COMPLETE
 echo ============================================================
echo Repo: %REPO%
echo Branch: %BRANCH%
echo.
pause
exit /b 0

:FAIL
echo.
echo ============================================================
echo   SOURCE SYNC FAILED
 echo ============================================================
echo Check the Git message above. If GitHub asks you to sign in,
echo complete the browser/Git Credential Manager login and run again.
echo.
pause
exit /b 1
