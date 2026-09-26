@echo off
setlocal
title RivalBull Stop
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Stop-Local.ps1" %*
set "STOP_EXIT=%ERRORLEVEL%"
if not "%STOP_EXIT%"=="0" (
    echo.
    echo Stop failed. See the message above.
    if /I not "%~1"=="-NoPause" pause
)
exit /b %STOP_EXIT%
