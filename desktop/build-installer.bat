@echo off
REM Builds setup.exe -- right-click this file and choose "Run as administrator".
REM
REM It calls build-installer.ps1 with -ExecutionPolicy Bypass for that run only,
REM because the default user policy (RemoteSigned) blocks unsigned .ps1 files
REM SILENTLY -- the console just returns to the prompt with no message at all.
REM This changes no security setting on the machine; the bypass ends with the command.

cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-installer.ps1"

echo.
pause