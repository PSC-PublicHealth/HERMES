@echo on
setlocal
set oldcurdir=%cd%
cd /d %~dp0
set instDir=%1
set logfile="%instDir%\install_hermes.log"
echo ------------------------------------------->>%logfile%
echo Installing on %date% @ %time%:>> %logfile%
set PATH=%~dp0\..\..\python;%~dp0\..\..\python\Scripts;%PATH%
python.exe install_hermes.py -n -a %instDir% >> %logfile% 2>&1
cd /d %oldcurdir%
endlocal
