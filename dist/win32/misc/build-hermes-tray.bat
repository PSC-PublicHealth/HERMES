@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
..\..\tools\Ahk2exe\Ahk2exe.exe /in "hermes-tray.ahk" /icon "win.ico"
cd /d %oldcurdir%
endlocal