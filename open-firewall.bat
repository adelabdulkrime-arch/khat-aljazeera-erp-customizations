@echo off
REM Opens TCP port 80 so other devices on the workshop LAN can reach the system.
REM Right-click this file and choose "Run as administrator".
REM
REM Scoped to Private/Domain profiles only: the system stays reachable on the
REM workshop network but is NOT exposed when this machine joins a public Wi-Fi.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "if (Get-NetFirewallRule -DisplayName 'Khat ERP' -ErrorAction SilentlyContinue) { Write-Host '  Rule already exists.' -ForegroundColor Green } else { New-NetFirewallRule -DisplayName 'Khat ERP' -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow -Profile Private,Domain | Out-Null; Write-Host '  Firewall rule created (TCP 80, private networks).' -ForegroundColor Green }"

echo.
pause