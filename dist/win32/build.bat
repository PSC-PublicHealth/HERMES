@echo off
python -m virtualenv --help>nul
if %errorlevel%==1 goto :novenv
setlocal
set oldcurdir=%cd%
cd /d %~dp0
echo Building hermes-tray
call misc\build-hermes-tray
if exist requirements\nul goto :compile
python -m virtualenv requirements
requirements\Scripts\pip install -r ..\..\HERMES2\requirements.txt
echo Merging python into requirements directory
xcopy python requirements /e /s /y /q
:compile
..\tools\InnoSetup\iscc /qp /O"build" herm-win32-setup.iss
cd /d %oldcurdir%
endlocal
goto :EOF
:novenv
echo Error: virtualenv not installed