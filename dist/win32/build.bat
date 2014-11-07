@echo off
python -m virtualenv --help>nul
if %errorlevel%==1 goto :novenv
setlocal
set oldcurdir=%cd%
cd /d %~dp0
if exist requirements\nul goto :compile
python -m virtualenv requirements
requirements\Scripts\pip install -r ..\..\HERMES2\requirements.txt
echo Merging requirements into python directory
xcopy python requirements /e /s /d /y /q
:compile
..\tools\InnoSetup\iscc /O"build" herm-win32-setup.iss
cd /d %oldcurdir%
endlocal
goto :EOF
:novenv
echo Error: virtualenv not installed