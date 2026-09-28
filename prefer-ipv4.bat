@echo off
REM Prefer IPv4 over IPv6 for outgoing connections.
REM Right-click this file and choose "Run as administrator".
REM
REM WHY: this machine has no working IPv6 (curl -6 to Docker Hub fails with 000),
REM but Windows still prefers IPv6 by default and DNS returns IPv6 addresses
REM first. Every connection therefore stalls on a dead protocol until it times
REM out -- which is why "docker pull" sat at zero bytes and google.com took 7s.
REM
REM This sets DisabledComponents = 0x20 (prefer IPv4), which does NOT disable
REM IPv6 -- it only changes the preference order, so IPv6 still works if the
REM network ever provides it. Microsoft-documented value.
REM
REM TO REVERT: run this command as administrator, then reboot:
REM   reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" /v DisabledComponents /f

reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" /v DisabledComponents /t REG_DWORD /d 32 /f

if %errorlevel%==0 (
  echo.
  echo   Done. IPv4 is now preferred over IPv6.
  echo   A RESTART is required for this to take effect.
  echo.
) else (
  echo.
  echo   Failed -- make sure you ran this as administrator.
  echo.
)
pause