@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
echo Building hermes-tray
call misc\build-hermes-tray
if exist requirements\nul (
    echo Requirements already downloaded, not updating
    goto :compile
)
echo Copying \python to \requirements
xcopy python requirements\ /e /s /q
requirements\python.exe ..\tools\get-pip.py
requirements\python.exe -m pip install -r ..\..\HERMES2\requirements.txt
echo Adding .bat to \requirements\scripts
setlocal EnableDelayedExpansion 
cd /d %~dp0\requirements\Scripts
for %%f in (*-script.py) do (
    set filename=%%~nf
    del !filename:~0,-7!.exe
    copy /y ..\..\misc\-script.bat !filename:~0,-7!.bat
)
setlocal DisableDelayedExpansion
cd /d %~dp0
:compile
..\tools\InnoSetup\iscc /qp /O"build" herm-win32-setup.iss
cd /d %oldcurdir%
endlocal
goto :EOF