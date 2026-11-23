@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Prafulla Goal\Career Reels\tools\windows\Fetch-Broll.ps1" %1
echo.
pause
