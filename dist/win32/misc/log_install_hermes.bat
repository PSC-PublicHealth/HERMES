@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
echo ------------------------------------------->>"%AppData%\HERMES\install_hermes.log"
echo Installing on %date% @ %time%:>> "%AppData%\HERMES\install_hermes.log"
set PATH=%~dp0\..\..\python;%~dp0\..\..\python\Scripts;%PATH%
python.exe install_hermes.py -n -a "%AppData%\HERMES" >>"%AppData%\HERMES\install_hermes.lo"g 2>&1
cd /d %oldcurdir%
endlocal
