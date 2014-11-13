@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
echo ------------------------------------------->>..\..\install_hermes.log
echo Installing on %date% @ %time%:>>..\..\install_hermes.log
set PATH=%~dp0\..\..\python;%~dp0\..\..\python\Scripts;%PATH%
python\python.exe install_hermes.py -n>>..\..\install_hermes.log 2>&1
cd /d %oldcurdir%
endlocal
