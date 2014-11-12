@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
..\..\tools\Ahk2exe\Ahk2exe.exe /in "hermes-tray.ahk" /icon "..\..\..\HERMES2\src\ui_www\icons\favicon.ico"
cd /d %oldcurdir%
endlocal