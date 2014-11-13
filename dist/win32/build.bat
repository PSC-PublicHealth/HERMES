@echo off
python -m virtualenv --help>nul
if %errorlevel%==1 goto :novenv
setlocal
set oldcurdir=%cd%
cd /d %~dp0
echo Building hermes-tray
call misc\build-hermes-tray
if exist requirements\nul (
    echo Requirements already downloaded, not updating
    goto :compile
)
python -m virtualenv requirements
requirements\Scripts\pip install -r ..\..\HERMES2\requirements.txt
echo Adding 32-bit .exe to \requirements\scripts
setlocal EnableDelayedExpansion 
cd /d %~dp0\requirements\Scripts
for %%f in (*-script.py) do (
    set filename=%%~nf
    copy /y ..\Lib\site-packages\setuptools\cli-32.exe !filename:~0,-7!.exe
)
setlocal DisableDelayedExpansion
cd /d %~dp0
echo Merging \python into \requirements
xcopy python requirements /e /s /y /q
echo Installing 32-bit pip to \requirements
requirements\python -m pip install --upgrade --force-reinstall pip
:compile
..\tools\InnoSetup\iscc /qp /O"build" herm-win32-setup.iss
cd /d %oldcurdir%
endlocal
goto :EOF
:novenv
echo Error: virtualenv not installed