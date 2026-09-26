@echo off
setlocal
title RivalBull Launcher
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-Local.ps1" %*
set "LAUNCH_EXIT=%ERRORLEVEL%"
if not "%LAUNCH_EXIT%"=="0" (
    echo.
    echo Startup failed. See the message above.
    if /I not "%~1"=="-NoBrowser" pause
)
exit /b %LAUNCH_EXIT%
