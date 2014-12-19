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
if exist req32\nul if exist req64\nul if exist reqall\nul  (
    echo Requirements already downloaded, not updating
    goto :try_compile
)
call :gettempfolder requirements32
set req32folder=%tempfolder%
call :gettempfolder requirements64
set req64folder=%tempfolder%
echo Copying \python32 and \python64 to \%req32folder% and \%req64folder%
xcopy python32 %req32folder%\ /e /s /q
xcopy python64 %req64folder%\ /e /s /q
%req32folder%\python.exe ..\tools\get-pip.py
%req32folder%\python.exe -m pip install -r ..\..\HERMES2\requirements.txt
%req64folder%\python.exe ..\tools\get-pip.py
%req64folder%\python.exe -m pip install -r ..\..\HERMES2\requirements.txt
echo Adding .bat to \requirements*\Scripts
setlocal EnableDelayedExpansion 
cd /d %~dp0\%req32folder%\Scripts
for %%f in (*-script.py) do (
    set filename=%%~nf
    del !filename:~0,-7!.exe
    copy /y ..\..\misc\-script.bat !filename:~0,-7!.bat
)
cd /d %~dp0\%req64folder%\Scripts
for %%f in (*-script.py) do (
    set filename=%%~nf
    del !filename:~0,-7!.exe
    copy /y ..\..\misc\-script.bat !filename:~0,-7!.bat
)
setlocal DisableDelayedExpansion
cd /d %~dp0

echo Splitting requirements folders into \req32 \req64 \reqall (prepare to wait)
if exist req32\nul rd /s /q req32
if exist req64\nul rd /s /q req64
if exist reqall\nul rd /s /q reqall
md req32
md req64
md reqall
call :assigndriveletter %req32folder%
set fullreq32=%assigneddriveletter%
call :assigndriveletter %req64folder%
set fullreq64=%assigneddriveletter%
call :assigndriveletter req32
set partreq32=%assigneddriveletter%
call :assigndriveletter req64
set partreq64=%assigneddriveletter%
call :assigndriveletter reqall
set partreqall=%assigneddriveletter%
if "%notenoughdrives%"=="true" (
    call :cleartempfiles
    echo Installer creation failed
    goto :end
)

for /r %fullreq32%:\ %%i in (*) do (
	if not "%%~xi"==".pyc" (
		if not exist %fullreq64%:\%%~pnxi (
			call :copyfile "%%i" "%partreq32%:%%~pnxi"
		) else (
			fc /b "%%i" "%fullreq64%:\%%~pnxi" > nul
			if errorlevel 1 (
				call :copyfile "%%i" "%partreq32%:%%~pnxi"
			) else (
				call :copyfile "%%i" "%partreqall%:%%~pnxi"
			)
		)
	)
)
for /r %fullreq64%:\ %%i in (*) do (
	if not "%%~xi"==".pyc" (
		if not exist %fullreq32%:%%~pnxi (
			call :copyfile "%%i" "%partreq64%:%%~pnxi"
		) else (
			fc /b "%%i" "%fullreq32%:%%~pnxi" > nul
			@if errorlevel 1 (
				call :copyfile "%%i" "%partreq64%:%%~pnxi"
			)
		)
	)
)
call :cleartempfiles
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

goto :EOF
::helper function to create target directories if they don't exist when copying
:copyfile
copy %1 %2 > nul 2>&1
if errorlevel 1 echo f | xcopy %1 %2 /q > nul
goto :EOF

::helper function to alias a free drive letter to a directory
:assigndriveletter
for %%i in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    subst %%i: %1 > nul 2>&1
    if not errorlevel 1 (
        set assigneddriveletter=%%i
        exit /b
    )
)
echo Error: Not enough free drives to associate %1
set notenoughdrives=true

goto :EOF
::helper function to append a random value and time offset and ensure a random folder in the current directory
:gettempfolder
set tempfolder=%1-%random%-%time:~6,5%
if exist "%tempfolder%" GOTO :gettempfolder

goto :EOF
:cleartempfiles
subst /d %fullreq32%: > nul 2>&1
subst /d %fullreq64%: > nul 2>&1
subst /d %partreq32%: > nul 2>&1
subst /d %partreq64%: > nul 2>&1
subst /d %partreqall%: > nul 2>&1
rd /s /q %req32folder%
rd /s /q %req64folder%