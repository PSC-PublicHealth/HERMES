@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
where /q svnversion
if not errorlevel 1 for /f "usebackq tokens=*" %%v in (`svnversion ..\..\HERMES2\ https://redmine.hindsight.psc.edu/svn/hermes/trunk/HERMES2`) do set SvnRevision="/dSvnRevision=%%v"
if not exist misc\hermes-tray.exe goto :buildtray
..\tools\md5sum misc\hermes-tray.ahk > misc\hermes-tray.ahk.curr.md5
if not exist misc\hermes-tray.ahk.last.md5 goto :buildtray
fc misc\hermes-tray.ahk.curr.md5 misc\hermes-tray.ahk.last.md5 > nul
if errorlevel 1 (
	goto :buildtray
) else (
	del misc\hermes-tray.ahk.curr.md5
	echo No changes detected to hermes-tray.ahk. Using existing hermes-tray.exe.
	goto :nextreq
)
:buildtray
del misc\hermes-tray.ahk.last.md5
move misc\hermes-tray.ahk.curr.md5 misc\hermes-tray.ahk.last.md5
del misc\hermes-tray.exe
echo Building hermes-tray.exe
start /b %comspec% /c misc\build-hermes-tray > nul
:nextreq
if exist requirements\nul (
    echo Requirements already downloaded, not updating
    goto :try_compile
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
:try_compile
::wait for hermes-tray.exe because build-hermes-tray.bat was started asynchronously
for /l %%i in (1,1,30) do (
	if not exist misc\hermes-tray.exe (
		ping -n 2 127.0.0.1 > nul
	) else (
		goto :compile_setup
	)
)
echo Error! Could not build hermes-tray.exe. Aborting...
goto :end
:compile_setup
..\tools\InnoSetup\iscc /qp %SvnRevision% herm-win32-setup.iss
:end
cd /d %oldcurdir%
endlocal